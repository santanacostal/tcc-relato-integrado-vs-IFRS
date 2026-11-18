#!/usr/bin/env python3
"""
Extrai tabelas de emissões de gases de efeito estufa (Escopos 1, 2 e 3) dos PDFs.

Estratégia:
  1. Localiza as páginas que mencionam Escopo 1 e Escopo 2 (texto já extraído em
     saida/raw/*.txt, com marcadores "=== PÁGINA n ===").
  2. Tenta extrair as tabelas dessas páginas com pdfplumber.
  3. Se o pdfplumber não achar tabela, tenta o Camelot (flavor "stream").
  4. Salva cada tabela em CSV e gera tabelas/indice_tabelas.csv.

IMPORTANTE: os números ficam como TEXTO, exatamente como no PDF (ex.: "1.234,5").
Nada é convertido, arredondado ou somado. Confira cada CSV contra a página do PDF
antes de usar os valores no TCC.

Uso:
  python tabelas_emissoes.py PASTA_DOS_PDFS PASTA_DE_SAIDA
(PASTA_DE_SAIDA é a mesma usada em extrair_corpus.py)
"""
import csv
import re
import sys
from pathlib import Path

# Mesmos rótulos de extrair_corpus.py; só os relatórios IFRS têm inventário de GEE
IFRS = {
    "Irani_IFRS_S1_S2_2025.pdf": "Irani_IFRS_2025",
    "Natura_IFRS_S1_S2_2025.pdf": "Natura_IFRS_2025",
    "Renner_IFRS_S1_S2_2025.pdf": "Renner_IFRS_2025",
    "B3_IFRS_S1_S2_2025.pdf": "B3_IFRS_2025",
    "Vale_IFRS_S1_S2_2025.pdf": "Vale_IFRS_2025",
}
RE_ESC1 = re.compile(r"escopo\s*1", re.I)
RE_ESC2 = re.compile(r"escopo\s*2", re.I)
RE_UNID = re.compile(r"t\s*CO\s*[2₂]\s*e|tCO2|CO\s*[2₂]\s*e|toneladas", re.I)


def paginas_candidatas(txt_raw):
    texto = Path(txt_raw).read_text(encoding="utf-8")
    partes = re.split(r"\n=== PÁGINA (\d+) ===\n", texto)
    # partes = ['', '1', texto1, '2', texto2, ...]
    achadas = []
    for i in range(1, len(partes), 2):
        n, t = int(partes[i]), partes[i + 1]
        if RE_ESC1.search(t) and RE_ESC2.search(t) and RE_UNID.search(t):
            achadas.append(n)
    return achadas


def limpa_celula(c):
    return re.sub(r"\s+", " ", c).strip() if c else ""


def com_pdfplumber(pdf, pagina):
    import pdfplumber
    tabelas = []
    with pdfplumber.open(pdf) as doc:
        page = doc.pages[pagina - 1]
        for tb in page.extract_tables():
            linhas = [[limpa_celula(c) for c in lin] for lin in tb]
            # descarta tabelas triviais (1 linha ou 1 coluna)
            if len(linhas) >= 2 and max(len(l) for l in linhas) >= 2:
                tabelas.append(linhas)
    return tabelas


def com_camelot(pdf, pagina):
    try:
        import camelot
        achadas = camelot.read_pdf(str(pdf), pages=str(pagina), flavor="stream")
    except Exception as e:  # camelot pode falhar por dependências (ghostscript etc.)
        print(f"   camelot indisponível/erro na p.{pagina}: {type(e).__name__}")
        return []
    saida = []
    for t in achadas:
        linhas = [[limpa_celula(c) for c in lin] for lin in t.df.values.tolist()]
        if len(linhas) >= 2 and max(len(l) for l in linhas) >= 2:
            saida.append(linhas)
    return saida


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pasta_pdfs, saida = Path(sys.argv[1]), Path(sys.argv[2])
    destino = saida / "tabelas"
    destino.mkdir(exist_ok=True)
    indice = []
    for pdf in sorted(pasta_pdfs.glob("*.pdf")):
        rotulo = next((r for k, r in IFRS.items() if pdf.name.endswith(k)), None)
        if rotulo is None:
            continue
        paginas = paginas_candidatas(saida / "raw" / f"{rotulo}.txt")
        print(f"{rotulo}: páginas candidatas {paginas}")
        for p in paginas:
            tabelas, motor = com_pdfplumber(pdf, p), "pdfplumber"
            if not tabelas:
                tabelas, motor = com_camelot(pdf, p), "camelot-stream"
            if not tabelas:
                indice.append([rotulo, p, 0, "nenhuma", "", "conferir à mão"])
                continue
            for k, linhas in enumerate(tabelas, start=1):
                nome = f"{rotulo}_p{p:03d}_t{k}.csv"
                with open(destino / nome, "w", newline="", encoding="utf-8-sig") as f:
                    csv.writer(f).writerows(linhas)
                indice.append([rotulo, p, k, motor, nome, f"{len(linhas)} linhas x {max(len(l) for l in linhas)} colunas"])
    with open(destino / "indice_tabelas.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["rotulo", "pagina_pdf", "tabela", "motor", "arquivo", "observacao"])
        w.writerows(indice)
    print(f"{len(indice)} registros em {destino/'indice_tabelas.csv'}")


if __name__ == "__main__":
    main()
