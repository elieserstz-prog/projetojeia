# Verificação documental da Fase 1

## O que foi executado nesta entrega

Usados apenas Python e `jsonschema` já disponíveis no ambiente, sem instalar dependências e sem executar motores CAD, interface JEIA ou fluxo STEP.

| Verificação | Resultado observado |
|---|---|
| JSON Schema contra meta-schema Draft 2020-12 | Válido |
| Formatos dos exemplos, incluindo RFC 3339 | Verificados com FormatChecker ativo |
| Quatro exemplos positivos completos | Todos aceitos pelo schema |
| N01: selectionGeneration ausente | Rejeitado no campo obrigatório esperado |
| N02: operação duplicada | Aceito estruturalmente; checagem documental identificou repetição da chave OP-01 |
| N03: unidade ausente liberada | Aceito estruturalmente; checagem documental identificou elegibilidade indevida e natureza sintética |
| IDs e referências tipadas nos sete exemplos | Sem duplicação de ID de registro ou referência órfã nas relações conferidas |
| Hash de entrada declarado nas fontes | Coincide com o hash fictício declarado pelo exemplo |
| Forma afim das matrizes de transformação | Última linha [0,0,0,1] nos exemplos |
| MINSERT: centros após rotação, escala e conversão | [254,457.2,0] e [254,584.2,0] mm conferidos |
| OCS inclinado convertido para WCS/mm | [-50.8,101.6,76.2] mm conferido |
| Detalhe: 1 polegada representada na escala 1:2 | 50.8 mm físicos no exemplo, sem somar escala do viewport |

Essas verificações foram realizadas por comandos temporários de conferência dos artefatos. Não foi entregue nem integrado um validador semântico operacional. Não constituem prova de implementação de todas as regras nem de resultados dos motores em DXFs reais.

## O que permanece previsto, não executado

- Extração completa por adaptadores ezdxf/FreeCAD e reconciliação de arquivos reais.
- Validação semântica automatizada de todas as invariantes.
- Classificação automática de molduras/carimbos/peças e confirmação na interface.
- Associação de características entre vistas e integração ao planejamento/orçamento.
- Corpus DXF industrial revisado, testes operacionais da matriz de 30 verificações e casos adicionais.
- Compatibilidade funcional em Windows, nove abas e fluxo STEP.

Os resultados dessas etapas não podem ser inferidos da validação estrutural deste schema. Os valores `expectedSemanticValid` do manifesto são expectativas normativas para a futura suíte, não afirmação de execução de um validador completo.

## Preservação do trabalho existente

Os artefatos estão fora do checkout `/workspace/projetojeia`. O commit original de referência e a correção da Etapa 1 não foram alterados, nem houve integração à main. Nenhuma instalação Windows foi acessada. A pasta `vendor/` não versionada que já existia no checkout permanece fora desta entrega.

Situação final: **especificação documental pronta para revisão e aprovação do usuário; nenhuma implementação da próxima fase autorizada ou iniciada.**
