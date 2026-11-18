#!/usr/bin/env python3
"""
Extração do corpus do TCC: Relato Integrado (IIRC) x IFRS S1/S2

O que o script faz (sem IA, só extração mecânica de texto):
  1. Converte cada PDF em texto, página por página, com marcador "=== PÁGINA n ===".
  2. Gera duas versões: bruta (raw) e limpa (sem cabeçalhos/rodapés repetidos e
     sem numeração solta de página).
  3. Gera tabela_controle.csv com páginas, palavras e páginas sem texto.

Motor de extração (usa o primeiro disponível):
  - PyMuPDF (fitz)      -> recomendado no seu computador:  pip install pymupdf
  - pdftotext (poppler) -> alternativa de linha de comando
  - pdfplumber          -> alternativa em Python puro (mais lenta)

Faixas de topo e rodapé: os relatórios trazem, em todas as páginas, menus de navegação
("Governança | Gestão de Riscos e Oportunidades | Métricas e Metas ..."), cabeçalhos e
numeração. Essas palavras fazem parte do dicionário de termos e inflariam a frequência,
então o script IGNORA uma faixa no topo (MARGEM_TOPO) e uma no rodapé (MARGEM_RODAPE) de
cada página, em qualquer motor de extração. Os valores estão logo abaixo das constantes.

Uso:
  python extrair_corpus.py PASTA_DOS_PDFS PASTA_DE_SAIDA
Ajuste o dicionário DOCUMENTOS abaixo com os nomes dos seus arquivos.
"""
import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# arquivo (nome exato ou prefixo) -> (rótulo, empresa, tipo, grupo)
DOCUMENTOS = {
    "Irani_Relato_Integrado_2025.pdf": ("Irani_RI_2025", "Irani", "Relato Integrado", "A"),
    "Irani_IFRS_S1_S2_2025.pdf": ("Irani_IFRS_2025", "Irani", "IFRS S1/S2", "A"),
    "Natura_Relatorio_Integrado_2025.pdf": ("Natura_RI_2025", "Natura", "Relato Integrado", "A"),
    "Natura_IFRS_S1_S2_2025.pdf": ("Natura_IFRS_2025", "Natura", "IFRS S1/S2", "A"),
    "Renner_Relatorio_Anual_2025.pdf": ("Renner_Anual_2025", "Lojas Renner", "Relatório Anual", "A"),
    "Renner_IFRS_S1_S2_2025.pdf": ("Renner_IFRS_2025", "Lojas Renner", "IFRS S1/S2", "A"),
    "B3_Relatorio_Anual_2025.pdf": ("B3_Anual_2025", "B3", "Relatório Anual", "B"),
    "B3_IFRS_S1_S2_2025.pdf": ("B3_IFRS_2025", "B3", "IFRS S1/S2", "B"),
    "Vale_Relatorio_Anual_2025.pdf": ("Vale_Anual_2025", "Vale", "Relatório Anual", "B"),
    "Vale_IFRS_S1_S2_2025.pdf": ("Vale_IFRS_2025", "Vale", "IFRS S1/S2", "B"),
}

LIMIAR_REPETICAO = 0.30   # linha curta que aparece em >=30% das páginas = cabeçalho/rodapé
MAX_CHARS_CABECALHO = 160
MARGEM_TOPO = 0.10        # fração da altura da página ignorada no topo (menus, cabeçalhos)
MARGEM_RODAPE = 0.06      # fração da altura da página ignorada no rodapé (numeração, links)
MIN_CHARS_PAGINA = 20     # abaixo disso a página é marcada como "sem texto"


def casar(nome_arquivo):
    """Associa o arquivo ao dicionário pelo final do nome (os uploads têm prefixo)."""
    for chave, info in DOCUMENTOS.items():
        if nome_arquivo.endswith(chave) or nome_arquivo == chave:
            return info
    return None


def importar_pymupdf():
    try:
        import pymupdf as fitz  # nome atual
    except ImportError:
        import fitz  # nome antigo (gera aviso de "deprecated" nas versões novas)
    return fitz


def paginas_fitz(pdf):
    fitz = importar_pymupdf()
    paginas = []
    with fitz.open(pdf) as doc:
        for p in doc:
            r = p.rect
            area = fitz.Rect(r.x0, r.y0 + r.height * MARGEM_TOPO, r.x1, r.y1 - r.height * MARGEM_RODAPE)
            # clip = só o corpo da página; sort=True ordena os blocos na ordem de leitura
            paginas.append(p.get_text("text", clip=area, sort=True))
    return paginas


def tamanhos_paginas(pdf):
    """Largura e altura (pt) de cada página, via pdfinfo (vem junto com o poppler)."""
    saida = subprocess.run(["pdfinfo", "-f", "1", "-l", "100000", str(pdf)],
                           capture_output=True, text=True, check=True).stdout
    return {int(m.group(1)): (float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r"Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+)", saida)}


def paginas_pdftotext(pdf):
    # sem -layout: o poppler respeita melhor a ordem de leitura em colunas
    tam = tamanhos_paginas(pdf)
    paginas = []
    for n in sorted(tam):
        w, h = tam[n]
        cmd = ["pdftotext", "-f", str(n), "-l", str(n),
               "-x", "0", "-y", str(int(h * MARGEM_TOPO)),
               "-W", str(int(w)), "-H", str(int(h * (1 - MARGEM_TOPO - MARGEM_RODAPE))),
               str(pdf), "-"]
        paginas.append(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    return paginas


def paginas_pdfplumber(pdf):
    import pdfplumber
    paginas = []
    with pdfplumber.open(pdf) as doc:
        for p in doc.pages:
            w, h = float(p.width), float(p.height)
            corpo = p.crop((0, h * MARGEM_TOPO, w, h * (1 - MARGEM_RODAPE)))
            paginas.append(corpo.extract_text() or "")
    return paginas


def extrair_paginas(pdf):
    try:
        importar_pymupdf()
        return "PyMuPDF", paginas_fitz(pdf)
    except ImportError:
        pass
    try:
        return "pdftotext", paginas_pdftotext(pdf)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return "pdfplumber", paginas_pdfplumber(pdf)


def normalizar(linha):
    return re.sub(r"\s+", " ", linha).strip()


def limpar(paginas):
    """Remove linhas curtas repetidas em muitas páginas e números de página soltos."""
    n = len(paginas)
    contagem = Counter()
    for texto in paginas:
        vistas = {normalizar(l) for l in texto.splitlines() if l.strip()}
        contagem.update(l for l in vistas if len(l) <= MAX_CHARS_CABECALHO)
    repetidas = {l for l, c in contagem.items() if n >= 10 and c / n >= LIMIAR_REPETICAO}
    limpas = []
    for texto in paginas:
        linhas = []
        for l in texto.splitlines():
            nl = normalizar(l)
            if not nl or nl in repetidas or re.fullmatch(r"\d{1,3}", nl):
                continue
            linhas.append(nl)
        limpas.append("\n".join(linhas))
    return limpas, repetidas


def gravar(caminho, paginas):
    with open(caminho, "w", encoding="utf-8") as f:
        for i, t in enumerate(paginas, start=1):
            f.write(f"\n=== PÁGINA {i} ===\n{t.strip()}\n")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pasta_pdfs, saida = Path(sys.argv[1]), Path(sys.argv[2])
    (saida / "raw").mkdir(parents=True, exist_ok=True)
    (saida / "limpo").mkdir(exist_ok=True)

    linhas_controle = []
    for pdf in sorted(pasta_pdfs.glob("*.pdf")):
        info = casar(pdf.name)
        if info is None:
            print(f"[ignorado] {pdf.name} (não está em DOCUMENTOS; ex.: carta de asseguração)")
            continue
        rotulo, empresa, tipo, grupo = info
        motor, paginas = extrair_paginas(pdf)
        limpas, repetidas = limpar(paginas)
        gravar(saida / "raw" / f"{rotulo}.txt", paginas)
        gravar(saida / "limpo" / f"{rotulo}.txt", limpas)
        palavras = sum(len(t.split()) for t in limpas)
        sem_texto = [i for i, t in enumerate(paginas, 1) if len(t.strip()) < MIN_CHARS_PAGINA]
        # páginas candidatas a sumário: início do documento com "sumário"/"índice"
        sumario = [i for i, t in enumerate(paginas[:10], 1) if re.search(r"sum[áa]rio|[íi]ndice", t, re.I)]
        linhas_controle.append({
            "rotulo": rotulo, "empresa": empresa, "tipo": tipo, "grupo": grupo,
            "arquivo": pdf.name, "motor": motor, "paginas": len(paginas),
            "palavras_limpo": palavras, "linhas_removidas_repetidas": len(repetidas),
            "margem_topo": MARGEM_TOPO, "margem_rodape": MARGEM_RODAPE,
            "paginas_sem_texto": " ".join(map(str, sem_texto)),
            "paginas_possivel_sumario": " ".join(map(str, sumario)),
        })
        print(f"[ok] {rotulo}: {len(paginas)} páginas, {palavras} palavras ({motor})")

    with open(saida / "tabela_controle.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_controle[0].keys()))
        w.writeheader()
        w.writerows(linhas_controle)


if __name__ == "__main__":
    main()
