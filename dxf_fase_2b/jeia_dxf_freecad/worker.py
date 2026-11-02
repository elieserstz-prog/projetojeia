"""Isolated FreeCAD worker, called with only its script path.

Requests/responses use private temporary files selected by the controller.
The module has no package installation or external service access.
"""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    req_path=os.environ.get('JEIA_DXF2B_REQUEST')
    out_path=os.environ.get('JEIA_DXF2B_RESPONSE')
    if not req_path or not out_path:return 2
    request=json.loads(Path(req_path).read_text(encoding='utf-8'))
    try:
        if request.get('freecadLib'):
            sys.path.insert(0,request['freecadLib'])
        from jeia_dxf_freecad.native import extract_native
        result=extract_native(request['input'],request_id=request['requestId'],generation=request['generation'],
            revision=request['revision'],**request['limits'])
        text=json.dumps(result,ensure_ascii=False,allow_nan=False)
    except Exception as exc:
        import traceback
        text=json.dumps({'workerError':type(exc).__name__+': '+str(exc),'workerTrace':traceback.format_exc()})
    with Path(out_path).open('x',encoding='utf-8') as stream:stream.write(text)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
