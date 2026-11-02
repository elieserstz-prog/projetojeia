"""Keep missing coordinate frames explicit without accepting provisional geometry."""
from .core import compare


def assess_geometry(packet, oracle, midpoints, inventory):
    provisional = compare(packet, oracle, midpoints)
    unresolved = [item['name'] for item in inventory if item.get('coordinateFrameStatus') == 'unresolved']
    has_frame_diagnostic = any(d['code'] == 'GLOBAL_PLACEMENT_UNAVAILABLE' for d in packet.get('diagnostics', []))
    if not unresolved and not has_frame_diagnostic:
        return provisional
    return {'status': 'pending', 'checks': [
        {'id': 'global_coordinates_unresolved', 'status': 'pending', 'objects': unresolved,
         'reason': 'Local shapes retained. Global placement unavailable; full WCS comparison is not assessable.'}],
        'knownFrameComparison': provisional, 'provisionalResultsAccepted': False,
        'meaning': 'No global coordinates inferred; partial comparisons do not approve this case'}
