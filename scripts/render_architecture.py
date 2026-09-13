from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from html import escape
import textwrap
W,H=1800,1320
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
rect((1350,51,1735,114),'#20334e',r=13);text(1373,68,'IMPLEMENTED LOCAL SYSTEM',19,'#9dc6ff',True)
for x,n,title in [(65,'01','Evidence'),(660,'02','Investigation'),(1255,'03','Review & recovery')]:
 text(x,215,n,21,'#536cf0',True);text(x+45,209,title,30,'#172438',True)
card(65,285,480,195,'Saved send attempt','Saved before sending; acknowledgment deliberately withheld.',eyebrow='LOCAL RECORD')
card(65,560,480,210,'Gmail API','Fresh metadata for the existing self-email: matching message count, Sent and Inbox labels.',accent='#148772',eyebrow='REAL PROVIDER · OAUTH 2.0')
card(65,880,480,190,'Provider sandbox','Background worker tests healthy, uncertain and conflicting states.',accent='#7b6b96',eyebrow='SEPARATE TEST PATH')
card(660,380,480,255,'Read-only evidence tools','inspect_send_attempt\nquery_gmail_receipt',eyebrow='STRANDS TOOLS')
# Additional explanatory line below tool names.
wrap(705,550,'Only scoped facts reach the model; no mailbox address or message body.',390,21)
card(660,745,480,265,'Strands agent','OpenAI / GPT-5 mini. Produces a Pydantic-validated recommendation, actual tool trace and token usage.',eyebrow='LIVE INVESTIGATION')
text(705,956,'No send tool. No approval tool.',20,'#536cf0',True)
card(1255,285,480,195,'Operator dashboard','Review evidence and diagnosis. Approve local state reconciliation.',eyebrow='HUMAN REVIEW')
card(1255,590,480,265,'FastAPI recovery gate','Rechecks Gmail and the decision version. Holds uncertainty; approval reconciles local belief.',accent='#148772',eyebrow='DETERMINISTIC CONTROL')
text(1300,801,'Gmail recovery never resends.',20,'#148772',True)
card(1255,940,480,150,'SQLite','Recovery state, versions and audit events on one persistent host.',eyebrow=None)
# Evidence flows
arrow([(545,383),(595,383),(595,455),(660,455)])
arrow([(545,665),(605,665),(605,580),(660,580)],'#148772')
arrow([(545,975),(600,975),(600,610),(660,610)],'#9c8fae',True)
text(552,1000,'test tools',16,'#7b6b96')

arrow([(850,635),(850,745)],'#536cf0');arrow([(950,745),(950,635)],'#536cf0')
text(689,678,'evidence',17,'#536cf0');text(960,678,'tool calls',17,'#536cf0')
arrow([(1140,875),(1194,875),(1194,383),(1255,383)],'#536cf0')
text(1150,320,'report',17,'#536cf0')
arrow([(1495,480),(1495,590)],'#148772');text(1512,517,'approval',18,'#148772')
arrow([(1495,855),(1495,940)],'#148772');text(1512,883,'persist',18,'#148772')
rect((65,1140,1735,1270),'#e7edf5',r=16)
text(90,1158,'DEMO BOUNDARY',17,'#536cf0',True)
wrap(90,1192,'Real Gmail self-email; acknowledgment loss deliberately injected. Gmail may rewrite Message-ID, so subject/account/time correlation is weaker evidence. Bedrock is supported but quota-blocked; live exchange integration and shared cloud storage are next.',1605,21)
Path('docs/architecture-diagram.png').parent.mkdir(exist_ok=True)
im.save('docs/architecture-diagram.png',optimize=True)
source=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="StateGuard Architecture"><rect width="100%" height="100%" fill="#f3f6fa"/>'+''.join(svg)+'</svg>'
Path('docs/architecture-diagram.svg').write_text(source,encoding='utf-8')
Path('docs/architecture-diagram.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>StateGuard Architecture</title><style>body{margin:0;background:#f3f6fa}svg{display:block;width:100%;height:auto;max-width:1800px;margin:auto}</style></head><body>'+source+'</body></html>',encoding='utf-8')
print('Created PNG, editable SVG and updated HTML architecture.')
