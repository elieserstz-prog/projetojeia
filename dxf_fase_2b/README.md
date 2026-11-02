# JEIA_DXF_TECH — FASE 2B

**EXPERIMENTAL — SOMENTE PARA TESTES. IMPORTAÇÃO DXF NÃO APROVADA NESTE AMBIENTE.**

[**⬇️ BAIXAR JEIA_DXF_TECH_FASE_2B.zip**](https://github.com/elieserstz-prog/projetojeia/raw/refs/heads/desenvolvimento-dxf-fase-2b/JEIA_DXF_TECH_FASE_2B.zip)

Adaptador FreeCAD independente: código-fonte, schema congelado 1.0, testes, quatro exemplos DXF, resultados de geometria real e diagnósticos das importações que falharam. O ZIP não contém binários, bibliotecas instaladas, instalador ou arquivos da instalação CAD.

Branch `desenvolvimento-dxf-fase-2b`, derivada de `456495402676e7b4bee023377d5fea0ddfa8230f`. Nenhuma alteração na main, na Fase 2A, na correção de respostas CAD, nos motores antigos, nas nove abas ou no fluxo STEP.

## Estado real da validação

| Categoria | Resultado |
|---|---|
| Contrato/controlador/robustez, com simulações identificadas | 33 testes passaram |
| Fixtures de geometria com FreeCAD/Part reais | 12 passaram |
| Importação DXF via FreeCADCmd | 1 tentativa falhou (SIGSEGV) |
| Importação DXF via Python compatível + bibliotecas FreeCAD existentes | 4 tentativas falharam |
| Integração DXF aprovada | **Não** |

As fixtures de kernel criam geometria em memória para testar o coletor; NÃO são resultados extraídos dos quatro DXFs. O FreeCADCmd falha ao iniciar. A rota alternativa explícita também falhou em `Import.readDXF`; verificou-se que `import Draft` encontra `ModuleNotFoundError: No module named 'PySide'`. Não foram instaladas dependências nem modificadas bibliotecas para contornar o problema.

O probe retorna saída 1 porque a importação integrada falhou. As falhas não foram convertidas em testes aprovados, skips ou expected failures. Consulte [RELATORIO_TECNICO.md](RELATORIO_TECNICO.md) e [validation/PROBE_RESULTADOS.json](validation/PROBE_RESULTADOS.json).

## Componentes

- `jeia_dxf_freecad/collector.py`: coleta shapes/curvas/arestas/faces e BREP sem alterar os objetos.
- `native.py`: usa `Import.readDXF` em documento temporário, fecha apenas o documento criado e restaura o documento ativo anterior.
- `runner.py` e `worker.py`: isolamento em processo, timeout, snapshot dos bytes, hash e conferência de identidade da resposta.
- `contract.py`: contrato usando somente biblioteca padrão; sem dependência de ezdxf, Qt ou JEIA.
- `schema.json`: cópia byte a byte do schema da Fase 2A, sem extensão de campos.
- `tests/`: testes unitários e probe real com resultados separados por rota/caso.

## Uso isolado com FreeCAD já instalado

Não execute esta entrega dentro da pasta da CAD atual. Extraia o ZIP em uma pasta própria. O adaptador NÃO instala dependências, não faz downloads e não altera arquivos de entrada.

Exemplo de terminal Windows com um Python **já disponível** e um FreeCADCmd já instalado:

```powershell
python -m jeia_dxf_freecad examples\01_geometrias_mm.dxf --freecad-cmd "C:\Caminho\FreeCAD\bin\FreeCADCmd.exe" --output resultado.json
```

O caminho acima é ilustrativo: use o executável existente no seu computador. Não há tentativa automática de instalar ou substituir o FreeCAD. Sem `--output`, o JSON é escrito em stdout; saída existente é recusada. Saída 0 significa observações nativas produzidas, NÃO aprovação de integração/fabricação. Saída 2 indica falha/ausência de geometria, com JSON diagnóstico quando foi possível identificar o arquivo.

Rota alternativa explícita, apenas para um Python já compatível com as bibliotecas FreeCAD instaladas:

```sh
python -m jeia_dxf_freecad examples/01_geometrias_mm.dxf \
  --api-python /usr/bin/python3 --freecad-lib /usr/lib/freecad/lib \
  --output resultado.json
```

Esses caminhos correspondem ao Linux desta sessão. Não aponte um Python incompatível para bibliotecas nativas de outra versão/arquitetura. Não existe fallback silencioso entre as duas rotas.

Dentro do Console Python de um FreeCAD já aberto, o código pode ser carregado de uma pasta separada:

```python
import sys, json
sys.path.insert(0, r'C:\PastaSeparada\JEIA_DXF_TECH_FASE_2B')
from jeia_dxf_freecad.native import extract_native
resultado = extract_native(r'C:\DesenhosDeTeste\exemplo.dxf')
with open(r'C:\ResultadosDeTeste\resultado.json', 'x', encoding='utf-8') as f:
    json.dump(resultado, f, ensure_ascii=False, allow_nan=False, indent=2)
```

Este exemplo não foi executado no Windows. Em caso de falha do importador, o console apresenta a exceção. A CLI com worker é preferível para testes de importação porque isola crashes.

## Reproduzir os testes

O runtime do adaptador usa biblioteca padrão e FreeCAD previamente instalado. Os testes de schema utilizam `jsonschema` já disponível no ambiente de desenvolvimento. Nenhum script instala pacotes; se essa biblioteca de teste não existir em outra máquina, a validação estrutural não estará disponível ali.

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python tests/probe_freecad.py --api-python /usr/bin/python3 \
  --freecad-lib /usr/lib/freecad/lib --freecad-cmd /usr/bin/freecadcmd \
  --output resultados_novos
```

O diretório de resultados do probe deve ser novo. Cada teste nativo roda em processo separado. O resultado agregado continua falho se qualquer integração exigida falhar.

Todos os consumidores de matéria-prima, processo e orçamento permanecem bloqueados; `cncReleased=false`. Qualquer integração à JEIA depende de nova autorização.
