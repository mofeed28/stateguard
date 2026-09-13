from pathlib import Path
import json,re,wave,textwrap,subprocess,os
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]/'artifacts'/os.getenv('STATEGUARD_VIDEO_DIR','demo')
scenes=json.loads((ROOT/'scenes.json').read_text())
font_dir=Path('C:/Windows/Fonts')
def font(n,bold=False): return ImageFont.truetype(str(font_dir/('segoeuib.ttf' if bold else 'segoeui.ttf')),n)
def lines(draw,text,ft,width):
 out=[]; line=''
 for word in text.split():
  nxt=(line+' '+word).strip()
  if draw.textlength(nxt,font=ft)>width and line: out.append(line); line=word
  else: line=nxt
 return out+[line]
def block(draw,text,pos,size,width,color='#f4f6fb',bold=False,gap=1.2):
 ft=font(size,bold); x,y=pos
 for ln in lines(draw,text,ft,width): draw.text((x,y),ln,font=ft,fill=color); y+=int(size*gap)
 return y
frames=[]; subtitle=[]; clock=0; wavs=[]
for idx,scene in enumerate(scenes):
 with wave.open(str(ROOT/f'voice-{idx}.wav'),'rb') as w:
  params=w.getparams(); data=w.readframes(w.getnframes()); duration=w.getnframes()/w.getframerate(); wavs.append((params,data))
 base=Image.new('RGB',(1920,1080),'#0c1220'); d=ImageDraw.Draw(base)
 d.rounded_rectangle((64,58,122,116),radius=14,fill='#526ef5'); d.text((75,68),'SG',font=font(24,True),fill='white')
 d.text((145,68),'STATEGUARD',font=font(31,True),fill='white')
 d.text((65,140),'AGENTS FOR HUMANS  /  DEMO WALKTHROUGH',font=font(20),fill='#8ea1bc')
 y=block(d,scene['title'],(65,240),69,880,bold=True)
 y=block(d,scene['subtitle'],(65,y+38),38,850,color='#99b2ff')
 notes=['Fresh provider evidence','Strands + OpenAI','Approval never resends'] if idx<6 else (['Concurrent calls and stale approvals','Four constructed sandbox scenarios','Production effectiveness not yet measured'] if idx==6 else ['Real provider integration: planned','Shared cloud storage: planned','Working local prototype: demonstrated'])
 for j,n in enumerate(notes): d.ellipse((70,y+110+j*62,82,y+122+j*62),fill='#66d6b0'); block(d,n,(105,y+95+j*62),26,810,color='#d0d9e8')
 if scene['image']:
  shot=Image.open(ROOT/scene['image']).convert('RGB'); shot=ImageOps.contain(shot,(790,850)); base.paste(shot,(1050+(790-shot.width)//2,55))
 else:
  d.rounded_rectangle((1050,150,1840,800),radius=30,fill='#182439',outline='#2b4263',width=2)
  text='28' if idx==6 else '1'
  d.text((1270,235),text,font=font(180,True),fill='#66d6b0')
  block(d,'regression tests passing' if idx==6 else 'delivery after recovery',(1130,500),45,650,bold=True)
  block(d,'Controlled sandbox verification' if idx==6 else 'No duplicate in the demonstrated flow',(1130,640),28,620,color='#aabbd4')
 d.text((65,885),('REAL APP CAPTURES  |  EXISTING REAL GMAIL SELF-EMAIL' if ROOT.name=='gmail-demo' else 'REAL APP CAPTURES  |  SIMULATED EMAIL DELIVERY'),font=font(20,True),fill='#8397b4')
 chunks=textwrap.wrap(scene['narration'],width=115,break_long_words=False)
 total=sum(len(c) for c in chunks)
 for j,caption in enumerate(chunks):
  dur=duration*len(caption)/total
  im=base.copy(); dd=ImageDraw.Draw(im); dd.rectangle((0,940,1920,1080),fill='#060a12')
  block(dd,caption,(80,963),32,1750)
  dd.rectangle((0,1074,int(1920*(idx+1)/len(scenes)),1079),fill='#66d6b0')
  name=f'frame-{idx}-{j}.png'; im.save(ROOT/name); frames.append((name,dur)); subtitle.append((clock,clock+dur,caption)); clock+=dur
 if idx==0: base.save(ROOT/'poster.png')
with wave.open(str(ROOT/'narration.wav'),'wb') as w:
 w.setparams(wavs[0][0])
 for p,data in wavs:
  assert p[:3]==wavs[0][0][:3]; w.writeframes(data)
manifest=''.join(f"file '{name}'\nduration {dur:.6f}\n" for name,dur in frames)+f"file '{frames[-1][0]}'\n"
(ROOT/'frames.txt').write_text(manifest)
def stamp(t):
 ms=round(t*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(ROOT/'StateGuard-demo.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{c}' for i,(a,b,c) in enumerate(subtitle)),encoding='utf-8')
cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','concat','-safe','0','-i',str(ROOT/'frames.txt'),'-i',str(ROOT/'narration.wav'),'-c:v','libx264','-preset','ultrafast','-crf','23','-r','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(ROOT/'StateGuard-demo.mp4')]
subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
print(f'Rendered {clock:.1f} seconds to {ROOT / "StateGuard-demo.mp4"}')
