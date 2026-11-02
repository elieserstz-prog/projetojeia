"""Generate synthetic test DXFs only; never reads an installed CAD application."""
from pathlib import Path
import ezdxf


def generate(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    paths=[]
    def save(name,d):
        p=folder/name
        if p.exists():
            raise FileExistsError(p)
        d.saveas(p);paths.append(p)
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    m.add_line((0,0),(10,0));m.add_arc((20,0),5,350,10);m.add_circle((40,0),3)
    m.add_lwpolyline([(0,20,1),(10,20,-1),(20,20,0)],format='xyb')
    m.add_polyline2d([(0,40),(10,40),(10,50)],close=True)
    save('01_geometrias_mm.dxf',d)
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    m.add_lwpolyline([(0,0),(100,0),(100,60),(0,60)],close=True);m.add_circle((25,30),5)
    m.add_linear_dim(base=(0,-10),p1=(0,0),p2=(100,0),override={'dimtol':1,'dimtp':0.1,'dimtm':0.1}).render()
    b=d.blocks.new('CARIMBO');b.add_lwpolyline([(0,0),(100,0),(100,30),(0,30)],close=True)
    b.add_text('DESENHO EX-002');b.add_attdef('REV',(5,5),text='00')
    p=d.layouts.new('FOLHA');p.dxf.plot_paper_units=1
    p.add_lwpolyline([(-10,-10),(410,-10),(410,287),(-10,287)],close=True)
    p.add_blockref('CARIMBO',(250,10)).add_auto_attribs({'REV':'01'})
    p.add_viewport(center=(100,100),size=(100,80),view_center_point=(0,0),view_height=200)
    p.add_linear_dim(base=(0,-5),p1=(0,0),p2=(50,0)).render()
    save('02_peca_folha_carimbo_cotas.dxf',d)
    d=ezdxf.new('R2010');d.units=1;b=d.blocks.new('CIRCULO',base_point=(1,0))
    b.add_circle((0,0),1,dxfattribs={'layer':'0'})
    d.layers.new('PECA')
    e=d.modelspace().add_blockref('CIRCULO',(10,20),dxfattribs={'xscale':2,'yscale':1,'rotation':90,'layer':'PECA'})
    e.grid(size=(1,2),spacing=(0,5))
    d.modelspace().add_circle((2,3,4),1,dxfattribs={'extrusion':(0,1,0)})
    save('03_blocos_polegadas_ocs.dxf',d)
    d=ezdxf.new('R2000');d.units=0
    d.modelspace().add_line((0,0),(10,0));d.modelspace().add_text('Revisão: peça sintética — não fabricar')
    d.modelspace().add_spline([(0,0),(1,2),(3,4),(5,0)])
    save('04_unidade_ausente.dxf',d)
    return paths


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    for p in generate(parser.parse_args().folder):print(p)
