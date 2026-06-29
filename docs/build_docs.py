#!/usr/bin/env python3
"""Build the shareable PDFs from their markdown sources.

Pipeline per doc: Markdown -> styled HTML -> PDF (headless Edge --print-to-pdf).
Missing screenshots are replaced with a tidy "pending" placeholder so the PDFs
stay clean until real captures are dropped into docs/screenshots/.

Builds:
  HOUSEKEEPING_APP_SUPPORT.md   -> HOUSEKEEPING_APP_SUPPORT.pdf   (technical/support)
  HOUSEKEEPING_USER_GUIDE.md    -> HOUSEKEEPING_USER_GUIDE.pdf    (staff-facing)

Usage:  python docs/build_docs.py
Re-run whenever either markdown source changes.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = ["HOUSEKEEPING_APP_SUPPORT.md", "HOUSEKEEPING_USER_GUIDE.md"]

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color:#1a2a2f;
       font-size: 10.5pt; line-height: 1.5; }
h1 { color:#1a4a5c; border-bottom:3px solid #c8963e; padding-bottom:6px; font-size:22pt; }
h2 { color:#1a4a5c; border-bottom:1px solid #d9cfc4; padding-bottom:4px; margin-top:1.5em; font-size:15pt; }
h3 { color:#2a7a8a; font-size:12pt; margin-top:1.2em; }
table { border-collapse:collapse; width:100%; font-size:9.5pt; margin:8px 0; }
th,td { border:1px solid #d9cfc4; padding:6px 8px; text-align:left; vertical-align:top; }
th { background:#1a4a5c; color:#fff; }
tr:nth-child(even) td { background:#faf7f2; }
code { background:#f5ede0; padding:1px 4px; border-radius:3px; font-size:9pt; }
pre { background:#faf7f2; border:1px solid #d9cfc4; padding:10px; border-radius:6px; }
pre code { background:none; padding:0; }
blockquote { border-left:4px solid #c8963e; margin:10px 0; padding:6px 14px; background:#faf7f2; color:#33474d; }
img { max-width:100%; height:auto; border:1px solid #d9cfc4; border-radius:6px; }
img[src$=".svg"] { border:none; }
a { color:#2a7a8a; text-decoration:none; }
.screenshot-pending { display:block; border:2px dashed #c8963e; background:#faf7f2; color:#6b8a91;
       padding:22px; text-align:center; border-radius:8px; font-style:italic; }
h2 { page-break-after: avoid; }
table, pre, img { page-break-inside: avoid; }
"""


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    sys.exit("Could not find msedge.exe. Edit EDGE_CANDIDATES in this script.")


def replace_missing_images(html):
    def repl(m):
        src = m.group(1)
        if src.lower().startswith(("http://", "https://")):
            return m.group(0)
        if os.path.exists(os.path.join(ROOT, src.replace("/", os.sep))):
            return m.group(0)
        return '<span class="screenshot-pending">[ image pending: %s ]</span>' % src
    return re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', repl, html)


def build(md_name, edge):
    import markdown
    md_path = os.path.join(ROOT, md_name)
    pdf_path = os.path.join(ROOT, os.path.splitext(md_name)[0] + ".pdf")
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists"])
    body = replace_missing_images(body)
    html = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>%s</style></head><body>%s</body></html>" % (CSS, body))
    tmp = os.path.join(ROOT, "_doc_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        url = "file:///" + tmp.replace("\\", "/")
        subprocess.run([edge, "--headless=new", "--disable-gpu",
                        "--no-pdf-header-footer", "--print-to-pdf=" + pdf_path, url],
                       check=True, timeout=120)
        print("Wrote", pdf_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    edge = find_edge()
    for md in DOCS:
        build(md, edge)


if __name__ == "__main__":
    main()
