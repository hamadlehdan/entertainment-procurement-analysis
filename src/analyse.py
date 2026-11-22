"""Real UK Contracts Finder OCDS awards relevant to entertainment/AV services.

A bounded public-source query; no private quotations or invented suppliers.
"""
import argparse
from datetime import date
from pathlib import Path
import re
import sys
from urllib.parse import urljoin
import pandas as pd
import plotly.express as px
import requests
from reporting import write_outputs

ROOT=Path(__file__).resolve().parents[1]
API='https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search'
# The following is a transparent keyword-defined SCREEN, not an industry-wide taxonomy.
SEGMENTS={
    'Live performance/music':r'\b(music|musician|festival|performer|performance|concert|theatre|theater)\b',
    'AV/sound/lighting':r'\b(audio[- ]?visual|audiovisual|sound system|sound production|stage lighting|lighting design|projection|public address system)\b',
    'Event production':r'\b(event management|event production|event services|live event|production services|stage hire)\b',
}


def segment(text):
    """Returns first matching segment by documented, auditable priority."""
    normalized=str(text or '').lower()
    for category,pattern in SEGMENTS.items():
        if re.search(pattern,normalized):return category
    return None


def next_link(payload):
    links=payload.get('links') or {}
    if isinstance(links,dict):
        value=links.get('next') or links.get('Next')
        if isinstance(value,dict):return value.get('href') or value.get('url')
        if isinstance(value,str):return value
    if isinstance(links,list):
        for item in links:
            if item.get('rel')=='next':return item.get('href') or item.get('url')
    return None


def get_releases(start,end,max_pages=400):
    """Read a fixed publication date window; stop with error if pagination is incomplete."""
    if date.fromisoformat(start)>date.fromisoformat(end):raise ValueError('from-date is after to-date')
    params={'publishedFrom':start+'T00:00:00','publishedTo':end+'T23:59:59','stages':'award','limit':100}
    session=requests.Session();session.headers.update({'User-Agent':'public-procurement-analytics-portfolio/1.0','Accept':'application/json'})
    url=API;seen_urls=set();releases=[]
    for page in range(max_pages):
        if url in seen_urls:raise RuntimeError('API pagination loop detected; refusing incomplete results')
        seen_urls.add(url)
        response=session.get(url,params=(params if page==0 else None),timeout=45)
        response.raise_for_status();data=response.json()
        batch=data.get('releases')
        if not isinstance(batch,list):raise RuntimeError('Response lacks expected OCDS releases array')
        releases.extend(batch)
        next_url=next_link(data)
        if not next_url:return releases,{'pages':page+1,'releases':len(releases),'publication_start':start,'publication_end':end}
        url=urljoin(API,next_url)
        if not url.startswith('https://www.contractsfinder.service.gov.uk/'):
            raise RuntimeError(f'Unexpected external pagination link {url}')
        params=None
    raise RuntimeError(f'Incomplete API window: pagination exceeded --max-pages={max_pages}; use a shorter period or raise the cap')


def extract_awards(releases):
    """One row per (ocid, award id); do NOT duplicate value by number of suppliers."""
    rows=[]
    for release in releases:
        tender=release.get('tender') or {}
        title=tender.get('title') or ''
        description=tender.get('description') or ''
        category=segment(title+' '+description)
        if not category:continue
        if 'award' not in ' '.join(release.get('tag') or []).lower():continue
        for award in release.get('awards') or []:
            amount=(award.get('value') or {}).get('amount')
            currency=(award.get('value') or {}).get('currency')
            suppliers=sorted({str(s.get('name','')).strip() for s in award.get('suppliers') or [] if s.get('name')})
            documents=award.get('documents') or []
            notice_url=next((d.get('url') for d in documents if 'contractsfinder.service.gov.uk/Notice/' in str(d.get('url'))),None)
            rows.append({'ocid':release.get('ocid'),'award_id':award.get('id'),'release_date':release.get('date'),'award_date':award.get('date'),'title':title,'buyer':(release.get('buyer') or {}).get('name'),'segment':category,'status':award.get('status'),'amount_gbp':amount if currency=='GBP' else None,'award_currency':currency,'suppliers':'; '.join(suppliers),'supplier_count':len(suppliers),'notice_url':notice_url,'release_id':release.get('id')})
    raw=pd.DataFrame(rows)
    if raw.empty:raise ValueError('No relevant awards matched; consider widening the fixed publication date window, not fabricating results')
    raw['release_date']=pd.to_datetime(raw['release_date'],utc=True,errors='coerce')
    raw['amount_gbp']=pd.to_numeric(raw['amount_gbp'],errors='coerce')
    raw=raw.sort_values('release_date').drop_duplicates(['ocid','award_id'],keep='last')
    # Exclude cancelled awards: visible in audit CSV elsewhere if required.
    return raw.reset_index(drop=True)


def summarise(df):
    valid=df.loc[df['amount_gbp'].notna() & df['amount_gbp'].ge(0)].copy()
    if valid.empty:raise ValueError('No GBP-valued awards found; cannot compute £ charts')
    by_segment=valid.groupby('segment',as_index=False).agg(awards=('award_id','size'),award_value_gbp=('amount_gbp','sum'),median_award_gbp=('amount_gbp','median'))
    by_buyer=valid.groupby('buyer',dropna=False,as_index=False).agg(awards=('award_id','size'),award_value_gbp=('amount_gbp','sum')).sort_values('award_value_gbp',ascending=False)
    return valid,by_segment,by_buyer


def analyze(df,qa,out):
    values,segments,buyers=summarise(df)
    total=float(values['amount_gbp'].sum())
    multi=int(values['supplier_count'].gt(1).sum())
    kpis={'Screened award records':f'{len(df):,}','GBP-valued awards':f'{len(values):,}','Published GBP award values':f'£{total:,.0f}','Multi-supplier GBP awards':str(multi)}
    figures=[('Published award value by segment',px.bar(segments,x='segment',y='award_value_gbp',labels={'award_value_gbp':'Published GBP awards (not actual spend)'})),('Top buyers by published award value',px.bar(buyers.head(15).sort_values('award_value_gbp'),x='award_value_gbp',y='buyer',orientation='h')),('Distribution of individual GBP award values',px.histogram(values,x='amount_gbp',nbins=min(25,max(5,len(values))),labels={'amount_gbp':'Published award value (GBP)'}))]
    sample=values.sort_values('amount_gbp',ascending=False).head(20)[['title','buyer','segment','amount_gbp','suppliers','notice_url']]
    top=buyers.iloc[0]
    findings=f'''# Entertainment and audiovisual procurement | UK public awards\n\n**Publication window:** {qa['publication_start']} to {qa['publication_end']}; **Source:** [UK Contracts Finder OCDS](https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search), Cabinet Office.\n\n## Key observations (within the keyword-defined sample only)\n- Retained **{len(df):,}** distinct award IDs after screening and deduplication across **{qa['releases']:,}** source releases ({qa['pages']} API pages).\n- **{len(values):,}** retained award records have a nonnegative GBP amount. Their **published award values total £{total:,.0f}**. This is *not* actual procurement expenditure or achieved savings.\n- The buyer with the highest sum in this specific sample is **{top['buyer']}** at **£{top['award_value_gbp']:,.0f}**.\n- **{multi:,}** GBP-valued awards list more than one supplier; values are counted **once per award**, not once per supplier.\n\n## Practical procurement interpretation\nThe data shows where public buyers publish awards for a narrow subset of music, live-event and audiovisual services. Use award size and buyer patterns as context for a supplier-market mapping exercise; validate exact service scope, specifications, service quality, warranty and deliverables before comparing supplier quotes.\n\n## Limitations\n- Keyword screening produces false positives and misses some relevant awards; this is **not** an exhaustive entertainment market total.\n- Dates reflect *publication*, not necessarily start or payment dates. Contract notices can be amended or duplicated in source releases.\n- Award value is **not** an invoice, negotiated fee, realised spend, cost-saving figure or profit; no actual quote comparison is possible from this dataset.\n- Non-GBP or missing-value records are not included in pound totals. No FX conversion is made.\n- Supplier concentration cannot be reliably inferred by naively splitting multi-supplier award values.\n'''
    out=Path(out)
    write_outputs(out,'Entertainment procurement | Public UK awards',f"Official Contracts Finder · Published {qa['publication_start']} to {qa['publication_end']}",kpis,figures,[('Awards by service segment',segments.round(2)),('Largest buyer award totals',buyers.head(30).round(2)),('Largest awards with source links',sample)],findings)
    df.to_csv(out/'screened_awards.csv',index=False)
    pd.DataFrame([{**qa,'keyword_matches':len(df),'gbp_awards':len(values),'missing_or_non_gbp':len(df)-len(values)}]).to_csv(out/'data_quality.csv',index=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--from-date',default='2026-01-01')
    p.add_argument('--to-date',default='2026-01-31')
    p.add_argument('--max-pages',type=int,default=400)
    p.add_argument('--out',default=str(ROOT/'outputs'))
    a=p.parse_args()
    try:
        releases,qa=get_releases(a.from_date,a.to_date,a.max_pages)
        awards=extract_awards(releases)
        analyze(awards,qa,a.out)
    except (requests.RequestException,ValueError,RuntimeError) as exc:sys.exit(f'Could not produce a verified complete analysis: {exc}')
    print('Wrote outputs to',a.out)

if __name__=='__main__':main()
