"""Run only inside a compatible, already available FreeCAD Python runtime."""
from hashlib import sha256
from pathlib import Path
import sys
import uuid

from .collector import collect_document
from .contract import metadata


def extract_native(path,*,request_id=None,generation=0,revision=1,**limits):
    import FreeCAD as App
    import Import
    # A plain compatible Python can load the native libraries without the
    # workbench paths normally initialized by FreeCADCmd. Activate only the
    # already installed Draft module from FreeCAD's own resource directory.
    draft_path=Path(App.getResourceDir())/'Mod'/'Draft'
    if draft_path.is_dir() and str(draft_path) not in sys.path:sys.path.append(str(draft_path))
    path=Path(path)
    before=path.read_bytes()
    old=App.ActiveDocument
    old_name=old.Name if old is not None else None
    doc=None
    try:
        doc=App.newDocument('JEIA_DXF2B_'+uuid.uuid4().hex)
        # Explicit C++ importer; no hidden fallback to Draft/legacy/downloader.
        Import.readDXF(str(path),doc.Name,False)
        doc.recompute()
        if sha256(path.read_bytes()).digest()!=sha256(before).digest():
            raise ValueError('DXF bytes changed while native importer was running')
        result=collect_document(doc,metadata(before,path.name),App,request_id=request_id,
            generation=generation,revision=revision,**limits)
        result['sources'][1]['options']['importer']='Import.readDXF(ignore_errors=False)'
        return result
    finally:
        if doc is not None:App.closeDocument(doc.Name)
        if old_name is not None and App.getDocument(old_name) is not None:App.setActiveDocument(old_name)
