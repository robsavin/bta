"""Procedural stand-in art (2560x1440) so the pipeline runs before real Midjourney images exist.
Real images dropped in assets/<ID>.png|jpg|webp take priority."""
import numpy as np, os, sys
from PIL import Image, ImageFilter, ImageDraw
rng = np.random.default_rng(7)
W, H = 2560, 1440
def hexc(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16) for i in (0,2,4)],float)
def grad(top,bot):
    t=np.linspace(0,1,H)[:,None,None]; return (hexc(top)*(1-t)+hexc(bot)*t)*np.ones((H,W,3))
def ridge(base,amp,seed,rough=1.0):
    r=np.random.default_rng(seed); x=np.linspace(0,1,W); y=np.zeros(W)
    for k in range(1,7): y+=r.normal()*np.sin(2*np.pi*(k*0.6+r.random())*x+r.random()*6)/k**rough
    return base+amp*y/np.abs(y).max()
def fill_below(img,ys,color,alpha=1.0):
    mask=(np.arange(H)[:,None]>=ys[None,:])[:,:,None]
    img[:]=np.where(mask,img*(1-alpha)+hexc(color)*alpha,img)
def slab(img,pts,color,strata=None):
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).polygon(pts,fill=255)
    m=np.array(m)[:,:,None]/255.0; layer=np.ones((H,W,3))*hexc(color)
    if strata:
        yy=np.arange(H)[:,None,None]; layer*= (1+0.06*np.sin(yy/strata+np.arange(W)[None,:,None]/900))
    img[:]=img*(1-m)+layer*m
def hiker(img,x,y,s,col="#3b2f2a",pack="#8a4b2a"):
    im=Image.fromarray(img.clip(0,255).astype("uint8")); d=ImageDraw.Draw(im)
    d.ellipse([x-6*s,y-40*s,x+6*s,y-28*s],fill=col); d.rectangle([x-8*s,y-30*s,x+8*s,y-8*s],fill=col)
    d.rectangle([x-16*s,y-34*s,x-6*s,y-10*s],fill=pack); d.rectangle([x-7*s,y-8*s,x+7*s,y],fill=col)
    img[:]=np.array(im).astype(float)
def finish(img,name,tint=None):
    # paper grain + brush dabs for a gouache-ish feel
    im=Image.fromarray(img.clip(0,255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.6))
    d=ImageDraw.Draw(im,"RGBA")
    for _ in range(2500):
        x,y=rng.integers(0,W),rng.integers(0,H); c=tuple(int(v) for v in im.getpixel((int(x),int(y))))
        s=int(rng.integers(8,34)); d.ellipse([x,y,x+s*2,y+s],fill=c+(70,))
    a=np.array(im).astype(float)+rng.normal(0,5,(H,W,1))
    if tint is not None: a=a*0.9+hexc(tint)*0.1
    Image.fromarray(a.clip(0,255).astype("uint8")).save(f"assets/{name}.png")
SK={"A":("#e8c9a0","#f2dfc0"),"B":("#d9c3a5","#ead9bd"),"C":("#b8b3a8","#d6cfc0"),"D":("#d8c7a8","#ecdcc0"),
    "E":("#c5b9a6","#ddd0b8"),"F":("#c9b69c","#e2cfb0"),"G":("#bfae98","#d8c5a8"),"H":("#f0c48a","#f6dcae")}
def scene(n):
    img=grad(*SK[n])
    for i,(b,c) in enumerate([(0.42,"#a7a191"),(0.52,"#8b8676"),(0.62,"#6f6a5e")]):
        fill_below(img,ridge(b*H,60+i*20,10+i+ord(n)),c,0.95)
    if n in "ACH": slab(img,[(900,0),(2560,0),(2560,H),(300,H),(700,500)],"#7c7a76",strata=14)
    if n in "BDG": slab(img,[(0,300),(2560,0),(2560,H),(0,H)],"#85807a",strata=11)
    if n=="C": slab(img,[(0,900),(2560,760),(2560,960),(0,1080)],"#5c564d")
    if n in "EF": slab(img,[(0,500),(2560,900),(2560,H),(0,H)],"#8c8070")
    if n=="F":
        for _ in range(900): x,y=rng.integers(0,W),rng.integers(500,H); ImageDraw.Draw(Image.new("RGB",(1,1)))
    if n=="H": slab(img,[(1500,800),(2300,820),(2400,1300),(1300,1320)],"#5d5750")
    hiker(img,{"A":1230,"B":1280,"C":1300,"D":1200,"E":1350,"F":1500,"G":1600,"H":1650}[n],
          {"A":720,"B":900,"C":880,"D":900,"E":760,"F":1000,"G":1150,"H":790}[n],{"A":2.0,"B":4.5,"C":3.0,"D":4.0,"E":3.0,"F":3.5,"G":6,"H":5}[n])
    if n in "EFG":
        for _ in range(60):
            x,y=rng.integers(0,W),rng.integers(700,H); r=rng.integers(8,26)
            img[max(0,y-r):y+r,max(0,x-r):x+r]=img[max(0,y-r):y+r,max(0,x-r):x+r]*0.7+hexc("#d9cdb8")*0.3
    finish(img,n)
os.makedirs("assets",exist_ok=True)
for n in "ABCDEFGH": scene(n); print("placeholder",n)
