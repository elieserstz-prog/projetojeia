# JEIA_DXF_TECH FASE 2A

**EXPERIMENTAL — SOMENTE PARA TESTES. Não integrado à JEIA.**

Adaptador Python independente usando ezdxf. Lê um DXF ASCII, preserva os bytes de entrada e produz JSON estruturalmente compatível com `JEIA_DXF_TECH 1.0`. Não importa módulos da CAD 04.1, não usa FreeCAD/Qt, não abre serviços, não gera G-code e não instala dependências automaticamente.

Branch: `desenvolvimento-dxf-fase-2a`, criada a partir de `456495402676e7b4bee023377d5fea0ddfa8230f`. A alteração fica inteiramente em `dxf_fase_2a/`, mais o ZIP e seu checksum na raiz da branch. Não contém a correção anterior de respostas CAD.

## Baixar

[**Baixar JEIA_DXF_TECH_FASE_2A.zip**](https://github.com/elieserstz-prog/projetojeia/raw/refs/heads/desenvolvimento-dxf-fase-2a/JEIA_DXF_TECH_FASE_2A.zip)

O navegador salva o arquivo conforme suas configurações, normalmente em Downloads. O ZIP contém somente esta entrega independente: adaptador, schema, regras de referência, DXFs sintéticos, resultados JSON, testes e relatório técnico. Não inclui arquivos da instalação CAD nem os fontes originais da aplicação.

## Executar separadamente no Windows

Extraia o ZIP em uma pasta própria, por exemplo `Downloads\JEIA_DXF_TECH_FASE_2A`. No PowerShell dessa pasta, com Python 3.12 disponível:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m jeia_dxf_tech examples\01_geometrias_mm.dxf --output resultado.json
```

Esses comandos são instruções para uma futura execução local isolada. Não foram executados no Windows nesta sessão e não devem ser rodados na pasta da instalação atual da JEIA. Não é necessário instalar FreeCAD ou Qt para este adaptador. Durante o desenvolvimento foram usadas dependências já disponíveis no ambiente Linux, sem instalação de pacotes.

Em Linux, com as dependências disponíveis:

```sh
python3 -m unittest discover -s tests -v
python3 -m jeia_dxf_tech examples/03_blocos_polegadas_ocs.dxf --output resultado.json
```

Sem `--output`, o JSON vai para stdout. Um arquivo de saída existente é recusado; o adaptador também impede usar o DXF de entrada como saída. Não existe opção de sobrescrever o desenho. A importação Python é:

```python
from jeia_dxf_tech import extract, Options
resultado = extract('peca.dxf', Options(request_id='teste-001', selection_generation=1))
```

## O que está implementado

- SHA-256 dos bytes lidos uma vez; requisição, geração da seleção e revisão no contexto.
- Entidades e tags originais (ordem, repetições e texto), incluindo vértices de POLYLINE e atributos anexados.
- Model/Paper separados; layers, estilos, definições de blocos e cada ocorrência/instância.
- Geometria analítica LINE, ARC, CIRCLE, ELLIPSE, POINT, LWPOLYLINE, POLYLINE 2D/3D.
- OCS/WCS, z/elevacão, escalas de blocos, espelhamentos e composição de blocos aninhados.
- MINSERT com células distintas, grade rotacionada sem escala indevida e diagnóstico de células coincidentes.
- Conversões industriais explícitas para mm; unidade ausente/desconhecida não vira fator 1.
- Curvas de polilinha normalizadas como COMPOSITE_CURVE; escala não uniforme pode produzir ELLIPSE.
- Cotas no Model, Paper e blocos; valores geométricos calculáveis, style/overrides e tolerâncias brutas preservados.
- Textos/atributos e câmeras de viewport preservados para inspeção.
- Validação estrutural local pelo schema congelado da Fase 1; limites e entidades sem suporte diagnosticados.

## O que NÃO está implementado

Esta é extração, não reconhecimento físico completo. Não há classificação automática de molduras/carimbos/peças, associação de vistas, confirmação do operador, identificação/deduplicação de furos físicos, operações, cálculos de matéria-prima ou orçamento. Os arrays físicos ficam vazios e os consumidores operacionais ficam bloqueados. Nem mesmo um círculo corretamente extraído é promovido a furo.

Não há execução FreeCAD nem reconciliação entre motores. Não há validador semântico completo: `semanticStatus=not_checked`. Não há recuperação automática de arquivo corrompido, suporte a DXF binário, resolução de Xrefs, mapeamento inverso de viewport/perspectiva ou leitura física automática de tolerâncias. SPLINE e outros tipos ainda não implementados são retidos com diagnóstico `unsupported`.

Larguras e thickness são preservados nos dados brutos, mas a geometria canônica de polilinha representa linha central; o diagnóstico impede tratar isso como superfície/bruto. Cotas em blocos transformados mantêm os dados originais sem inventar fator de escala da dimensão. `displayMeasurement` permanece indefinido; o código não substitui nominal por envelope.

Consulte [RELATORIO_TECNICO.md](RELATORIO_TECNICO.md) para validações e limites. O [schema](jeia_dxf_tech/schema.json) é uma cópia byte a byte da Fase 1; não foi alterado para fazer os testes passarem.

## Publicação

A consulta à API do GitHub para preparar uma Release retornou `Forbidden` nesta sessão. A autenticação HTTPS Git permitiu publicação em branch; por isso o ZIP está disponibilizado diretamente na branch, conforme alternativa autorizada. Não foi criada Release e não há integração à main.

Qualquer integração ao reconhecimento operacional JEIA depende de aprovação posterior.
