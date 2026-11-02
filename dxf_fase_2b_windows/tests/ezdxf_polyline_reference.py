"""Developer reference using an ALREADY installed ezdxf; never installs it."""
import argparse
from hashlib import sha256
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostic.core import write_json
from diagnostic.polyline_probe import variants, legacy_polylines


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import ezdxf
    path = ROOT / 'examples/01_geometrias_mm.dxf'
    raw = path.read_bytes(); poly, cases = variants(raw)
    original = ezdxf.readfile(path)
    entity = next(iter(original.modelspace().query('POLYLINE')))
    lines = list(entity.virtual_entities())
    assert entity.is_closed and len(lines) == 3
    results = []
    for name, content, count in cases:
        doc = ezdxf.read(io.StringIO(content.decode('ascii')))
        ent = next(iter(doc.modelspace()))
        edges = list(ent.virtual_entities())
        nondegenerate = [edge for edge in edges if (edge.dxf.end-edge.dxf.start).magnitude > 1e-8]
        assert len(nondegenerate) == count
        results.append({'variant': name, 'dxftype': ent.dxftype(), 'closed': bool(ent.is_closed if ent.dxftype() == 'POLYLINE' else ent.closed),
                        'rawVirtualEdgeCount': len(edges), 'nondegenerateEdgeCount': len(nondegenerate),
                        'degenerateEdgesRetained': len(edges)-len(nondegenerate),
                        'edges': [{'type': e.dxftype(), 'start': list(e.dxf.start), 'end': list(e.dxf.end)} for e in edges]})
    assert path.read_bytes() == raw
    write_json(args.output, {'kind': 'ezdxf_existing_library_reference', 'ezdxfVersion': ezdxf.__version__,
                            'inputSha256': sha256(raw).hexdigest(), 'originalRawPolyline': poly,
                            'originalEzdxfEdges': [{'start': list(e.dxf.start), 'end': list(e.dxf.end)} for e in lines],
                            'variants': results, 'sourceUnchanged': True, 'integrationApproved': False})
    print('PASS: original DXF closed with 3 edges; all 5 differential references match ezdxf')


if __name__ == '__main__':
    main()
