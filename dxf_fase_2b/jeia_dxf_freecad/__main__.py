import argparse
import json
from pathlib import Path
import sys
from .runner import Options, extract, succeeded


def main(argv=None):
    parser=argparse.ArgumentParser(description='Experimental — somente para testes. FreeCAD independente, sem integracao JEIA.')
    parser.add_argument('input',type=Path);parser.add_argument('--output',type=Path)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--freecad-cmd',help='Path to an already installed FreeCADCmd')
    group.add_argument('--api-python',help='Explicit compatible Python already able to load FreeCAD; no automatic fallback')
    parser.add_argument('--freecad-lib',help='Existing FreeCAD library folder for explicit API Python mode')
    parser.add_argument('--timeout',type=float,default=120)
    args=parser.parse_args(argv)
    try:
        if args.output and args.output.resolve()==args.input.resolve():raise ValueError('Output cannot be input DXF')
        result=extract(args.input,Options(freecad_cmd=args.freecad_cmd,api_python=args.api_python,
            freecad_lib=args.freecad_lib,timeout=args.timeout))
        text=json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8') as out:out.write(text)
        else:sys.stdout.write(text)
        return 0 if succeeded(result) else 2
    except (ValueError,OSError) as exc:
        print('EXTRACTION FAILED: '+str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
