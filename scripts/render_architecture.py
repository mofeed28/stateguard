from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from html import escape
import textwrap
W,H=1800,1490
im=Image.new('RGB',(W,H),'#f3f6fa'); d=ImageDraw.Draw(im); svg=[]
fonts=Path('C:/Windows/Fonts')
def font(size,bold=False): return ImageFont.truetype(str(fonts/('segoeuib.ttf' if bold else 'segoeui.ttf')),size)
def rect(box,fill,outline=None,r=18):
 d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=2)
 x,y,x2,y2=box; svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" rx="{r}" fill="{fill}" stroke="{outline or fill}" stroke-width="2"/>')
def text(x,y,value,size=24,color='#172438',bold=False):
 d.text((x,y),value,font=font(size,bold),fill=color)
 svg.append(f'<text x="{x}" y="{y+size}" fill="{color}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')
def wrap(x,y,value,width,size=23,color='#516174',bold=False):
 line=''
 for word in value.split():
  test=(line+' '+word).strip()
  if d.textlength(test,font=font(size,bold))>width and line:
   text(x,y,line,size,color,bold);y+=size+10;line=word
  else:line=test
 if line:text(x,y,line,size,color,bold);y+=size+10
 return y

def card(x,y,w,h,title,body,accent='#536cf0',eyebrow=None):
 rect((x,y,x+w,y+h),'#ffffff','#dbe3ec');rect((x+20,y+24,x+26,y+h-24),accent,r=3)
 ty=y+26
 if eyebrow:text(x+45,ty,eyebrow,17,accent,True);ty+=31
 text(x+45,ty,title,28,'#172438',True);ty+=48
 wrap(x+45,ty,body,w-80,22)

def arrow(points,color='#8091a7',dashed=False):
 if not dashed:d.line(points,fill=color,width=3)
 else:
  for a,b in zip(points,points[1:]):
   import math
   length=math.dist(a,b)
   for n in range(0,int(length),18):
    t=n/length;u=min(n+10,length)/length
    d.line([(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t),(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)],fill=color,width=3)
 x,y=points[-1];px,py=points[-2]
 import math
 a=math.atan2(y-py,x-px); head=[(x,y),(x-13*math.cos(a-.45),y-13*math.sin(a-.45)),(x-13*math.cos(a+.45),y-13*math.sin(a+.45))];d.polygon(head,fill=color)
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="3"'+(' stroke-dasharray="10 8"' if dashed else '')+'/>')
 svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in head)+f'" fill="{color}"/>')

rect((0,0,W,175),'#112037',r=0)
text(65,32,'StateGuard',48,'#ffffff',True)
text(65,98,'Check what the bot remembers against what actually happened.',27,'#c4d4eb')
rect((1390,51,1735,114),'#20334e',r=13);text(1410,68,'AWS + LOCAL ARCHITECTURE',18,'#9dc6ff',True)
text(65,205,'01  Two separate evidence paths',30,'#172438',True)
card(65,270,480,215,'Sandbox worker + gate','Every minute via EventBridge. Healthy: one simulated delivery. Uncertain: wait. Conflict: block retry.',eyebrow='SANDBOX · NO REAL SENDS')
card(660,270,480,215,'Sandbox evidence tools','inspect_worker_history / query_delivery_provider read the simulated ledger and worker state.',eyebrow='READ-ONLY STRANDS TOOLS')
card(65,540,480,215,'Existing Gmail send claim','One previously sent self-email. Read fresh receipt metadata from Gmail with OAuth; no resend operation.',accent='#148772',eyebrow='REAL PROVIDER · CONTROLLED TEST')
card(660,540,480,215,'Gmail evidence tools','inspect_send_attempt / query_gmail_receipt read the saved claim and fresh Gmail evidence.',accent='#148772',eyebrow='READ-ONLY STRANDS TOOLS')
card(1255,340,480,325,'Strands investigation','One agent per investigation, using the matching pair of tools. OpenAI GPT-5 mini returns a validated diagnosis, tool trace and measured usage.',eyebrow='ADVISORY ONLY')
text(1300,608,'No send tool. No approval tool.',20,'#536cf0',True)
arrow([(545,365),(660,365)])
arrow([(545,635),(660,635)],'#148772')
arrow([(1140,365),(1190,365),(1190,420),(1255,420)],'#536cf0')
arrow([(1140,635),(1210,635),(1210,585),(1255,585)],'#148772')
text(1148,335,'evidence',16,'#536cf0')
text(65,795,'02  Review & recovery',30,'#172438',True)
card(65,875,480,235,'Versioned recovery state','AWS: DynamoDB conditional writes. Local: SQLite transactions. Separate records for sandbox and Gmail; diagnosis and audit events persist here.',eyebrow='SHARED STATE ON AWS')
card(660,875,480,235,'FastAPI on AWS Lambda','Reads persisted state for the dashboard. The recovery gate rechecks evidence and the expected version before writing a reconciliation.',eyebrow='DETERMINISTIC AUTHORIZATION')
card(1255,875,480,235,'Operator dashboard','Review evidence, diagnosis and audit history. The operator requests approval through the API; reconciliation updates belief only.',eyebrow='HUMAN DECISION')
arrow([(1495,665),(1495,775),(570,775),(570,840),(305,840),(305,875)],'#536cf0')
text(840,748,'validated report saved to state',18,'#536cf0')
arrow([(545,945),(660,945)])
text(556,913,'read',18)
arrow([(660,1035),(545,1035)],'#148772');text(559,1044,'write',18,'#148772')
arrow([(1140,945),(1255,945)]);text(1155,913,'view',18)
arrow([(1255,1035),(1140,1035)],'#148772');text(1147,1044,'approve',18,'#148772')
rect((65,1170,1735,1280),'#e7edf5',r=16)
text(90,1187,'RUNTIME & SECRETS',17,'#536cf0',True)
wrap(90,1220,'Lambda uses its IAM role for DynamoDB and Secrets Manager. OpenAI and Gmail credentials are read server-side from Secrets Manager. Local development uses .env and ignored credential files.',1590,22)
rect((65,1310,1735,1450),'#e7edf5',r=16)
text(90,1327,'DEMO BOUNDARY',17,'#148772',True)
wrap(90,1360,'Gmail acknowledgment loss is deliberately injected. Subject/account/time matching is weaker than a stable provider identifier. Sandbox atomicity does not guarantee exactly-once delivery to external APIs. Bedrock is optional; live trading integration is future work.',1590,22)
Path('docs/architecture-diagram.png').parent.mkdir(exist_ok=True)
im.save('docs/architecture-diagram.png',optimize=True)
source=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="StateGuard Architecture"><rect width="100%" height="100%" fill="#f3f6fa"/>'+''.join(svg)+'</svg>'
Path('docs/architecture-diagram.svg').write_text(source,encoding='utf-8')
Path('docs/architecture-diagram.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>StateGuard Architecture</title><style>body{margin:0;background:#f3f6fa}svg{display:block;width:100%;height:auto;max-width:1800px;margin:auto}</style></head><body>'+source+'</body></html>',encoding='utf-8')
print('Created PNG, editable SVG and updated HTML architecture.')
