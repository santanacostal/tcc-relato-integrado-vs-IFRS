# Relato Integrado × IFRS S1/S2: scripts, dicionário e checklist

Este repositório reúne o material complementar do Trabalho de Conclusão de Curso "Comparação entre o Relato Integrado e as Informações Financeiras Relacionadas à Sustentabilidade: uma análise das abordagens IIRC e IFRS S1/S2" (Ciências Contábeis, FEA/USP, 2026).

O estudo compara dez documentos do exercício de 2025 (o Relato Integrado ou relatório anual e o relatório IFRS S1/S2 de cinco companhias: Irani, Natura, Lojas Renner, B3 e Vale) por frequência de termos, emissões de gases de efeito estufa e checklist de divulgação.

## 🚀 Como Reproduzir (Rápido)

1. Tenha o Python 3 instalado e, na pasta do repositório, instale as dependências:
   `pip install -r requirements.txt`
2. Baixe os dez PDFs dos relatórios nos sites de relações com investidores das empresas e coloque-os em uma pasta (por exemplo, `pdfs`). Ajuste os nomes dos arquivos no dicionário `DOCUMENTOS` de `extrair_corpus_v2.py`.
3. Extraia o texto: `python extrair_corpus_v2.py pdfs saida`
4. Extraia as tabelas de emissões: `python tabelas_emissoes.py pdfs saida`
5. Crie `saida/paginas_excluir.csv` (colunas `rotulo,paginas`) com os sumários e índices GRI/SASB a excluir da contagem.
6. Gere as frequências e os gráficos: `python analise_termos.py saida`

> Os PDFs não são redistribuídos aqui. Eles são públicos e as referências completas estão no trabalho.

## O que acontece durante a execução?

1. **Extração:** cada PDF é convertido em texto, página a página, ignorando menus, cabeçalhos e rodapés (topo 10% e rodapé 6% da página, e linhas repetidas em 30% ou mais das páginas).
2. **Tabelas de emissões:** os Escopos 1, 2 e 3 são extraídos dos relatórios IFRS. Os valores usados no trabalho foram conferidos manualmente contra a página de origem.
3. **Análise:** os 51 termos do dicionário são contados por variável e normalizados por 10 mil palavras. O script gera as tabelas de frequência, a razão IFRS ÷ RI/anual e os gráficos.

## 📊 Resultados e Análise

Os resultados gerados na execução do trabalho ficam em `saida/`:

- `saida/resultados/`: tabelas de frequência (`frequencia_por_variavel.csv`, `frequencia_por_termo.csv`, `matriz_documento_x_variavel.csv`, `comparacao_RI_vs_IFRS.csv`) e as figuras (`fig1_mapa_de_calor.png`, `fig2_RI_vs_IFRS_por_variavel.png`).
- `saida/tabelas/`: tabelas de emissões extraídas dos relatórios IFRS, uma por página de origem.

O checklist de divulgação (`Checklist_divulgacao_TCC.xlsx`) traz notas de 0 a 2 por variável e documento, com a página do PDF e o trecho que sustenta cada nota.

## 📂 Estrutura do Projeto

```
.
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── extrair_corpus_v2.py          # PDF -> texto, página a página
├── tabelas_emissoes.py           # tabelas de emissões (Escopos 1, 2 e 3)
├── analise_termos.py             # frequências, razão IFRS/RI e gráficos
├── dicionario_termos.csv         # 51 expressões por variável
├── Checklist_divulgacao_TCC.xlsx # checklist 0/1/2 com evidências
├── tabela_controle.csv           # controle dos documentos analisados
└── saida/
    ├── resultados/               # tabelas de frequência e figuras
    └── tabelas/                  # tabelas de emissões extraídas
```

## 🛠️ Tecnologias Utilizadas

- Python 3
- PyMuPDF e pdfplumber (extração de texto)
- Camelot (extração de tabelas)
- pandas e matplotlib (tabelas e gráficos)
- Expressões regulares (módulo `re`) para a contagem de termos

## ⚠️ Limitações

- A frequência de termos mede foco temático, e não qualidade ou profundidade da divulgação.
- Em páginas de duas colunas, trechos de colunas diferentes podem se misturar; a numeração das páginas é a posição no PDF, não a impressa.
- Os valores de emissões devem ser conferidos na página do PDF antes de qualquer uso.
- O checklist reflete o julgamento de uma única pesquisadora.

## 🤖 Uso de inteligência artificial

A ferramenta Claude (Anthropic) foi usada como apoio à escrita e à depuração dos scripts em Python, à proposta inicial do dicionário de termos, à conferência dos valores de emissões e à localização de páginas de evidência do checklist. As contagens são feitas apenas por expressões regulares, sem etapa de inteligência artificial na execução. O dicionário, os valores e as notas foram revisados pela autora.

## 📄 Licença

Código sob licença MIT (arquivo `LICENSE`).
