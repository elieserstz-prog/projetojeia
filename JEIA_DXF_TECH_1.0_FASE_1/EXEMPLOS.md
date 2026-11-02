# Exemplos estruturados e contraprovas

As instâncias em `exemplos/` são JSONs completos do contrato, não trechos a serem preenchidos. **Não são arquivos DXF nativos nem saídas reais de FreeCAD/ezdxf.** São modelos documentais de como representar desenhos e resultados futuros. Handles, nomes, atores e hashes são ilustrativos. `byteLength=0` e hashes repetidos são placeholders declarados pelo diagnóstico `SYNTHETIC_DATA`; nunca devem ser aceitos como identidade de um desenho real.

Todos os casos positivos continuam bloqueados para material/processo/custo por serem sintéticos. Ser válido estrutural/semanticamente é diferente de estar autorizado para uso. Os campos `schemaStatus`/`semanticStatus` internos continuam `not_checked` para não transformar os exemplos em resultados autodeclarados de um consumidor inexistente.

## 01 — Placa, moldura, carimbo, bloco, cota e duas vistas

Arquivo: [01_placa_folha_carimbo.json](exemplos/01_placa_folha_carimbo.json).

- Model em mm: contorno retangular 100 × 60 e círculo de raio 5, com uma representação repetida deslocada 200 mm em X.
- `v-front` e `v-detail` são associadas à mesma peça por decisão de operador **sintético**, em escala 1:1. A tradução da segunda vista é explicitada em `t-v2`.
- Cota linear de 100 mm: medição geométrica, nominal/apresentação e estilo preservados, com tolerância bilateral -0.1/+0.1 mm. A tolerância não é um parâmetro numérico do software.
- Layout Paper separado: contorno de folha 420 × 297 mm; carimbo em bloco com origem [270,0,0], geometria em layer 0 e layer efetiva CARIMBO. Texto de desenho e revisão permanece como anotação.
- A classificação da moldura usa topologia e template verificado; o carimbo usa estrutura do bloco e semântica dos campos; a peça usa estrutura de contornos e associação dimensional/projeção. Nenhuma exclusão se baseia só no nome da layer.
- Dois círculos documentais representam, por decisão explícita simulada, **um** furo físico: duas `observations`, uma relação `same_feature`, uma `feature` e uma intenção de furação com quantity=1.
- Profundidade, passância e montagem permanecem desconhecidas. A intenção de furação é bloqueada, mesmo havendo confirmação da identidade do furo.
- Observações de diâmetro ezdxf e FreeCAD são guardadas separadamente e concordam em 10 mm. Essa concordância não identifica sozinha a função de fabricação. O vínculo da observação FreeCAD à entidade é uma premissa declarada do cenário sintético; um adaptador real deverá demonstrá-lo ou manter a geometria sem associação.

IDs-chave: `e-hole1`/`e-hole2` são entidades diferentes; `obs-hole-front`/`obs-hole-detail` são observações; `feature-hole` é a hipótese física confirmada no exemplo. O bloco de carimbo e suas ocorrências têm identidades próprias.

## 02 — Transformações, polegadas, MINSERT, OCS e escalas independentes

Arquivo: [02_transformacoes_layouts_escalas.json](exemplos/02_transformacoes_layouts_escalas.json).

O desenho Model usa polegadas; o layout Paper usa mm. Não aplicar 25.4 ao papel. Há dois INSERTs virtuais/células derivados de um MINSERT, mantendo o mesmo handle de definição e IDs de ocorrência distintos.

### Cálculo de bloco e grade

Definição de bloco com base b=[1,0,0]; círculo local de raio 1 na origem. INSERT i=[10,20,0], escala S=[2,1,1], rotação 90°, normal +Z. A matriz em coordenadas de desenho é:

```text
M0 = T(10,20,0) Rz(90°) S(2,1,1) T(-1,0,0)
   = [ 0 -1  0 10 ]
     [ 2  0  0 18 ]
     [ 0  0  1  0 ]
     [ 0  0  0  1 ]
```

O círculo vira elipse. Centro canônico: [254,457.2,0] mm; semieixos [0,50.8,0] e [-25.4,0,0] mm. Manter CIRCLE de raio 50.8 seria incorreto.

Para coluna c=1 com columnSpacing=5, a grade é rotacionada para [0,5,0] e **não** multiplicada por S. O segundo centro é [254,584.2,0] mm. Se a grade fosse escalada, o centro seria errado.

As geometrias elípticas derivam de `g-circle-local`; `appliedTransformIds` registra a matriz de cada célula e a conversão de unidades na ordem de aplicação. Não há fusão por geometria/handle.

### OCS inclinado

Círculo com centro OCS [2,3,4], raio 1 e extrusion [0,1,0]. Pelo Arbitrary Axis Algorithm: Ax=[-1,0,0], Ay=[0,0,1], N=[0,1,0]. Centro WCS=[-2,4,3] polegadas, ou [-50.8,101.6,76.2] mm. A normal canônica é [0,1,0]. Não achatar para Z=0. Essa ocorrência fica fora das vistas candidatas de planejamento; não há interpretação de furo associada.

### Viewport e escala de detalhe

Viewport ortográfica: altura Model=10 polegadas=254 mm; altura no papel=50.8 mm. Escala de apresentação física=0.2. O mapeamento numérico de coordenadas Model em polegadas para papel em mm tem fator 5.08, não 0.2. A matriz inclui centro do papel [100,100,0]. Seu Z conserva profundidade de vista conforme VP-02, sem constituir medida física no papel.

Uma linha de detalhe de x=30 a x=31 polegadas mede 25.4 mm **representados**. A vista `v-detail` tem drawingPerPart=0.5, portanto o comprimento físico ilustrativo é 50.8 mm. `spaceToViewTransformId` converte unidades e desloca a origem; `viewToPartTransformId` aplica o fator 2. O viewport não entra nessa cadeia uma segunda vez. As associações são simuladas, não validação de um desenho industrial.

## 03 — Conflito entre motores e interpretação ambígua

Arquivo: [03_conflito_e_ambiguidade.json](exemplos/03_conflito_e_ambiguidade.json).

Uma mesma ocorrência, no mesmo frame e unidade, recebe círculo de raio 5 do ezdxf e raio 6 do FreeCAD. Diâmetros 10 e 12 mm são preservados em observações independentes. O reconciliador documental indica `differ`, delta=2 mm, sem `selectedObservationId` e sem geometria canônica selecionada.

O círculo também pode representar perfil externo, furo ou construção. `selectedClass=null`, `inclusion=pending`, sem feature ou operação inventada. A vista não tem peça associada nem escala física determinada e está desabilitada para planejamento. Um diagnóstico impede consumidores dependentes; não há média de diâmetros nem preferência automática por motor.

## 04 — Unidade não declarada

Arquivo: [04_unidade_ausente.json](exemplos/04_unidade_ausente.json).

`$INSUNITS=0`, fator mm/unidade nulo, comprimento geométrico bruto 10 em `drawing_unit`. Não há equivalente de 10 mm nem geometria física canônica escolhida. O dado é preservado para revisão, com `UNITS_UNRESOLVED` e bloqueio de material/processo/custo. Transform identidade no próprio frame bruto não resolve unidade.

## Contraprovas

| Arquivo | Schema | Semântica esperada | Motivo |
|---|---|---|---|
| [N01_estrutura_invalida.json](exemplos/N01_estrutura_invalida.json) | Rejeitar | Não avaliar para consumo | Ausência de selectionGeneration obrigatório |
| [N02_operacao_duplicada.json](exemplos/N02_operacao_duplicada.json) | Aceitar | Rejeitar OP-01 | Dois IDs diferentes com a mesma chave de intenção de furação |
| [N03_unidade_ausente_liberada.json](exemplos/N03_unidade_ausente_liberada.json) | Aceitar | Rejeitar UN-02/EL-01/EL-03 | Elegibilidade material indevida com unidade ausente e pacote sintético |

O [manifesto](exemplos/manifesto.json) declara resultados esperados e regras de cada caso. Não é um runner de testes. Rejeições semânticas não estão implementadas por esta entrega; as verificações documentais realizadas são descritas separadamente.
