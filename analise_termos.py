#!/usr/bin/env python3
"""
Análise lexical do corpus: frequência de termos por variável (Tabela 1 do TCC).

Método (sem IA, regra 100% transparente e replicável):
  1. Lê os textos limpos de saida/limpo/*.txt (gerados por extrair_corpus.py).
  2. Normaliza o texto: minúsculas e sem acentos (preserva as posições dos caracteres).
  3. Conta, em cada documento, as ocorrências dos termos do DICIONARIO abaixo.
  4. Normaliza pelo tamanho do documento: ocorrências por 10 mil palavras.
  5. Gera tabelas (CSV), gráficos (PNG) e as concordâncias (o trecho de cada ocorrência,
     com a página), para você VALIDAR manualmente se o termo foi usado no sentido esperado.

Como ler a contagem por variável: cada trecho do texto é contado UMA vez por variável,
mesmo que dois termos do dicionário o cubram (ex.: "riscos climáticos" casa com "risco(s)"
e com "risco(s) climático(s)"). Já a tabela por termo mostra a contagem de cada termo isolado.

Uso:
  python analise_termos.py PASTA_SAIDA
Opcional: crie PASTA_SAIDA/paginas_excluir.csv (colunas: rotulo,paginas) para excluir
sumários e índices GRI/SASB, por exemplo:  Natura_RI_2025,"1-6;85-89"
"""
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# DICIONÁRIO  (EDITE AQUI)
# Regras: o texto já está em minúsculas e SEM acentos ("informações" -> "informacoes").
# Cada termo é uma expressão regular. \b marca limite de palavra.
# ---------------------------------------------------------------------------
DICIONARIO = {
    "Materialidade": {
        "materialidade": r"\bmaterialidade\b",
        "tema(s) material(is)": r"\btemas? materia(?:l|is)\b",
        "informação material": r"\binforma(?:cao|coes) materia(?:l|is)\b",
        "partes interessadas / stakeholders": r"\b(?:partes interessadas|stakeholders?)\b",
    },
    "Governança": {
        "governança": r"\bgovernanca\b",
        "conselho de administração": r"\bconselho de administracao\b",
        "comitê(s)": r"\bcomites?\b",
        "supervisão": r"\bsupervis(?:ao|ionad[oa]s?|iona)\b",
        "diretoria": r"\bdiretoria\b",
        "alta administração": r"\balta administracao\b",
    },
    "Estratégia e Modelo de Negócios": {
        "estratégia(s)": r"\bestrategi(?:a|as|co|cos|ca|cas)\b",
        "modelo(s) de negócio": r"\bmodelos? de negocios?\b",
        "cadeia(s) de valor": r"\bcadeias? de valor\b",
        "curto/médio/longo prazo": r"\b(?:curto|medio|longo) prazo\b|\bcurto, medio e longo\b",
        "transição": r"\btransicao\b",
    },
    "Riscos e Oportunidades": {
        "risco(s)": r"\briscos?\b",
        "oportunidade(s)": r"\boportunidades?\b",
        "risco(s) climático(s)": r"\briscos? climaticos?\b",
        "risco(s) físico(s)": r"\briscos? fisicos?\b",
        "risco(s) de transição": r"\briscos? de transicao\b",
        "análise de cenários / cenários climáticos": r"\b(?:analises? de cenarios?|cenarios? climaticos?)\b",
        "mitigação": r"\bmitigacao\b",
        "adaptação": r"\badaptacao\b",
        "resiliência": r"\bresiliencia\b",
    },
    "Indicadores Climáticos": {
        "escopo 1": r"\bescopo 1\b",
        "escopo 2": r"\bescopo 2\b",
        "escopo 3": r"\bescopo 3\b",
        "tCO2e": r"\bt ?co ?2? ?e\b",
        "GHG Protocol": r"\bghg protocol\b",
        "emissões": r"\bemissa?o(?:es)?\b|\bemissoes\b",
        "gases de efeito estufa / GEE": r"\bgases? de efeito estufa\b|\bgee\b",
        "inventário": r"\binventarios?\b",
        "net zero / neutralidade de carbono": r"\bnet ?zero\b|\bneutralidade (?:de )?carbono\b|\bcarbono neutro\b",
        "descarbonização": r"\bdescarboniza\w*",
    },
    "Métricas e Metas": {
        "meta(s)": r"\bmetas?\b",
        "indicador(es)": r"\bindicadores?\b",
        "métrica(s)": r"\bmetricas?\b",
        "KPI": r"\bkpis?\b",
        "ano-base / linha de base": r"\bano[- ]base\b|\blinha de base\b",
        "SBTi": r"\bsbti\b",
    },
    "Criação de Valor (RI)": {
        "criação/geração de valor": r"\b(?:criacao|geracao) de valor\b|\b(?:criar|gerar|criamos|geramos|cria|gera) valor\b|\bvalor compartilhado\b",
        "capital (financeiro, humano, natural...)": r"\bcapital (?:financeiro|manufaturado|intelectual|humano|social|natural|de relacionamento)\b|\bcapitais (?:financeiro|manufaturado|intelectual|humano|social|natural)\b",
        "seis capitais / mapa de capitais": r"\bseis capitais\b|\bmapas? de capitais\b|\bcapitais do negocio\b|\bnossos capitais\b",
        "pensamento integrado / conectividade": r"\bpensamento integrado\b|\bconectividade\b|\bvisao integrada\b",
    },
    "Informações Financeiras de Sustentabilidade": {
        "efeito(s)/impacto(s) financeiro(s)": r"\b(?:efeitos?|impactos?) financeir[oa]s?\b",
        "fluxo(s) de caixa": r"\bfluxos? de caixa\b",
        "custo de capital": r"\bcustos? de capital\b",
        "acesso a financiamento/capital": r"\bacesso (?:a|ao) (?:financiamento|capital|credito)\b",
        "demonstrações financeiras": r"\bdemonstracoes financeiras\b",
        "posição/desempenho financeiro": r"\b(?:posicao|desempenho) financeir[oa]\b",
        "preço/precificação de carbono": r"\b(?:preco|precificacao) (?:interno )?(?:de )?carbono\b",
    },
}

VARIAVEIS = list(DICIONARIO)
CONTEXTO = 80          # caracteres de cada lado nas concordâncias
MAX_CONC_POR_TERMO = 15  # amostra de concordâncias por termo e documento (0 = todas)
RE_PAGINA = re.compile(r"\n=== PÁGINA (\d+) ===\n")
RE_CODIGO_INDICE = re.compile(r"\bgri \d{1,3}-\d{1,2}\b|\b[a-z]{2}-[a-z]{2}-\d{3}[a-z]?(?:\.\d)?\b", re.I)

# cores (paleta de referência validada: slots 1 e 2) e superfície
COR_RI, COR_IFRS = "#2a78d6", "#eb6834"
SUPERFICIE, TEXTO, TEXTO_2, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"


def norm(texto):
    """minúsculas e sem acentos, mantendo o mesmo número de caracteres."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in texto).lower()


def parse_paginas(s):
    out = set()
    for parte in re.split(r"[;, ]+", s.strip()):
        if not parte:
            continue
        if "-" in parte:
            a, b = parte.split("-")
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(parte))
    return out


def ler_paginas(caminho):
    t = Path(caminho).read_text(encoding="utf-8")
    partes = RE_PAGINA.split("\n" + t)
    return {int(partes[i]): partes[i + 1] for i in range(1, len(partes), 2)}


def unir_spans(spans):
    spans = sorted(spans)
    merged = []
    for a, b in spans:
        if merged and a < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    saida = Path(sys.argv[1])
    res = saida / "resultados"
    res.mkdir(exist_ok=True)

    controle = pd.read_csv(saida / "tabela_controle.csv", encoding="utf-8-sig")
    excluir = {}
    p_exc = saida / "paginas_excluir.csv"
    if p_exc.exists():
        for r in csv.DictReader(open(p_exc, encoding="utf-8-sig")):
            if r.get("rotulo"):
                excluir[r["rotulo"]] = parse_paginas(r.get("paginas", ""))

    linhas_termo, linhas_var, conc, suspeitas = [], [], [], []
    for _, d in controle.iterrows():
        rot = d["rotulo"]
        paginas = ler_paginas(saida / "limpo" / f"{rot}.txt")
        ign = excluir.get(rot, set())
        palavras = 0
        cont_termo = defaultdict(int)
        spans_var = defaultdict(int)
        for n, texto in paginas.items():
            flat = texto.replace("\n", " ")
            # páginas candidatas a índice GRI/SASB (para você revisar; não são excluídas sozinhas)
            if len(RE_CODIGO_INDICE.findall(flat)) >= 12:
                suspeitas.append([rot, n, len(RE_CODIGO_INDICE.findall(flat)), "muitos códigos GRI/SASB (possível índice)"])
            if n in ign:
                continue
            palavras += len(flat.split())
            nt = norm(flat)
            for var, termos in DICIONARIO.items():
                todos = []
                for termo, rx in termos.items():
                    for m in re.finditer(rx, nt):
                        cont_termo[(var, termo)] += 1
                        todos.append((m.start(), m.end()))
                        conc.append((rot, n, var, termo, flat[max(0, m.start() - CONTEXTO): m.end() + CONTEXTO]))
                spans_var[var] += len(unir_spans(todos))
        for var, termos in DICIONARIO.items():
            for termo in termos:
                c = cont_termo[(var, termo)]
                linhas_termo.append([rot, d["empresa"], d["tipo"], var, termo, c, round(c / palavras * 10000, 2)])
            c = spans_var[var]
            linhas_var.append([rot, d["empresa"], d["tipo"], d["grupo"], var, c, round(c / palavras * 10000, 2), palavras])

    termo_df = pd.DataFrame(linhas_termo, columns=["rotulo", "empresa", "tipo", "variavel", "termo", "ocorrencias", "freq_10mil"])
    var_df = pd.DataFrame(linhas_var, columns=["rotulo", "empresa", "tipo", "grupo", "variavel", "ocorrencias", "freq_10mil", "palavras_analisadas"])
    termo_df.to_csv(res / "frequencia_por_termo.csv", index=False, encoding="utf-8-sig")
    var_df.to_csv(res / "frequencia_por_variavel.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(suspeitas, columns=["rotulo", "pagina", "codigos", "motivo"]).to_csv(res / "paginas_suspeitas_indice.csv", index=False, encoding="utf-8-sig")

    # concordâncias (amostra por termo e documento)
    df_c = pd.DataFrame(conc, columns=["rotulo", "pagina", "variavel", "termo", "trecho"])
    if MAX_CONC_POR_TERMO:
        df_c = df_c.groupby(["rotulo", "termo"], group_keys=False).head(MAX_CONC_POR_TERMO)
    df_c.to_csv(res / "concordancias_amostra.csv", index=False, encoding="utf-8-sig")

    # matriz documento x variável
    ordem_empresas = list(dict.fromkeys(controle["empresa"]))
    ordem_docs = sorted(controle["rotulo"], key=lambda r: (
        ordem_empresas.index(controle.loc[controle["rotulo"] == r, "empresa"].iloc[0]),
        "IFRS" in r))
    matriz = var_df.pivot(index="rotulo", columns="variavel", values="freq_10mil").loc[ordem_docs, VARIAVEIS]
    matriz.to_csv(res / "matriz_documento_x_variavel.csv", encoding="utf-8-sig")

    # comparação RI/Anual x IFRS por empresa
    var_df["lado"] = np.where(var_df["tipo"].str.contains("IFRS"), "IFRS", "RI/Anual")
    comp = var_df.pivot_table(index=["empresa", "variavel"], columns="lado", values="freq_10mil").reset_index()
    comp["diferenca_IFRS_menos_RI"] = (comp["IFRS"] - comp["RI/Anual"]).round(2)
    comp["razao_IFRS_sobre_RI"] = (comp["IFRS"] / comp["RI/Anual"].replace(0, np.nan)).round(2)
    comp["variavel"] = pd.Categorical(comp["variavel"], VARIAVEIS, ordered=True)
    comp = comp.sort_values(["empresa", "variavel"])
    comp.to_csv(res / "comparacao_RI_vs_IFRS.csv", index=False, encoding="utf-8-sig")

    graficos(matriz, ordem_docs, controle, comp, res)
    print("Pronto. Arquivos em", res)


def estilo(ax):
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRADE)
    ax.tick_params(colors=TEXTO_2, labelsize=8)
    ax.yaxis.grid(True, color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)


def graficos(matriz, ordem_docs, controle, comp, res):
    # ---- 1) mapa de calor: documento x variável (cor relativa dentro de cada variável) ----
    rotulos_leg = {r["rotulo"]: f'{r["empresa"]} - {"IFRS S1/S2" if "IFRS" in r["tipo"] else r["tipo"]}' for _, r in controle.iterrows()}
    vals = matriz.values
    rel = (vals - vals.min(axis=0)) / np.where(np.ptp(vals, axis=0) == 0, 1, np.ptp(vals, axis=0))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("azul", ["#eaf1fb", "#9cc0ee", "#2a78d6", "#14407a"])
    fig, ax = plt.subplots(figsize=(13, 5.6), facecolor=SUPERFICIE)
    ax.imshow(rel, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(VARIAVEIS)))
    ax.set_xticklabels([v.replace(" e ", " e\n", 1).replace(" (RI)", "\n(RI)").replace("Informações Financeiras de Sustentabilidade", "Inform. Financeiras\nde Sustentabilidade") for v in VARIAVEIS], fontsize=8.5, color=TEXTO)
    ax.set_yticks(range(len(ordem_docs)))
    ax.set_yticklabels([rotulos_leg[r] for r in ordem_docs], fontsize=9, color=TEXTO)
    ax.xaxis.tick_top()
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            ax.text(j, i, f"{vals[i, j]:.1f}", ha="center", va="center", fontsize=8.5,
                    color="#ffffff" if rel[i, j] > 0.55 else TEXTO)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(VARIAVEIS)), minor=True)
    ax.set_yticks(np.arange(-.5, len(ordem_docs)), minor=True)
    ax.grid(which="minor", color=SUPERFICIE, linewidth=2)
    ax.tick_params(which="both", length=0)
    fig.suptitle("Ocorrências de termos por variável, por 10 mil palavras", x=0.01, ha="left", fontsize=13, color=TEXTO, fontweight="bold")
    fig.text(0.01, 0.01, "Número = ocorrências por 10 mil palavras. A cor é relativa ao maior valor de cada variável (coluna), por isso não compara variáveis entre si.",
             fontsize=8, color=TEXTO_2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(res / "fig1_mapa_de_calor.png", dpi=170, facecolor=SUPERFICIE)
    plt.close(fig)

    # ---- 2) barras agrupadas: RI/Anual x IFRS por empresa, uma variável por painel ----
    empresas = list(dict.fromkeys(controle["empresa"]))
    fig, axs = plt.subplots(2, 4, figsize=(15, 7.4), facecolor=SUPERFICIE)
    x = np.arange(len(empresas))
    w = 0.38
    for ax, var in zip(axs.ravel(), VARIAVEIS):
        sub = comp[comp["variavel"] == var].set_index("empresa").reindex(empresas)
        ax.bar(x - w / 2 - 0.01, sub["RI/Anual"], w, color=COR_RI, label="Relato Integrado / Relatório Anual")
        ax.bar(x + w / 2 + 0.01, sub["IFRS"], w, color=COR_IFRS, label="Relatório IFRS S1/S2")
        ax.set_xticks(x)
        ax.set_xticklabels([e.replace("Lojas ", "") for e in empresas], fontsize=8, color=TEXTO_2)
        ax.set_title(var.replace(" e Modelo de Negócios", " e Modelo\nde Negócios").replace("Informações Financeiras de Sustentabilidade", "Inform. Financeiras\nde Sustentabilidade"),
                     fontsize=9.5, color=TEXTO, loc="left")
        estilo(ax)
    h, l = axs.ravel()[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper right", ncol=2, frameon=False, fontsize=9.5, labelcolor=TEXTO)
    fig.suptitle("Relato Integrado / Relatório Anual x IFRS S1/S2: ocorrências por 10 mil palavras", x=0.01, ha="left", fontsize=13, color=TEXTO, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(res / "fig2_RI_vs_IFRS_por_variavel.png", dpi=170, facecolor=SUPERFICIE)
    plt.close(fig)


if __name__ == "__main__":
    main()
