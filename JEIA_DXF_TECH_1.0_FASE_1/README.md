# JEIA_DXF_TECH 1.0 — Fase 1: especificação para aprovação

**Estado: proposta técnica entregue; implementação não autorizada.**

Esta pasta contém exclusivamente documentação, JSON Schema e exemplos sintéticos do contrato. Não é um novo motor, adaptador, validador operacional, executável ou instalador. O JSON Schema é uma especificação declarativa. Não foi conectado à JEIA.

Referências de escopo: arquitetura aprovada pelo usuário como relatório 003 e auditoria do commit original `456495402676e7b4bee023377d5fea0ddfa8230f`. A correção anterior permanece separada, na branch `correcao-cad041-respostas`, commit `37eddd74657e86b962191bc78d8b1388f8adf01a`. Nenhum desses arquivos é modificado por esta entrega.

## Conteúdo e ordem de leitura

1. [ESPECIFICACAO.md](ESPECIFICACAO.md): finalidade, estrutura, presença dos campos, estados e consumo seguro.
2. [JEIA_DXF_TECH_1.0.schema.json](JEIA_DXF_TECH_1.0.schema.json): schema JSON Schema Draft 2020-12 completo, com referências exclusivamente locais.
3. [DICIONARIO_DE_CAMPOS.md](DICIONARIO_DE_CAMPOS.md): campos obrigatórios/opcionais, tipos, enums e variantes geométricas.
4. [REGRAS_E_INVARIANTES.md](REGRAS_E_INVARIANTES.md): identidade, unidades, matrizes, cotas, classificação, reconciliação e deduplicação.
5. [EXEMPLOS.md](EXEMPLOS.md) e pasta `exemplos/`: instâncias completas e contraprovas do contrato.
6. [PLANO_DE_TESTES_E_APROVACAO.md](PLANO_DE_TESTES_E_APROVACAO.md): testes automatizados previstos, resultados esperados e critérios de aprovação.
7. [VERIFICACAO_DA_ENTREGA.md](VERIFICACAO_DA_ENTREGA.md): verificações documentais realmente realizadas e limites.
8. `MANIFESTO_SHA256.txt`: integridade dos arquivos entregues, sem incluir o próprio manifesto.

## Autoridade normativa

- O schema define estrutura, tipos, campos, enums e restrições locais.
- As regras com identificadores em `REGRAS_E_INVARIANTES.md` são igualmente obrigatórias: definem relações entre registros, interpretação e impedimentos de consumo.
- Um JSON que passa no schema pode falhar semanticamente. Essa diferença é demonstrada por contraprovas.
- O plano de testes define a evidência futura necessária para aprovar implementações. Não é uma implementação desses testes.
- Exemplos ilustram decisões; não ampliam suporte nem substituem regras. Em caso de divergência, o contrato deve ser revisado antes da implementação, sem escolher silenciosamente uma interpretação.

Todos os exemplos têm `context.purpose = synthetic_example`, hashes fictícios identificados como tais e bloqueio de consumo operacional. Não são saídas reais dos motores nem desenhos liberados para fabricação. Os exemplos descrevem entidades de desenhos DXF no contrato; **não são arquivos DXF nativos**. Fixtures DXF executáveis de regressão serão uma entrega futura, após autorização.

## Exclusões desta fase

Não há alteração da CAD 04.1, dos motores, das nove abas, de STEP, da instalação Windows, da proteção contra respostas obsoletas ou da branch main. Não há instalação de dependências. A integração e os testes operacionais dependem de nova autorização.
