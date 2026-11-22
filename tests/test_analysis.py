from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from analyse import segment,extract_awards,summarise,next_link


def test_topic_screen():
    assert segment('Music festival services')=='Live performance/music'
    assert segment('Audio visual hire')=='AV/sound/lighting'
    assert segment('Event management production')=='Event production'
    assert segment('Medical consumables') is None


def test_award_value_counted_once_when_multiple_suppliers():
    # Artificial unit-test fixture, NOT a reported contract award.
    rec={'ocid':'x','id':'r1','date':'2026-01-02T00:00:00Z','tag':['award'],
         'buyer':{'name':'Test Council'},'tender':{'title':'Music festival','description':'Live festival'},
         'awards':[{'id':'a1','value':{'amount':1200,'currency':'GBP'},'suppliers':[{'name':'Supplier A'},{'name':'Supplier B'}]}]}
    frame=extract_awards([rec,dict(rec,id='r2')])
    valued,segment_totals,buyers=summarise(frame)
    assert len(frame)==1
    assert valued['supplier_count'].iloc[0]==2
    assert segment_totals['award_value_gbp'].sum()==1200


def test_next_link_formats():
    assert next_link({'links':{'next':{'href':'https://example.test/p2'}}})=='https://example.test/p2'
    assert next_link({'links':{'next':'https://example.test/p3'}})=='https://example.test/p3'
