"""Process isolation and input identity; standard library only."""
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .contract import Packet, metadata, state


@dataclass(frozen=True)
class Options:
    freecad_cmd: str | None = None
    api_python: str | None = None
    freecad_lib: str | None = None
    timeout: float = 120
    max_input_bytes: int = 64*1024*1024
    max_response_bytes: int = 64*1024*1024
    max_brep_bytes: int = 16*1024*1024
    max_edges: int = 20000
    max_faces: int = 10000
    request_id: str | None = None
    generation: int = 0
    revision: int = 1

    def __post_init__(self):
        if self.api_python and self.freecad_cmd:raise ValueError('Select FreeCADCmd OR compatible API Python explicitly')
        if isinstance(self.timeout,bool) or not math.isfinite(self.timeout) or self.timeout<=0:raise ValueError('Invalid timeout')
        for name in ('max_input_bytes','max_response_bytes','max_brep_bytes','max_edges','max_faces'):
            if type(getattr(self,name)) is not int or getattr(self,name)<=0:raise ValueError('Invalid '+name)


def extract(path,options=None):
    options=options or Options();path=Path(path)
    if path.suffix.lower()!='.dxf':raise ValueError('Expected .dxf input')
    with path.open('rb') as source:data=source.read(options.max_input_bytes+1)
    if not data:raise ValueError('Empty input')
    if len(data)>options.max_input_bytes:raise ValueError('Input limit exceeded')
    packet=Packet(metadata(data,path.name),options.request_id,options.generation,options.revision)
    if data.startswith(b'AutoCAD Binary DXF'):
        return _failure(packet,'BINARY_DXF_NOT_SUPPORTED','Binary DXF not supported by this adapter')
    if options.freecad_lib and not options.api_python:
        raise ValueError('--freecad-lib is only applicable to explicit --api-python mode')
    cmd=options.api_python or options.freecad_cmd or shutil.which('FreeCADCmd') or shutil.which('freecadcmd')
    if not cmd or not shutil.which(cmd):return _failure(packet,'FREECAD_UNAVAILABLE','Selected FreeCAD executable not found')
    worker=Path(__file__).with_name('worker.py')
    with tempfile.TemporaryDirectory(prefix='jeia-dxf2b-') as td:
        root=Path(td);snapshot=root/path.name;snapshot.write_bytes(data)
        request=root/'request.json';response=root/'response.json';log=root/'native.log'
        request.write_text(json.dumps(dict(input=str(snapshot),requestId=packet.data['context']['requestId'],
            generation=options.generation,revision=options.revision,freecadLib=options.freecad_lib,
            limits={'max_edges':options.max_edges,'max_faces':options.max_faces,'max_brep_bytes':options.max_brep_bytes})),encoding='utf-8')
        env={**os.environ,'JEIA_DXF2B_REQUEST':str(request),'JEIA_DXF2B_RESPONSE':str(response),'PYTHONDONTWRITEBYTECODE':'1'}
        # Keep proxy/authentication and runtime guard environment unchanged.
        try:
            with log.open('wb') as stream:
                run=subprocess.run([str(cmd),str(worker)],stdout=stream,stderr=subprocess.STDOUT,
                    env=env,timeout=options.timeout,check=False)
        except subprocess.TimeoutExpired:
            return _failure(packet,'NATIVE_TIMEOUT','Native worker timed out; no geometry approved',_tail(log))
        except OSError as exc:
            return _failure(packet,'NATIVE_START_FAILED',str(exc),_tail(log))
        if run.returncode!=0:
            return _failure(packet,'NATIVE_PROCESS_FAILED','Worker exit '+str(run.returncode)+'; native crash/exit is not a successful extraction',_tail(log))
        if not response.is_file():return _failure(packet,'NATIVE_RESPONSE_MISSING','Worker wrote no JSON result',_tail(log))
        if response.stat().st_size>options.max_response_bytes:return _failure(packet,'NATIVE_RESPONSE_LIMIT','Native JSON exceeded explicit size limit')
        try:
            result=json.loads(response.read_text(encoding='utf-8'))
            if 'workerError' in result:return _failure(packet,'NATIVE_WORKER_ERROR',str(result['workerError']),
                (_tail(log)+'\n'+str(result.get('workerTrace','')))[-65536:])
            if result['contract']!='JEIA_DXF_TECH' or result['version']!='1.0':raise ValueError('Unsupported response contract')
            if result['document']['sha256']!=sha256(data).hexdigest():raise ValueError('Response hash mismatch')
            context=result['context']
            if (context['requestId'],context['selectionGeneration'],context['analysisRevision'])!=(packet.data['context']['requestId'],options.generation,options.revision):
                raise ValueError('Response selection identity mismatch')
            if any(s['inputSha256']!=packet.hash for s in result['sources']):raise ValueError('Source hash mismatch')
            if sha256(snapshot.read_bytes()).digest()!=sha256(data).digest():raise ValueError('Snapshot bytes changed')
            if result['validation']['cncReleased'] is not False:raise ValueError('Unexpected CNC permission')
            if any(e['status']!='blocked' for e in result['validation']['eligibility'] if e['consumer']!='visualization'):
                raise ValueError('Unexpected operational permission')
            json.dumps(result,allow_nan=False)
            return result
        except (ValueError,KeyError,TypeError,UnicodeError) as exc:
            return _failure(packet,'NATIVE_RESPONSE_INVALID',str(exc),_tail(log))


def _tail(path):
    if not path.is_file():return ''
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-65536));return stream.read().decode('utf-8',errors='replace')


def _failure(packet,code,message,log=None):
    packet.native_source['validation']=state('rejected',message)
    packet.diag(code,message,details={'nativeLogTail':log} if log else None)
    return packet.finish()


def succeeded(result):
    """Native process produced geometry, NOT industrial integration approval."""
    return any(g.get('payload',{}).get('type')!='UNSUPPORTED' for g in result.get('geometries',[])) and not any(d['code'] in {'NO_NATIVE_GEOMETRY','NATIVE_TIMEOUT',
        'NATIVE_PROCESS_FAILED','NATIVE_RESPONSE_INVALID','NATIVE_WORKER_ERROR','NATIVE_RESPONSE_MISSING',
        'NATIVE_START_FAILED','FREECAD_UNAVAILABLE','NATIVE_RESPONSE_LIMIT','BINARY_DXF_NOT_SUPPORTED'} for d in result['diagnostics'])
