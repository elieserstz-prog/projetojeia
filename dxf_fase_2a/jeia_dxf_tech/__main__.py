"""Run: python -m jeia_dxf_tech drawing.dxf --output report.json"""
import argparse
import json
from pathlib import Path
import sys

from .adapter import AdapterError, Options, extract


def main(argv=None):
    parser = argparse.ArgumentParser(description='Experimental — somente para testes. Extracao DXF independente; sem integracao JEIA.')
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path,help='New JSON file; existing files are never overwritten')
    parser.add_argument('--request-id')
    parser.add_argument('--selection-generation',type=int,default=0)
    args=parser.parse_args(argv)
    try:
        if args.output and args.output.resolve()==args.input.resolve():
            raise AdapterError('Output cannot be the input DXF')
        package=extract(args.input,Options(request_id=args.request_id,selection_generation=args.selection_generation))
        text=json.dumps(package,ensure_ascii=False,allow_nan=False,indent=2)+'\n'
        if args.output:
            with args.output.open('x',encoding='utf-8') as dest:
                dest.write(text)
        else:
            sys.stdout.write(text)
    except (AdapterError,OSError,ValueError) as exc:
        print('EXTRACTION FAILED: '+str(exc),file=sys.stderr)
        return 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
