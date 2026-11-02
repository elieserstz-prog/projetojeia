# Relatório técnico — Fase 2A

**Experimental — somente para testes. Adaptador independente; nenhuma integração à JEIA.**

## Resultado e escopo

Implementada leitura DXF ASCII com ezdxf 1.4.4 e emissão do contrato `JEIA_DXF_TECH 1.0`, usando o schema entregue na Fase 1 sem alterações. A saída preserva estrutura documental e observações geométricas; não executa as fases de interpretação física, confirmação na interface ou planejamento.

Base de desenvolvimento: commit original `456495402676e7b4bee023377d5fea0ddfa8230f`. Branch exclusiva `desenvolvimento-dxf-fase-2a`. A correção `correcao-cad041-respostas` e sua implementação não fazem parte desta entrega.

## Arquivos

| Caminho | Função |
|---|---|
| `jeia_dxf_tech/adapter.py` | API independente de extração, normalização e diagnóstico |
| `jeia_dxf_tech/__main__.py` | CLI com saída JSON e recusa de sobrescrita |
| `jeia_dxf_tech/__init__.py` | API pública `extract`, `Options`, `AdapterError`, `validate_structure` |
| `jeia_dxf_tech/schema.json` | Schema congelado JEIA_DXF_TECH 1.0 |
| `tests/test_adapter.py` | Suíte unittest de regressão com ezdxf real |
| `examples/*.dxf` | Quatro desenhos sintéticos reais, independentes da instalação CAD |
| `examples/generate_examples.py` | Geração explícita dos exemplos, sem sobrescrever arquivos existentes |
| `examples/resultados/*.json` | Resultados de extração dos desenhos distribuídos |
| `requirements.txt` | Versões utilizadas de ezdxf/jsonschema |
| `CONTRATO_REGRAS_1.0.md` | Referência normativa da Fase 1; não representa implementação completa |
| `RESULTADOS_TESTES.txt` | Resultado da execução local da suíte |

## Comportamento técnico

O arquivo é lido uma única vez, com limite de tamanho; o hash e o parser usam os mesmos bytes. A codificação é detectada pelo cabeçalho; decodificação inválida, tags desemparelhadas, handles duplicados e entrada binária são recusados. Não é usado `ezdxf.recover` e não há modificação do arquivo de origem.

IDs são derivados do hash, proprietário e handle/ordinal original. Ocorrências incluem espaço e caminho de instâncias/células. Entidades coincidentes não são deduplicadas fisicamente. Handle ausente só usa fallback quando a correspondência com o registro bruto é não ambígua; casos antigos sem handles suficientes podem ser recusados, em vez de inventar identidade. Helpers SEQEND sintetizados pela biblioteca não são apresentados como entidades originais.

Model e Paper têm frames e unidades separados. Matrizes nativas ezdxf são convertidas à convenção vetores-coluna do contrato. Normalização preserva OCS, elevação e orientação; círculos/arcos sob escala não uniforme são representados como elipses/trechos elípticos. Polilinhas curvas tornam-se composições de segmentos analíticos, com orientação explícita; correspondência degenerada de segmentos não é adivinhada.

Layers originais e efetivas, BYLAYER/BYBLOCK e visibilidade são preservados, mas não são usados como prova de função física. Blocos aninhados, pontos-base e MINSERT são tratados por instância, com parada explícita em recursão/limite. Células coincidentes ficam registradas com ambiguidade, sem inferir quantidade de peças.

Cotas preservam dados brutos, pontos, estilos e overrides, sem truncamento fixo em 500. Medição geométrica escalar só é convertida quando unidade e contexto permitem. Valores angulares calculados pela API ezdxf são convertidos de graus para rad; o grupo 42 angular bruto não recebe unidade assumida. Valores vetoriais de cotas ordenadas são conservados em diagnóstico, sem escolher eixo arbitrário. Nominal apresentado, associações à peça e tolerâncias físicas permanecem pendentes quando não interpretados.

## Validação executada

Ambiente Linux, Python 3.12.14, ezdxf 1.4.4 e jsonschema 4.26.0 já disponíveis. **Nenhuma dependência foi instalada nesta tarefa.**

Comando, na pasta independente:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Resultado final da suíte: **61 testes executados, 61 passaram, zero falhas/erros/skips.** O log acompanha o pacote. A suíte também é executada a partir do conteúdo extraído do ZIP, para verificar importação do módulo, presença do schema, exemplos e independência dos caminhos da instalação CAD.

Cobertura: tipos geométricos suportados; arco cruzando 0°; bulges esparsos/negativos/maiores que semicircunferência; fechamento; OCS/elevacão; polegadas/quilômetros; unidade ausente/astronômica; Model/Paper; atributos; layers/visibilidade; blocos rotacionados, aninhados, espelhados e não uniformes; MINSERT e células coincidentes; ciclos e limites; cotas em blocos/Paper, style/overrides e 501 cotas; câmera de viewport; tipos sem suporte; codificação legada; bytes e identidade; schema; CLI e recusa de sobrescrita.

Os testes conferem preservação dos bytes dos DXFs. A validação estrutural é real e executada; não deve ser confundida com cumprimento automático de todas as invariantes semânticas da Fase 1. Os testes geométricos usam fixtures analíticas sintéticas, não um corpus industrial aprovado.

## Exemplos distribuídos

| Arquivo | Cenário |
|---|---|
| `01_geometrias_mm.dxf` | Linha, círculo, arco e polilinhas em mm |
| `02_peca_folha_carimbo_cotas.dxf` | Peça no Model, folha/carimbo no Paper, bloco, atributo, cotas e viewport |
| `03_blocos_polegadas_ocs.dxf` | Polegadas, MINSERT não uniforme rotacionado e círculo OCS inclinado |
| `04_unidade_ausente.dxf` | Unidade ausente, texto em codificação legada e spline sem suporte |

Os JSONs anexos foram extraídos desses arquivos, não são confirmações simuladas de operador. Seus hashes correspondem aos DXFs reais distribuídos. A natureza experimental mantém todos os consumidores operacionais bloqueados.

## Limites e riscos restantes

- Extração somente; não separa semanticamente peça/moldura/carimbo, não associa vistas ou furos e não gera operações.
- FreeCAD não foi executado e nenhuma observação ou concordância desse motor foi fabricada. `reconciliations` permanece vazio.
- Não implementa todo o contrato semântico; `semanticStatus` permanece `not_checked` e CNC sempre falso.
- Leitura ASCII com codificação declarada; binário, Xrefs e recuperação de corrupção não são suportados nesta fase.
- SPLINE, HATCH, meshes e outros tipos fora do conjunto implementado são preservados como entidades brutas, com diagnóstico de geometria sem suporte. Não há conversão aproximada silenciosa.
- Câmeras e parâmetros de viewport são preservados, mas não há mapeamento/recorte inverso ou extração de dimensão física do papel. Escala de vista física não é inferida como 1:1.
- Cotas dentro de blocos transformados, apresentação nominal e tolerâncias exigem interpretação posterior; parâmetros não são omitidos silenciosamente.
- Largura e thickness não são modelados como superfícies/sólidos; linha central não equivale a bruto.
- Limites padrão: 64 MiB de entrada, 100 mil entidades da biblioteca, 100 mil ocorrências/instâncias e profundidade 32. Tamanho/entidades excedidos recusam a entrada; expansão parcial por limite de ocorrência/profundidade gera diagnóstico de cobertura incompleta.
- Referências e identidade têm testes básicos; não existe validador semântico completo de todo o grafo. Uso operacional continua proibido.
- O schema 1.0 não possui `viewport` em Target.kind; diagnósticos de viewport referenciam sua entidade DXF, preservando o ID do viewport em details. O schema não foi alterado para contornar esse detalhe.
- Windows, FreeCAD e interface CAD não foram executados. Compatibilidade nessa plataforma requer teste separado antes de qualquer integração.

## Publicação e preservação

Somente os arquivos da pasta nova e o ZIP/checksum foram adicionados à branch derivada da base original. Nenhum arquivo original da CAD é incluído no ZIP. Não foram alterados motores, abas, fluxo STEP, main ou instalação Windows; não foi gerado executável/instalador.

A consulta à API do GitHub retornou `Forbidden`, impedindo preparar uma Release nesta sessão. Foi usada a alternativa autorizada: arquivo ZIP diretamente na branch, com link de download e checksum. O commit exato publicado é informado no retorno da tarefa e pode ser conferido na branch GitHub.

**Qualquer integração ao JEIA continua condicionada à aprovação do usuário.**
