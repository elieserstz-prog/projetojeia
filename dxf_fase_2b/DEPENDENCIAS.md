# Dependências e isolamento

- Runtime controlador/contrato: biblioteca padrão Python 3.10 ou superior.
- Coletor/importador: FreeCAD/Part/Import já instalados e um Python nativamente compatível, ou FreeCADCmd do próprio FreeCAD.
- Testes de contrato/probe: jsonschema disponível no Python host; nesta sessão foi usada a versão 4.26.0 já instalada.
- Não há dependência de ezdxf, PyQt6, aplicação JEIA ou módulos dos motores antigos.
- Nenhum script executa pip, winget, apt, downloads ou instalação automática.
- PySide ausente no ambiente foi documentado; não foi instalado ou substituído.
- A ativação da pasta de bibliotecas é explícita e limitada ao processo de teste. `native.py` adiciona ao sys.path somente o Draft já existente no diretório de recursos do próprio FreeCAD. Não modifica arquivos daquela pasta.

As versões Linux testadas não comprovam compatibilidade Windows. Não use bibliotecas nativas compiladas para outro Python/arquitetura. O pacote não distribui bibliotecas, DLLs, arquivos .so, binários ou conteúdo da instalação CAD.
