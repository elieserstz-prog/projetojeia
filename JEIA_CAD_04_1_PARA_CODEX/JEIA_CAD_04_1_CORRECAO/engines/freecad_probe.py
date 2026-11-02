# FreeCAD official Python API. Invoked only through FreeCADCmd, not system Python.
import sys, json, os
try:
 import FreeCAD as App, Part
 path, output = sys.argv[-2:]
 if not os.path.isfile(path): raise ValueError('Arquivo inexistente')
 shape=Part.Shape()
 shape.read(path)
 bb=shape.BoundBox
 result={'motor':'FreeCAD/Part','arquivo':os.path.basename(path),'valido':bool(shape.isValid()),'solidos':len(shape.Solids),'faces':len(shape.Faces),'arestas':len(shape.Edges),'bbox_mm':{'x':bb.XLength,'y':bb.YLength,'z':bb.ZLength},'volume_mm3':shape.Volume,'observacao':'Medidas geométricas preliminares; não equivalem a cotas nominais nem aprovação para usinagem.'}
except Exception as e:
 result={'erro':str(e)}
try:
 with open(output,'w',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
except Exception: pass
