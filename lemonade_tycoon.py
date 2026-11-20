"""Lemonade Tycoon — run with Python 3, no external packages."""
import random, json, math, errno
import mimetypes
import threading
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlsplit
from pathlib import Path
from html import escape
SAVE=Path(__file__).with_name('lemonade_save.json')
IMAGE_DIR=Path(__file__).with_name('lemonade-tycoon-images')
WEATHER={'Heatwave':1.8,'Sunny':1.4,'Warm':1.2,'Cloudy':1,'Windy':.8,'Light rain':.6,'Heavy rain':.3}
LOC={'Park':(250,10),'High street':(400,20),'Station':(600,35),'Residential':(100,0)}
LOCATION_IMAGES={'Park':'park-stand.png','High street':'high-street-stand.png','Station':'station-shop.png','Residential':'residential-stand.png'}
EXTRA_STAFF_IMAGES=['asian-employee.png','indian-employee.png']
DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
TRAITS=['Organised','Friendly','Steady']
MAX_STAFF=10
DEFAULT_STAFF=[
    dict(id=1,name='Alex',trait='Organised',capacity=50,daily_wage=10),
    dict(id=2,name='Sam',trait='Friendly',capacity=50,daily_wage=10),
]
def team_stats(staff):
    base=sum(person['capacity'] for person in staff)
    traits={person['trait'] for person in staff}
    multiplier=1.1 if 'Organised' in traits and 'Friendly' in traits else 1.0
    return base,multiplier,math.floor(base*multiplier),round(sum(person['daily_wage'] for person in staff),2)
def load_game():
    saved=json.loads(SAVE.read_text())
    saved.setdefault('staff',deepcopy(DEFAULT_STAFF))
    for i,person in enumerate(saved['staff'],1): person.setdefault('id',i)
    saved.setdefault('off_today',[])
    saved['off_today']=[staff_id for staff_id in saved['off_today'] if any(person['id']==staff_id for person in saved['staff'])]
    saved['next_staff_id']=max(saved.get('next_staff_id',1),max((person['id'] for person in saved['staff']),default=0)+1)
    return saved
def fresh(): return dict(day=1,cash=100,weather='Sunny',reputation=75,history=[],staff=deepcopy(DEFAULT_STAFF),off_today=[],next_staff_id=3)
def working_staff(s):
    off_today=set(s.get('off_today',[]))
    return [person for person in s['staff'] if person['id'] not in off_today]
def staff_image(person):
    if person['id']==1: return 'alex.png'
    if person['id']==2: return 'sam.png'
    return EXTRA_STAFF_IMAGES[(person['id']-3)%len(EXTRA_STAFF_IMAGES)]
state=fresh()
def simulate(s,location,price,stock,quality):
    staff=working_staff(s)
    base_capacity,teamwork,capacity,wages=team_stats(staff)
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
    s['history'].append(dict(day=s['day'],weather=s['weather'],location=location,footfall=footfall,demand=demand,sold=sold,waste=stock-sold,revenue=revenue,cost=cost,profit=profit,wages=wages,staff=', '.join(person['name'] for person in staff),base_capacity=base_capacity,teamwork_multiplier=teamwork,capacity=capacity,satisfaction=round(satisfaction)))
    s['day']+=1; s['weather']=random.choices(list(WEATHER),[5,25,20,20,10,15,5])[0]; s['off_today']=[]
    return s

def page(error=''):
    s=state; last=s['history'][-1] if s['history'] else None
    selected_location=s.get('selected_location','Park')
    if selected_location not in LOCATION_IMAGES: selected_location='Park'
    working=working_staff(s)
    base_capacity,teamwork,capacity,wages=team_stats(working)
    off_today=set(s.get('off_today',[]))
    staff_rows=''.join(f"<li><b>{escape(person['name'])}</b> · {escape(person['trait'])} · {person['capacity']} cups/day · £{person['daily_wage']:.2f}/day · {('Shift cancelled today' if person['id'] in off_today else 'Working today' if s['day']<=30 else 'On your roster')}"+(f" <form class=inline method=post><input type=hidden name=staff_id value={person['id']}><button name=action value={'restore_shift' if person['id'] in off_today else 'cancel_shift'}>{'Restore shift' if person['id'] in off_today else 'Cancel shift today'}</button></form>" if s['day']<=30 and (person['id'] in off_today or len(working)>1) else '')+(f" <form class=inline method=post><input type=hidden name=staff_index value={i}><button name=action value=fire>Fire</button></form>" if s['day']<=30 and len(s['staff'])>1 else '')+'</li>' for i,person in enumerate(s['staff']))
    team='<section><h2>Staff and today’s shifts</h2><p>Cancel a shift for today without firing the staff member. Cancelled shifts return at the start of the next day. Roster changes remain in place until you change them.</p><ul>'+staff_rows+'</ul>'+f'<p>Working team: {len(working)} staff. Teamwork: {base_capacity} × {teamwork:g} = <b>{capacity} cups/day</b> ({(teamwork-1)*100:+.0f}%). Today’s wages: £{wages:.2f}.</p>'
    if s['day']<=30 and len(s['staff'])<MAX_STAFF:
        team+=f'''<form method="post"><h3>Add a staff member</h3><label>Name<input name="name" maxlength="24" required></label><label>Trait<select name="trait">{''.join(f'<option>{escape(trait)}</option>' for trait in TRAITS)}</select></label><p>Each new staff member brings 50 cups/day of capacity and costs £10/day.</p><button name="action" value="hire">Hire for today</button></form>'''
    team+='</section>'
    options=lambda vals,selected=None: ''.join(f'<option value="{escape(v)}"{" selected" if v==selected else ""}>{escape(v)}</option>' for v in vals)
    scene_staff=''.join(f'<img class="staff-sprite" src="/images/people/{staff_image(person)}" alt="{escape(person["name"])}" style="left:{(i+1)/(len(working)+1)*100:.1f}%">' for i,person in enumerate(working))
    scene=f'<div class="scene"><img class="location-art" src="/images/{LOCATION_IMAGES[selected_location]}" alt="{escape(selected_location)} lemonade stand">{scene_staff}</div>'
    result='' if not last else '<h2>Last trading day</h2><div class="grid">'+''.join(f'<div>{k.replace("_"," ").title()}<strong>{"£"+format(v,".2f") if k in ("revenue","cost","profit","wages") else escape(str(v))}</strong></div>' for k,v in last.items())+'</div>'
    form=f'''<form method="post"><label>Location<select name="location">{options(LOC,selected_location)}</select></label><label>Price per cup (£)<input name="price" type="number" min=".5" max="20" step=".1" value="4" required></label><label>Cups prepared<input name="stock" type="number" min="0" max="1000" value="30" required></label><label>Drink quality<select name="quality">{options(['Standard','Premium'])}</select></label><p>Standard: £0.40/cup · Premium: £0.75/cup · Staff wages: £{wages:.2f}/day</p><button name="action" value="trade">Start trading day</button></form>''' if s['day']<=30 else '<h2>Campaign complete</h2>'
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lemonade Tycoon</title><style>body{{font:16px system-ui;background:#f6f4df;color:#253e2c;max-width:680px;margin:auto;padding:20px}}.scene{{position:relative;width:100%;aspect-ratio:3/2;overflow:hidden;border-radius:14px;background:#d9e8d5;margin:14px 0 20px}}.location-art{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}.staff-sprite{{position:absolute;bottom:4%;width:100px;height:196px;object-fit:contain;image-rendering:pixelated;transform:translateX(-50%);filter:drop-shadow(1px 2px 2px #3338}}section,form{{background:white;padding:18px;border-radius:14px;margin:14px 0}}label{{display:block;margin:12px 0}}input,select,button{{font:inherit;padding:10px;border-radius:8px;border:1px solid #b4c3a4}}input,select{{display:block;width:100%;box-sizing:border-box;margin-top:5px}}button{{background:#f5d34c;cursor:pointer;font-weight:bold;margin:4px}}.quit{{background:#e7a59a}}.inline{{display:inline;padding:0;margin:0;background:transparent}}.inline button{{padding:5px 9px}}ul{{padding-left:22px}}li{{margin:9px 0}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.grid div{{background:white;padding:12px;border-radius:10px}}strong{{display:block;font-size:23px}}.error{{color:#a22}}</style><h1>🍋 Lemonade Tycoon</h1>{scene}<p>Day {min(s['day'],30)} / 30 · {DAYS[(min(s['day'],30)-1)%7]} · {s['weather']}</p><div class="grid"><div>Cash<strong>£{s['cash']:.2f}</strong></div><div>Reputation<strong>{s['reputation']}%</strong></div></div><p class="error">{escape(error)}</p>{team}{form}{result}<form method="post"><button name="action" value="save">Save game</button><button name="action" value="load">Resume saved game</button><button name="action" value="reset">New Game</button><button class="quit" name="action" value="quit">Quit</button></form><small>Python rules-based simulation · No AI</small><script>const locationImages={json.dumps(LOCATION_IMAGES)};document.querySelector('[name=location]')?.addEventListener('change',event=>document.querySelector('.location-art').src='/images/'+locationImages[event.target.value]);</script></html>'''
class Handler(BaseHTTPRequestHandler):
    def reply(self,error=''):
        body=page(error).encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if not path.startswith('/images/'): return self.reply()
        asset=(IMAGE_DIR/unquote(path.removeprefix('/images/'))).resolve()
        if not asset.is_relative_to(IMAGE_DIR.resolve()) or not asset.is_file():
            self.send_error(404); return
        content=asset.read_bytes()
        content_type='image/webp' if content[:4]==b'RIFF' and content[8:12]==b'WEBP' else mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
        self.send_response(200); self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(content))); self.end_headers(); self.wfile.write(content)
    def do_POST(self):
        global state
        try:
            p=parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode()); get=lambda k:p[k][0]; action=get('action')
            if action=='hire' and state['day']<=30:
                name=get('name').strip(); trait=get('trait')
                if not name or len(name)>24 or trait not in TRAITS: raise ValueError('Enter a name and choose a valid staff trait.')
                if len(state['staff'])>=MAX_STAFF: raise ValueError(f'You can have up to {MAX_STAFF} staff members.')
                state['staff'].append(dict(id=state['next_staff_id'],name=name,trait=trait,capacity=50,daily_wage=10)); state['next_staff_id']+=1
            elif action=='fire' and state['day']<=30:
                index=int(get('staff_index'))
                if len(state['staff'])<=1: raise ValueError('Keep at least one staff member on the team.')
                if not 0<=index<len(state['staff']): raise ValueError('That staff member is no longer on the team.')
                staff_id=state['staff'].pop(index)['id']; state['off_today']=[sid for sid in state['off_today'] if sid!=staff_id]
            elif action in ('cancel_shift','restore_shift') and state['day']<=30:
                staff_id=int(get('staff_id'))
                if not any(person['id']==staff_id for person in state['staff']): raise ValueError('That staff member is no longer on the team.')
                off_today=set(state['off_today'])
                if action=='cancel_shift':
                    if staff_id not in off_today and len(working_staff(state))<=1: raise ValueError('At least one staff member must remain on shift.')
                    off_today.add(staff_id)
                else:
                    off_today.discard(staff_id)
                state['off_today']=list(off_today)
            elif action=='trade' and state['day']<=30:
                price=float(get('price')); stock=int(get('stock')); loc=get('location'); q=get('quality')
                if not .5<=price<=20 or not 0<=stock<=1000 or loc not in LOC or q not in ['Standard','Premium']: raise ValueError('Invalid trading plan.')
                state['selected_location']=loc
                simulate(state,loc,price,stock,q)
            elif action=='save': SAVE.write_text(json.dumps(state)); return self.reply('Game saved.')
            elif action=='load': state=load_game()
            elif action=='reset': state=fresh()
            elif action=='quit':
                self.reply('Game stopped. You can close this tab.')
                threading.Thread(target=server.shutdown,daemon=True).start()
                return
            self.send_response(303); self.send_header('Location','/'); self.end_headers()
        except (ValueError,KeyError,OSError) as e: self.reply(str(e))
if __name__=='__main__':
    for port in range(8000,8011):
        try:
            server=HTTPServer(('127.0.0.1',port),Handler)
            break
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
    else:
        raise RuntimeError('No available local port between 8000 and 8010.')
    print(f'Open http://localhost:{port} in your browser. Ctrl+C to stop.')
    server.serve_forever()
