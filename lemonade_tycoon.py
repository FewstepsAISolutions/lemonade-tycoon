"""Lemonade Tycoon — run with Python 3, no external packages."""
import random, json, math
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from pathlib import Path
from html import escape
SAVE=Path(__file__).with_name('lemonade_save.json')
WEATHER={'Heatwave':1.8,'Sunny':1.4,'Warm':1.2,'Cloudy':1,'Windy':.8,'Light rain':.6,'Heavy rain':.3}
LOC={'Park':(250,10),'High street':(400,20),'Station':(600,35),'Residential':(100,0)}
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
DEFAULT_STAFF=[
    dict(name='Alex',trait='Organised',capacity=50,daily_wage=10),
    dict(name='Sam',trait='Friendly',capacity=50,daily_wage=10),
]
# Unordered trait pairs: the same pairing always produces the same effect.
TRAIT_PAIRS={
    tuple(sorted(('Organised','Friendly'))):1.1,
    tuple(sorted(('Organised','Organised'))):1.0,
    tuple(sorted(('Friendly','Friendly'))):1.0,
}
def team_stats(staff):
    base=sum(person['capacity'] for person in staff)
    multiplier=TRAIT_PAIRS.get(tuple(sorted(person['trait'] for person in staff)),1.0)
    return base,multiplier,math.floor(base*multiplier),round(sum(person['daily_wage'] for person in staff),2)
def load_game():
    saved=json.loads(SAVE.read_text())
    saved.setdefault('staff',deepcopy(DEFAULT_STAFF))
    return saved
def fresh(): return dict(day=1,cash=100,weather='Sunny',reputation=75,history=[],staff=deepcopy(DEFAULT_STAFF))
state=fresh()
def simulate(s,location,price,stock,quality):
    base_capacity,teamwork,capacity,wages=team_stats(s['staff'])
    fee=LOC[location][1]; unit=.4 if quality=='Standard' else .75
    cost=round(fee+unit*stock+wages,2)
    if cost>s['cash']: raise ValueError('Not enough cash for this plan.')
    weekend=(s['day']-1)%7>=5
    day_factor=(1.4 if location=='Park' else .65 if location=='Station' else 1.1) if weekend else 1
    footfall=round(LOC[location][0]*day_factor*random.uniform(.9,1.1))
    conversion=min(1,.25*WEATHER[s['weather']]*(4/price)**1.2*(1.2 if quality=='Premium' else 1)*(0.5+s['reputation']/150))
    demand=round(footfall*conversion)
    sold=min(stock,demand,capacity); revenue=round(sold*price,2); profit=round(revenue-cost,2)
    satisfaction=min(100,max(0,75+(10 if quality=='Premium' else 0)-25*(demand-sold)/max(1,demand)))
    s['cash']=round(s['cash']+profit,2); s['reputation']=round((s['reputation']+satisfaction)/2,1)
    s['history'].append(dict(day=s['day'],weather=s['weather'],location=location,footfall=footfall,demand=demand,sold=sold,waste=stock-sold,revenue=revenue,cost=cost,profit=profit,wages=wages,base_capacity=base_capacity,teamwork_multiplier=teamwork,capacity=capacity,satisfaction=round(satisfaction)))
    s['day']+=1; s['weather']=random.choices(list(WEATHER),[5,25,20,20,10,15,5])[0]
    return s

def page(error=''):
    s=state; last=s['history'][-1] if s['history'] else None
    base_capacity,teamwork,capacity,wages=team_stats(s['staff'])
    team='<section><h2>Your team</h2>'+''.join(f"<p>{escape(person['name'])} · {escape(person['trait'])} · {person['capacity']} cups/day · £{person['daily_wage']:.2f}/day</p>" for person in s['staff'])+f'<p>Teamwork: {base_capacity} × {teamwork:g} = <b>{capacity} cups/day</b> ({(teamwork-1)*100:+.0f}%). Daily wages: £{wages:.2f}.</p></section>'
    options=lambda vals: ''.join(f'<option>{escape(v)}</option>' for v in vals)
    result='' if not last else '<h2>Last trading day</h2><div class="grid">'+''.join(f'<div>{k.title()}<strong>{"£"+format(v,".2f") if k in ("revenue","cost","profit","wages") else escape(str(v))}</strong></div>' for k,v in last.items())+'</div>'
    form=f'''<form method="post"><label>Location<select name="location">{options(LOC)}</select></label><label>Price per cup (£)<input name="price" type="number" min=".5" max="20" step=".1" value="4" required></label><label>Cups prepared<input name="stock" type="number" min="0" max="1000" value="30" required></label><label>Drink quality<select name="quality">{options(['Standard','Premium'])}</select></label><p>Standard: £0.40/cup · Premium: £0.75/cup · Staff wages: £{wages:.2f}/day</p><button name="action" value="trade">Start trading day</button></form>''' if s['day']<=30 else '<h2>Campaign complete</h2>'
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lemonade Tycoon</title><style>body{{font:16px system-ui;background:#f6f4df;color:#253e2c;max-width:680px;margin:auto;padding:20px}}section,form{{background:white;padding:18px;border-radius:14px;margin:14px 0}}label{{display:block;margin:12px 0}}input,select,button{{font:inherit;padding:10px;border-radius:8px;border:1px solid #b4c3a4}}input,select{{display:block;width:100%;box-sizing:border-box;margin-top:5px}}button{{background:#f5d34c;cursor:pointer;font-weight:bold;margin:4px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.grid div{{background:white;padding:12px;border-radius:10px}}strong{{display:block;font-size:23px}}.error{{color:#a22}}</style><h1>🍋 Lemonade Tycoon</h1><p>Day {min(s['day'],30)} / 30 · {DAYS[(min(s['day'],30)-1)%7]} · {s['weather']}</p><div class="grid"><div>Cash<strong>£{s['cash']:.2f}</strong></div><div>Reputation<strong>{s['reputation']}%</strong></div></div><p class="error">{escape(error)}</p>{team}{form}{result}<form method="post"><button name="action" value="save">Save game</button><button name="action" value="load">Resume saved game</button><button name="action" value="reset">New game</button></form><small>Python rules-based simulation · No AI</small></html>'''
class Handler(BaseHTTPRequestHandler):
    def reply(self,error=''):
        body=page(error).encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self): self.reply()
    def do_POST(self):
        global state
        try:
            p=parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()); get=lambda k:p[k][0]; action=get('action')
            if action=='trade' and state['day']<=30:
                price=float(get('price')); stock=int(get('stock')); loc=get('location'); q=get('quality')
                if not .5<=price<=20 or not 0<=stock<=1000 or loc not in LOC or q not in ['Standard','Premium']: raise ValueError('Invalid trading plan.')
                simulate(state,loc,price,stock,q)
            elif action=='save': SAVE.write_text(json.dumps(state)); return self.reply('Game saved.')
            elif action=='load': state=load_game()
            elif action=='reset': state=fresh()
            self.send_response(303); self.send_header('Location','/'); self.end_headers()
        except (ValueError,KeyError,OSError) as e: self.reply(str(e))
if __name__=='__main__':
    print('Open http://localhost:8000 in your browser. Ctrl+C to stop.')
    HTTPServer(('127.0.0.1',8000),Handler).serve_forever()
