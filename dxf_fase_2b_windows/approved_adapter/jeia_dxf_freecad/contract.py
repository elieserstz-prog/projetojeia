"""Standard-library-only contract construction. No CAD or JEIA imports."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import uuid

VERSION='0.1.0'


def state(value='extracted',reason=None,diagnostics=()):
    return dict(state=value,evidenceIds=[],diagnosticIds=list(diagnostics),reason=reason)


def number(value):
    v=float(value)
    if not math.isfinite(v):raise ValueError('Nonfinite native geometry value')
    return v


def vec(value):
    return [number(value.x),number(value.y),number(value.z)]


def quantity(value=None,unit='mm',reason=None):
    return dict(value=None if value is None else number(value),unit=unit,
                validation=state('unknown' if value is None else 'extracted',reason))


def metadata(data,name):
    """Read ASCII header facts only; never infer physical units from FreeCAD."""
    version='unknown';insunits=0;measurement=None;encoding=None;header={}
    if not data.startswith(b'AutoCAD Binary DXF'):
        text=data.decode('latin1');rows=text.splitlines();key=None;section='';pending=False
        for i in range(0,len(rows)-1,2):
            try:code=int(rows[i].strip())
            except ValueError:continue
            value=rows[i+1].strip()
            if code==0 and value=='SECTION':pending=True;continue
            if pending and code==2:section=value;pending=False;continue
            if code==0 and value=='ENDSEC':section='';key=None;continue
            if section!='HEADER':continue
            if code==9:key=value
            elif key=='$ACADVER' and code==1:version=value;header[key]=value
            elif key in ('$INSUNITS','$MEASUREMENT') and code==70:
                try:header[key]=int(value)
                except ValueError:continue
                if key=='$INSUNITS':insunits=header[key]
                else:measurement=header[key]
        if not 0<=insunits<=32767:insunits=0
        encoding='utf-8' if version>='AC1021' and version!='unknown' else None
    factors={1:25.4,2:304.8,3:1609344.,4:1.,5:10.,6:1000.,7:1e6,
             8:0.0000254,9:0.0254,10:914.4,11:1e-7,12:1e-6,13:0.001,
             14:100.,15:1e4,16:1e5,17:1e12,21:1200000/3937,
             22:100000/3937,23:3600000/3937,24:6336000000/3937}
    factor=factors.get(insunits)
    return dict(id='document-'+sha256(data).hexdigest()[:32],fileName=Path(name).name,
        sha256=sha256(data).hexdigest(),byteLength=len(data),dxfVersion=version,encoding=encoding,
        units=dict(rawInsunits=insunits,rawMeasurement=measurement,resolvedUnit='INSUNITS:'+str(insunits) if factor else None,
            mmPerDrawingUnit=factor,resolutionMethod='header' if factor else 'unknown',
            validation=state('extracted' if factor else 'unknown','Header fact; native importer scale remains unverified')),
        rawHeader=header,validation=state())


class Packet:
    def __init__(self,meta,request_id=None,generation=0,revision=1,synthetic=False):
        if request_id is not None and (not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9._:/@+\-]{0,255}',request_id)):
            raise ValueError('Invalid request ID')
        if type(generation) is not int or generation<0:raise ValueError('Invalid selection generation')
        if type(revision) is not int or revision<1:raise ValueError('Invalid analysis revision')
        schema=json.loads(Path(__file__).with_name('schema.json').read_text(encoding='utf-8'))
        self.data={k:[] for k,v in schema['properties'].items() if v.get('type')=='array'}
        self.hash=meta['sha256']
        self.data.update(contract='JEIA_DXF_TECH',version='1.0',document=meta,context=dict(
            requestId=request_id or 'req-'+uuid.uuid4().hex,selectionGeneration=generation,analysisRevision=revision,
            purpose='synthetic_example' if synthetic else 'production_analysis',producer='experimental-freecad-adapter-'+VERSION,
            createdAt=datetime.now(timezone.utc).isoformat()),validation=dict(stage='extracted',schemaStatus='not_checked',
                semanticStatus='not_checked',eligibility=[],cncReleased=False))
        self.source_original=self.uid('source','dxf_original');self.source_native=self.uid('source','freecad')
        self.data['sources'].append(dict(id=self.source_original,kind='dxf_original',version=meta['dxfVersion'],
            inputSha256=self.hash,options={'headerOnly':True},capabilities=['input_identity'],validation=state()))
        self.native_source=dict(id=self.source_native,kind='freecad',version='unavailable',inputSha256=self.hash,
            options={},capabilities=[],validation=state('unknown','Native worker has not completed'))
        self.data['sources'].append(self.native_source)
        self.frame=self.uid('frame','freecad_native_mm')
        self.data['frames'].append(dict(id=self.frame,kind='document_wcs',unit='mm',spaceId=None,
            description='FreeCAD kernel coordinates in internal mm; correspondence to DXF units/layouts not verified'))
        self.diag('EXPERIMENTAL_EXTRACTION_ONLY','No physical interpretation, reconciliation or JEIA integration.')
        self.diag('DXF_SPACE_AND_ORIGIN_MAPPING_UNAVAILABLE','Native shapes alone do not establish DXF handles, blocks, Model/Paper or view identity.')
        self.diag('NATIVE_IMPORT_SCALE_UNVERIFIED','FreeCAD kernel mm do not prove DXF unit conversion; do not apply another header factor.')
        if meta['units']['mmPerDrawingUnit'] is None:self.diag('DXF_UNITS_UNRESOLVED','Input DXF unit absent or unsupported; no factor 1 fallback.')
        if synthetic:self.diag('SYNTHETIC_DATA','Synthetic kernel fixture, not a DXF integration approval.')

    def uid(self,kind,*keys):
        return kind+'-'+sha256(json.dumps([self.hash,kind,*keys],separators=(',',':'),ensure_ascii=True).encode()).hexdigest()[:32]

    def diag(self,code,message,severity='blocker',geometry=None,details=None):
        id=self.uid('diagnostic',code,len(self.data['diagnostics']))
        self.data['diagnostics'].append(dict(id=id,code=code,severity=severity,
            targets=[dict(kind='geometry',id=geometry)] if geometry else [dict(kind='document',id=self.data['document']['id'])],
            message=message,details=details,blocksConsumers=[] if severity=='info' else ['material','process','cost'],
            status='open',evidenceIds=[]))
        return id

    def geometry(self,key,payload,approximation='analytic'):
        id=self.uid('geometry',key)
        self.data['geometries'].append(dict(id=id,sourceId=self.source_native,entityId=None,occurrenceId=None,
            sourceObjectKey=key,frameId=self.frame,payload=payload,approximation=approximation,
            derivedFromGeometryIds=[],appliedTransformIds=[],
            validation=state('unsupported',payload.get('reason')) if approximation=='unsupported' else state()))
        return id

    def evidence(self,key,geometry,value,description):
        id=self.uid('evidence',key)
        self.data['evidence'].append(dict(id=id,sourceId=self.source_native,targets=[dict(kind='geometry',id=geometry)],
            family='topology',independenceKey=key,method='FreeCAD_Part_native_observation',description=description,
            value=value,reliability='observed'))
        return id

    def finish(self):
        self.data['validation']['eligibility']=[dict(scope=dict(kind='document',id=self.data['document']['id']),
            consumer=c,status='not_assessed' if c=='visualization' else 'blocked',
            blockingDiagnosticIds=[] if c=='visualization' else [d['id'] for d in self.data['diagnostics'] if c in d['blocksConsumers']],
            requiredDecisionIds=[],reason='Experimental native observations; source semantics and physical recognition unapproved.')
            for c in ('visualization','material','process','cost')]
        json.dumps(self.data,allow_nan=False)
        return self.data
