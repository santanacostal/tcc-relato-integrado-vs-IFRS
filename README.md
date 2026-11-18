# Relato Integrado × IFRS S1/S2: scripts, dicionário e checklist

Material complementar do Trabalho de Conclusão de Curso "Comparação entre o Relato Integrado e as
Informações Financeiras Relacionadas à Sustentabilidade: uma análise das abordagens IIRC e IFRS S1/S2"
(Ciências Contábeis, FEA/USP, 2026).

O estudo compara dez documentos do exercício de 2025 (o Relato Integrado ou relatório anual e o relatório
IFRS S1/S2 de cinco companhias: Irani, Natura, Lojas Renner, B3 e Vale) por frequência de termos,
emissões de gases de efeito estufa e checklist de divulgação.

## O que há neste repositório

| Pasta/arquivo | Conteúdo |
|---|---|
| `scripts/extrair_corpus.py` | Converte cada PDF em texto, página a página, ignorando menus, cabeçalhos e rodapés (topo 10%, rodapé 6% da página e linhas repetidas em 30% ou mais das páginas). |
| `scripts/analise_termos.py` | Conta os termos do dicionário por variável e normaliza por 10 mil palavras. Gera as tabelas de frequência, a razão IFRS ÷ RI/anual e os gráficos. |
| `scripts/tabelas_emissoes.py` | Extrai as tabelas de emissões (Escopos 1, 2 e 3) dos relatórios IFRS. Os valores usados no trabalho foram conferidos manualmente contra a página de origem. |
| `dados/dicionario_termos.csv` | As 51 expressões do dicionário, por variável, com a expressão regular de cada uma. |
| `dados/resultados/` | Tabelas de frequência geradas pelos scripts na execução do trabalho (`frequencia_por_variavel.csv`, `matriz_documento_x_variavel.csv`, `comparacao_RI_vs_IFRS.csv`). |
| `checklist/Checklist_divulgacao.xlsx` | Notas de 0 a 2 por variável e documento, com a página do PDF e o trecho que sustenta cada nota. |

## Não incluído

Os PDFs dos relatórios não são redistribuídos aqui. Eles são públicos e foram obtidos nos sites de
relações com investidores de cada empresa (exercício de 2025, publicados em 2026); as referências
completas estão no trabalho.

## Como reproduzir

1. `pip install -r requirements.txt`
2. Baixe os dez PDFs e ajuste os nomes dos arquivos no dicionário `DOCUMENTOS` de `scripts/extrair_corpus.py`.
3. `python scripts/extrair_corpus.py PASTA_DOS_PDFS saida`
4. `python scripts/tabelas_emissoes.py PASTA_DOS_PDFS saida`
5. Crie `saida/paginas_excluir.csv` (colunas `rotulo,paginas`) com os sumários e índices GRI/SASB a excluir da contagem.
6. `python scripts/analise_termos.py saida`

As contagens usam apenas expressões regulares em texto sem acentos e em minúsculas. Não há etapa de
inteligência artificial na execução.

## Limitações

- A frequência de termos mede foco temático, e não qualidade ou profundidade da divulgação.
- Em páginas de duas colunas, trechos de colunas diferentes podem se misturar; a numeração das páginas
  é a posição no PDF, não a impressa.
- Os números dos valores de emissões devem ser conferidos na página do PDF antes de qualquer uso.
- O checklist reflete o julgamento de uma única pesquisadora.

## Uso de inteligência artificial

A ferramenta Claude (Anthropic) foi usada como apoio à escrita e à depuração dos scripts em Python, à
proposta inicial do dicionário de termos, à conferência dos valores de emissões e à localização de
páginas de evidência do checklist. O dicionário, os valores e as notas foram revisados pela autora.

## Licença

Código sob licença MIT (arquivo `LICENSE`).
