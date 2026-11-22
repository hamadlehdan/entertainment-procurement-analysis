"""Small dependency-light HTML and text reporting helpers."""
from html import escape
from pathlib import Path
import pandas as pd
from plotly.io import to_html


def write_outputs(folder, title, subtitle, kpis, figures, tables, findings):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    styles = """<style>
    :root{font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;color:#e7eef8;background:#0c1322}
    body{margin:auto;padding:36px;max-width:1200px}h1{font-size:31px;margin:0 0 8px}p{color:#acbad1}
    .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:26px 0}
    .kpi{background:#17253b;border:1px solid #30405b;padding:22px;border-radius:12px}
    .kpi small{color:#a9bad1;display:block}.kpi strong{font-size:25px;margin-top:8px;display:block}
    section{background:#131f31;border:1px solid #30405b;padding:14px;margin:18px 0;border-radius:14px}
    table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:8px;border-bottom:1px solid #32405a}
    .table-wrap{overflow-x:auto}footer{font-size:12px;color:#9daec7;padding:18px 0}
    </style>"""
    kpi_markup = ''.join('<div class="kpi"><small>'+escape(str(k))+'</small><strong>'+escape(str(v))+'</strong></div>' for k,v in kpis.items())
    figure_markup = ''
    for index, (label, fig) in enumerate(figures):
        fig.update_layout(template="plotly_dark",paper_bgcolor="#131f31",plot_bgcolor="#131f31",font=dict(color="#e7eef8"),margin=dict(l=38,r=22,t=62,b=40))
        figure_markup += '<section><h2>'+escape(label)+'</h2>'+to_html(fig,full_html=False,include_plotlyjs=(True if index==0 else False))+'</section>'
    table_markup=''
    for name, df in tables:
        table_markup += '<section><h2>'+escape(name)+'</h2><div class="table-wrap">'+df.to_html(index=False,escape=True,border=0,classes='data')+'</div></section>'
    page=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>{styles}</head><body><h1>{escape(title)}</h1><p>{escape(subtitle)}</p><div class="kpis">{kpi_markup}</div>{figure_markup}{table_markup}<footer>Data is sourced as described in the project SOURCE_NOTES.md; this is a reproducible analysis of public third-party records, not internal employer information.</footer></body></html>'
    (folder/'dashboard.html').write_text(page,encoding='utf-8')
    (folder/'findings.md').write_text(findings,encoding='utf-8')
    for name, df in tables:
        filename=name.lower().replace(' ','_').replace('/','_')+'.csv'
        df.to_csv(folder/filename,index=False)
