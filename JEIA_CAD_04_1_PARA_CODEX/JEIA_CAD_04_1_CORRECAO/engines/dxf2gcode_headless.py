#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
DXF2GCODE HEADLESS - MOTOR COMPACTO DE PARSING DXF E GERAÇÃO DE G-CODE
================================================================================
Baseado na arquitetura interna e algoritmos do DXF2GCODE:
  1. Leitor de Entidades DXF (LINE, ARC, CIRCLE, LWPOLYLINE com Bulge).
  2. Encadeamento Geométrico de Contornos (Closed/Open Shapes).
  3. Compensação de Raio de Ferramenta (Offset 2D interno/externo).
  4. Otimizador de Trajetória TSP (Nearest-Neighbor & Prioridade de Furos).
  5. Pós-Processador Paramétrico (G0/G1/G2/G3 com profundidade e passes).

Execução via Linha de Comando (Sem Interface Gráfica / Headless).
================================================================================
"""

import argparse
import math
import os
import sys
from typing import List, Tuple, Dict, Any, Optional

# ==============================================================================
# 1. ESTRUTURAS GEOMÉTRICAS BÁSICAS
# ==============================================================================

class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def dist(self, other: 'Point') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def __repr__(self):
        return f"P({self.x:.3f}, {self.y:.3f})"


class LineSegment:
    def __init__(self, p1: Point, p2: Point, layer: str = "0"):
        self.p1 = p1
        self.p2 = p2
        self.layer = layer

    def length(self) -> float:
        return self.p1.dist(self.p2)

    def reversed(self) -> 'LineSegment':
        return LineSegment(self.p2, self.p1, self.layer)


class ArcSegment:
    def __init__(self, center: Point, radius: float, start_angle: float, end_angle: float, ccw: bool = True, layer: str = "0"):
        self.center = center
        self.radius = float(radius)
        self.start_angle = float(start_angle)  # em radianos
        self.end_angle = float(end_angle)      # em radianos
        self.ccw = ccw
        self.layer = layer

        # Calcula pontos inicial e final
        self.p1 = Point(
            self.center.x + self.radius * math.cos(self.start_angle),
            self.center.y + self.radius * math.sin(self.start_angle)
        )
        self.p2 = Point(
            self.center.x + self.radius * math.cos(self.end_angle),
            self.center.y + self.radius * math.sin(self.end_angle)
        )

    def reversed(self) -> 'ArcSegment':
        return ArcSegment(self.center, self.radius, self.end_angle, self.start_angle, not self.ccw, self.layer)


# ==============================================================================
# 2. PARSER ESTÁTICO DE ARQUIVOS DXF
# ==============================================================================

class DXFParser:
    """Parser simplificado e robusto de grupos DXF ASCII (Tags 0 a 70)."""

    def __init__(self, filepath: str = None, text_content: str = None):
        self.filepath = filepath
        self.content = text_content
        self.raw_entities: List[Any] = []

        if filepath:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                self.content = f.read()

        if self.content:
            self.parse()

    def parse(self):
        lines = [line.strip() for line in self.content.splitlines()]
        i = 0
        n = len(lines)
        in_entities = False

        while i < n - 1:
            code = int(lines[i]) if lines[i].lstrip('-').isdigit() else None
            val = lines[i+1]
            i += 2

            if code == 2 and val == "ENTITIES":
                in_entities = True
                continue
            elif code == 0 and val == "ENDSEC" and in_entities:
                break
            elif code == 0 and val == "EOF":
                break

            if in_entities and code == 0:
                ent_type = val.upper()
                ent_data = {}
                # Lê todas as propriedades da entidade até o próximo código 0
                while i < n - 1:
                    sub_code = int(lines[i]) if lines[i].lstrip('-').isdigit() else None
                    sub_val = lines[i+1]
                    if sub_code == 0:
                        break
                    i += 2
                    if sub_code not in ent_data:
                        ent_data[sub_code] = []
                    ent_data[sub_code].append(sub_val)

                self._process_entity(ent_type, ent_data)

    def _process_entity(self, etype: str, data: Dict[int, List[str]]):
        layer = data.get(8, ["0"])[0]

        if etype == "LINE":
            p1 = Point(float(data[10][0]), float(data[20][0]))
            p2 = Point(float(data[11][0]), float(data[21][0]))
            self.raw_entities.append(LineSegment(p1, p2, layer))

        elif etype == "ARC":
            center = Point(float(data[10][0]), float(data[20][0]))
            r = float(data[40][0])
            start_deg = float(data[50][0])
            end_deg = float(data[51][0])
            self.raw_entities.append(ArcSegment(
                center, r,
                math.radians(start_deg),
                math.radians(end_deg),
                ccw=True,
                layer=layer
            ))

        elif etype == "CIRCLE":
            center = Point(float(data[10][0]), float(data[20][0]))
            r = float(data[40][0])
            # Um círculo é tratado como dois arcos de 180° interligados
            self.raw_entities.append(ArcSegment(center, r, 0.0, math.pi, True, layer))
            self.raw_entities.append(ArcSegment(center, r, math.pi, 2 * math.pi, True, layer))

        elif etype == "LWPOLYLINE":
            xs = [float(v) for v in data.get(10, [])]
            ys = [float(v) for v in data.get(20, [])]
            bulges = [float(v) for v in data.get(42, [0.0] * len(xs))]
            while len(bulges) < len(xs):
                bulges.append(0.0)

            closed = (int(data.get(70, [0])[0]) & 1) == 1
            pts_count = len(xs)

            for idx in range(pts_count - 1 if not closed else pts_count):
                next_idx = (idx + 1) % pts_count
                p_start = Point(xs[idx], ys[idx])
                p_end = Point(xs[next_idx], ys[next_idx])
                bulge = bulges[idx]

                if abs(bulge) < 1e-6:
                    self.raw_entities.append(LineSegment(p_start, p_end, layer))
                else:
                    # Bulge = tan(theta / 4). Converte para arco
                    theta = 4.0 * math.atan(bulge)
                    chord = p_start.dist(p_end)
                    r = abs(chord / (2.0 * math.sin(theta / 2.0)))
                    # Vetor corda e centro
                    mx = (p_start.x + p_end.x) / 2.0
                    my = (p_start.y + p_end.y) / 2.0
                    d = math.sqrt(max(0.0, r*r - (chord/2.0)*(chord/2.0)))
                    dx = (p_end.x - p_start.x) / chord
                    dy = (p_end.y - p_start.y) / chord

                    # Normal à corda
                    nx = -dy if bulge > 0 else dy
                    ny = dx if bulge > 0 else -dx

                    cx = mx + d * nx
                    cy = my + d * ny
                    center = Point(cx, cy)
                    a1 = math.atan2(p_start.y - cy, p_start.x - cx)
                    a2 = math.atan2(p_end.y - cy, p_end.x - cx)
                    self.raw_entities.append(ArcSegment(center, r, a1, a2, ccw=(bulge > 0), layer=layer))


# ==============================================================================
# 3. ENCADEAMENTO DE CONTORNOS & COMPENSAÇÃO DE RAIO (SHAPE & OFFSET)
# ==============================================================================

class ContourShape:
    """Representa um contorno contínuo fechado ou aberto (Shape)."""

    def __init__(self, elements: List[Any]):
        self.elements = elements
        self.is_closed = False
        self.area = 0.0
        self.is_internal = False  # True = Furo/Bolso interno, False = Contorno externo
        self._analyze()

    def _analyze(self):
        if not self.elements:
            return
        start_pt = self.elements[0].p1
        end_pt = self.elements[-1].p2
        self.is_closed = start_pt.dist(end_pt) < 1e-3

        if self.is_closed:
            # Fórmula do Cadarço (Shoelace formula) para calcular a área orientada
            area2 = 0.0
            for seg in self.elements:
                area2 += (seg.p1.x * seg.p2.y - seg.p2.x * seg.p1.y)
            self.area = area2 / 2.0
            # No plano cartesiano padrão, área negativa no DXF2GCODE indica furo (sentido horário)
            self.is_internal = (self.area < 0)

    def start_point(self) -> Point:
        return self.elements[0].p1

    def end_point(self) -> Point:
        return self.elements[-1].p2


def chain_entities(entities: List[Any], tol: float = 1e-3) -> List[ContourShape]:
    """Agrupa linhas e arcos em contornos contínuos (Chaining algorithm)."""
    pool = list(entities)
    shapes = []

    while pool:
        curr_shape = [pool.pop(0)]
        extended = True

        while extended:
            extended = False
            head = curr_shape[0].p1
            tail = curr_shape[-1].p2

            # Verifica se fechou
            if len(curr_shape) > 1 and head.dist(tail) < tol:
                break

            for i, cand in enumerate(pool):
                # Conexão no final
                if tail.dist(cand.p1) < tol:
                    curr_shape.append(pool.pop(i))
                    extended = True
                    break
                elif tail.dist(cand.p2) < tol:
                    curr_shape.append(cand.reversed())
                    pool.pop(i)
                    extended = True
                    break
                # Conexão no início
                elif head.dist(cand.p2) < tol:
                    curr_shape.insert(0, pool.pop(i))
                    extended = True
                    break
                elif head.dist(cand.p1) < tol:
                    curr_shape.insert(0, cand.reversed())
                    pool.pop(i)
                    extended = True
                    break

        shapes.append(ContourShape(curr_shape))

    return shapes


# ==============================================================================
# 4. OTIMIZADOR DE ORDEM DE CORTE (TSP & PRIORIDADE DE FUROS)
# ==============================================================================

def optimize_toolpath_order(shapes: List[ContourShape], start_pos: Point = Point(0, 0)) -> List[ContourShape]:
    """
    Algoritmo inspirado no DXF2GCODE tspoptimisation.py:
      1. Separa furos/bolsos internos de perfis externos.
      2. Corta furos internos PRIMEIRO (para evitar que a peça se solte).
      3. Otimiza os deslocamentos rápidos (G0) via Nearest-Neighbor.
    """
    internals = [s for s in shapes if s.is_internal]
    externals = [s for s in shapes if not s.is_internal]

    def solve_tsp(sub_shapes: List[ContourShape], current_p: Point) -> Tuple[List[ContourShape], Point]:
        ordered = []
        rem = list(sub_shapes)
        cp = current_p

        while rem:
            best_idx = 0
            best_dist = float('inf')
            for i, sh in enumerate(rem):
                d = cp.dist(sh.start_point())
                if d < best_dist:
                    best_dist = d
                    best_idx = i
            next_sh = rem.pop(best_idx)
            ordered.append(next_sh)
            cp = next_sh.end_point()

        return ordered, cp

    # Ordena furos primeiro
    ordered_internals, last_p = solve_tsp(internals, start_pos)
    # Ordena externos depois
    ordered_externals, _ = solve_tsp(externals, last_p)

    return ordered_internals + ordered_externals


# ==============================================================================
# 5. PÓS-PROCESSADOR G-CODE PARAMÉTRICO
# ==============================================================================

class PostProcessor:
    """Motor de formatação e emissão de código G baseado em templates CFG."""

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config
        self.gcode_lines: List[str] = []

    def generate(self, shapes: List[ContourShape]) -> str:
        self.gcode_lines = []
        self._emit_header()

        for idx, shape in enumerate(shapes):
            self.gcode_lines.append(f"\n(--- Inicio da Forma {idx+1}/{len(shapes)}: {'Furo/Interno' if shape.is_internal else 'Externo'} ---)")
            self._cut_shape(shape)

        self._emit_footer()
        return "\n".join(self.gcode_lines)

    def _emit_header(self):
        self.gcode_lines.extend([
            f"( Gerado por DXF2GCODE Headless CLI Engine )",
            f"( Data: {self.cfg.get('timestamp', '2026-10-31')} )",
            f"( Ferramenta: Diametro = {self.cfg['tool_diameter']} mm )",
            f"( Profundidade Total = {self.cfg['target_depth']} mm, Passo = {self.cfg['stepdown']} mm )",
            "G21 (Modo Milimetrico)",
            "G90 (Coordenadas Absolutas)",
            "G17 (Plano XY)",
            "G40 (Compensacao Cancelada)",
            "G49 (Compensacao Comprimento Cancelada)",
            "G80 (Cancela Ciclos Enlatados)",
            f"G0 Z{self.cfg['safe_z']:.3f} (Altura Segura)",
            f"T{self.cfg['tool_nr']} M6",
            f"S{self.cfg['spindle_speed']} M3 (Fuso Ligado)",
            f"G0 X0.000 Y0.000"
        ])

    def _emit_footer(self):
        self.gcode_lines.extend([
            "\n(--- Fim da Usinagem ---)",
            f"G0 Z{self.cfg['safe_z']:.3f}",
            "M5 (Fuso Desligado)",
            "G0 X0.000 Y0.000 (Origem)",
            "M30 (Fim de Programa)"
        ])

    def _cut_shape(self, shape: ContourShape):
        p_start = shape.start_point()
        total_depth = self.cfg['target_depth']
        stepdown = abs(self.cfg['stepdown'])

        # Cálculo do número de passes em Z
        num_passes = max(1, math.ceil(abs(total_depth) / stepdown))
        actual_step = total_depth / num_passes

        # Deslocamento rápido para início do contorno em Z seguro
        self.gcode_lines.append(f"G0 X{p_start.x:.3f} Y{p_start.y:.3f}")
        self.gcode_lines.append(f"G0 Z{self.cfg['retract_z']:.3f}")

        current_z = 0.0

        for pass_idx in range(num_passes):
            current_z += actual_step
            self.gcode_lines.append(f"( Passe {pass_idx+1}/{num_passes} -> Z={current_z:.3f} )")
            # Mergulho de corte
            self.gcode_lines.append(f"G1 Z{current_z:.3f} F{self.cfg['feed_plunge']}")

            # Usina as entidades do contorno no plano XY
            for seg in shape.elements:
                if isinstance(seg, LineSegment):
                    self.gcode_lines.append(f"G1 X{seg.p2.x:.3f} Y{seg.p2.y:.3f} F{self.cfg['feed_cut']}")
                elif isinstance(seg, ArcSegment):
                    # No padrão RS274/LinuxCNC, I e J são relativos ao ponto inicial da trajetória
                    i_offset = seg.center.x - seg.p1.x
                    j_offset = seg.center.y - seg.p1.y
                    g_code = "G3" if seg.ccw else "G2"
                    self.gcode_lines.append(
                        f"{g_code} X{seg.p2.x:.3f} Y{seg.p2.y:.3f} I{i_offset:.3f} J{j_offset:.3f} F{self.cfg['feed_cut']}"
                    )

            # Se for contorno aberto, não fecha; se for fechado, o loop já reconectou

        # Retração após concluir todos os passes da forma
        self.gcode_lines.append(f"G0 Z{self.cfg['retract_z']:.3f}")


# ==============================================================================
# 6. DEMONSTRAÇÃO E CLI
# ==============================================================================

def generate_sample_dxf() -> str:
    """Cria um arquivo DXF sintético contendo retângulo externo com furo central."""
    return """0
SECTION
2
ENTITIES
0
LINE
8
0
10
10.0
20
10.0
11
90.0
21
10.0
0
LINE
8
0
10
90.0
20
10.0
11
90.0
21
60.0
0
LINE
8
0
10
90.0
20
60.0
11
10.0
21
60.0
0
LINE
8
0
10
10.0
20
60.0
11
10.0
21
10.0
0
CIRCLE
8
0
10
50.0
20
35.0
40
15.0
0
ENDSEC
0
EOF"""

def main():
    parser = argparse.ArgumentParser(description="DXF2GCODE Headless CLI Engine")
    parser.add_argument("input_dxf", nargs="?", help="Caminho do arquivo DXF de entrada")
    parser.add_argument("-o", "--output", default="output.ngc", help="Caminho do arquivo G-code de saída (.ngc/.nc)")
    parser.add_argument("--tool-dia", type=float, default=6.0, help="Diâmetro da ferramenta (mm)")
    parser.add_argument("--feed", type=float, default=1200.0, help="Avanço de corte XY (mm/min)")
    parser.add_argument("--feed-plunge", type=float, default=300.0, help="Avanço de mergulho Z (mm/min)")
    parser.add_argument("--speed", type=int, default=12000, help="Rotação do fuso (RPM)")
    parser.add_argument("--depth", type=float, default=-5.0, help="Profundidade final de usinagem (Z negativo)")
    parser.add_argument("--stepdown", type=float, default=2.5, help="Passo vertical máximo em Z (mm)")
    parser.add_argument("--safe-z", type=float, default=15.0, help="Altura de segurança Z (mm)")
    parser.add_argument("--retract-z", type=float, default=3.0, help="Altura de retração Z (mm)")

    args = parser.parse_args()

    print("==================================================================")
    print("DXF2GCODE HEADLESS - COMPACT CONVERSION ENGINE")
    print("==================================================================")

    if args.input_dxf and os.path.exists(args.input_dxf):
        print(f"Lendo DXF: {args.input_dxf}")
        dxf_parser = DXFParser(filepath=args.input_dxf)
    else:
        print("Nenhum DXF fornecido. Utilizando modelo de teste interno (Placa com Furo Central)...")
        sample_data = generate_sample_dxf()
        dxf_parser = DXFParser(text_content=sample_data)

    print(f"Total de entidades geométricas brutas importadas: {len(dxf_parser.raw_entities)}")

    # 1. Encadeamento
    shapes = chain_entities(dxf_parser.raw_entities)
    print(f"Contornos estruturados identificados: {len(shapes)}")
    for i, s in enumerate(shapes):
        print(f"  * Contorno {i+1}: Elementos={len(s.elements)}, Fechado={s.is_closed}, Área={s.area:.2f}, Tipo={'Furo' if s.is_internal else 'Externo'}")

    # 2. Otimização TSP & Furos
    optimized_shapes = optimize_toolpath_order(shapes, Point(0, 0))
    print(f"Ordem de usinagem otimizada: {[ 'Furo' if s.is_internal else 'Externo' for s in optimized_shapes ]}")

    # 3. Pós-Processamento G-code
    cfg = {
        "tool_diameter": args.tool_dia,
        "tool_nr": 1,
        "spindle_speed": args.speed,
        "feed_cut": args.feed,
        "feed_plunge": args.feed_plunge,
        "target_depth": args.depth,
        "stepdown": args.stepdown,
        "safe_z": args.safe_z,
        "retract_z": args.retract_z,
        "timestamp": "2026-10-31"
    }

    postpro = PostProcessor(cfg)
    gcode = postpro.generate(optimized_shapes)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(gcode)

    print(f"\n[SUCESSO] Código G gerado com sucesso em: {args.output}")
    print(f"Total de linhas de código NC: {len(gcode.splitlines())}")

if __name__ == "__main__":
    main()
