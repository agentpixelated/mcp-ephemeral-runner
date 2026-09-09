from manim import *
import json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
config.background_color = "#090B10"
config.pixel_width = 1280
config.pixel_height = 720
config.frame_rate = 24

CYAN = "#55C1FF"
GREEN = "#61D095"
YELLOW = "#FFD166"
RED = "#EF476F"
PURPLE = "#B084F5"
WHITE2 = "#E9EEF5"
MUTED = "#758195"


def koch_points(level, a=(-5,0), b=(5,0)):
    pts=[np.array([a[0],a[1],0.0]), np.array([b[0],b[1],0.0])]
    for _ in range(level):
        new=[]
        for p,q in zip(pts[:-1],pts[1:]):
            v=(q-p)/3
            p1=p+v; p3=p+2*v
            ang=PI/3
            rot=np.array([[math.cos(ang),-math.sin(ang),0],[math.sin(ang),math.cos(ang),0],[0,0,1]])
            peak=p1+rot@v
            new += [p,p1,peak,p3]
        new.append(pts[-1]); pts=new
    return pts


def path_from_points(points,color=CYAN,width=4):
    m=VMobject(stroke_color=color,stroke_width=width)
    m.set_points_as_corners(points)
    return m


def sierpinski_triangles(level, center=np.array([0.,0.,0.]), size=6.0):
    h=size*math.sqrt(3)/2
    verts=[center+np.array([-size/2,-h/3,0]), center+np.array([size/2,-h/3,0]), center+np.array([0,2*h/3,0])]
    tris=[verts]
    for _ in range(level):
        nxt=[]
        for a,b,c in tris:
            ab=(a+b)/2; bc=(b+c)/2; ca=(c+a)/2
            nxt += [[a,ab,ca],[ab,b,bc],[ca,bc,c]]
        tris=nxt
    return VGroup(*[Polygon(*t,stroke_color=CYAN,stroke_width=1.5,fill_color=CYAN,fill_opacity=.16) for t in tris])


def barnsley_image(w=720,h=520,n=70000,seed=3):
    rng=np.random.default_rng(seed); x=y=0.0
    xs=np.empty(n); ys=np.empty(n)
    for i in range(n):
        r=rng.random()
        if r<0.01: x,y=0,0.16*y
        elif r<0.86: x,y=0.85*x+0.04*y, -0.04*x+0.85*y+1.6
        elif r<0.93: x,y=0.2*x-0.26*y, 0.23*x+0.22*y+1.6
        else: x,y=-0.15*x+0.28*y, 0.26*x+0.24*y+0.44
        xs[i]=x; ys[i]=y
    img=np.zeros((h,w,3),dtype=np.uint8)
    px=((xs+2.8)/5.6*(w-1)).astype(int); py=((10.1-ys)/10.1*(h-1)).astype(int)
    good=(px>=0)&(px<w)&(py>=0)&(py<h)
    img[py[good],px[good]]=[72,205,132]
    for shift in (-1,1):
        p2=np.clip(px[good]+shift,0,w-1); q2=np.clip(py[good],0,h-1); img[q2,p2]=np.maximum(img[q2,p2],[20,80,55])
    return img


def bifurcation_image(w=900,h=460):
    img=np.zeros((h,w,3),dtype=np.uint8)
    rs=np.linspace(2.5,4.0,w)
    x=np.full(w,0.5)
    for _ in range(900): x=rs*x*(1-x)
    for _ in range(170):
        x=rs*x*(1-x)
        yy=np.clip(((1-x)*(h-1)).astype(int),0,h-1)
        img[yy,np.arange(w)]=[85,193,255]
    return img


def mandelbrot_image(w=900,h=560,center=(-0.5,0.0),scale=1.7,max_iter=160):
    aspect=w/h
    xs=np.linspace(center[0]-scale*aspect,center[0]+scale*aspect,w)
    ys=np.linspace(center[1]+scale,center[1]-scale,h)
    C=xs[None,:]+1j*ys[:,None]
    Z=np.zeros_like(C); alive=np.ones(C.shape,bool); it=np.zeros(C.shape,np.int16)
    for k in range(max_iter):
        Z[alive]=Z[alive]*Z[alive]+C[alive]
        esc=alive & (np.abs(Z)>2)
        it[esc]=k+1; alive[esc]=False
        if not alive.any(): break
    t=it.astype(float)/max_iter
    img=np.zeros((h,w,3),dtype=np.uint8)
    img[...,0]=(25+190*np.clip(t*1.7,0,1)).astype(np.uint8)
    img[...,1]=(50+180*np.clip(1-np.abs(t-.35)*2.2,0,1)).astype(np.uint8)
    img[...,2]=(90+165*np.clip(1-t*.8,0,1)).astype(np.uint8)
    img[alive]=[5,8,14]
    return img


def julia_image(c,w=720,h=520,scale=1.7,max_iter=140):
    xs=np.linspace(-scale,scale,w); ys=np.linspace(scale,-scale,h)
    Z=xs[None,:]+1j*ys[:,None]; it=np.zeros(Z.shape,np.int16); alive=np.ones(Z.shape,bool)
    for k in range(max_iter):
        Z[alive]=Z[alive]*Z[alive]+c
        esc=alive&(np.abs(Z)>2)
        it[esc]=k+1; alive[esc]=False
    t=it/max_iter
    img=np.zeros((h,w,3),dtype=np.uint8)
    img[...,0]=(60+170*np.clip(t*1.4,0,1)).astype(np.uint8)
    img[...,1]=(35+120*np.clip(1-t,0,1)).astype(np.uint8)
    img[...,2]=(110+145*np.clip(1-np.abs(t-.45),0,1)).astype(np.uint8)
    img[alive]=[5,8,14]
    return img


def rough_coast(level=5):
    x=np.linspace(-5.7,5.7,350)
    y=np.zeros_like(x)
    rng=np.random.default_rng(4)
    phases=rng.uniform(0,2*np.pi,level)
    for k in range(level):
        y += (0.65/(1.7**k))*np.sin((2.2**k)*x+phases[k])
    pts=[np.array([xx,yy,0]) for xx,yy in zip(x,y)]
    return path_from_points(pts,CYAN,3)


class FractalExplainer(Scene):
    def construct(self):
        self.timings=json.loads((ROOT/'timings.json').read_text())
        self.sections=[
            self.hook,self.coastline,self.recursion,self.koch,self.self_similarity,
            self.dimension_intuition,self.koch_dimension,self.sierpinski,self.snowflake,
            self.fern,self.ifs,self.logistic,self.bifurcation,self.complex_numbers,
            self.mandelbrot_rule,self.boundary,self.zoom,self.julia,self.nature,
            self.applications,self.closing,
        ]
        for i,fn in enumerate(self.sections):
            self._used=0.0; self._segdur=self.timings[i]['duration']
            fn()
            rem=self._segdur-self._used
            if rem>0: self.wait(rem)
            elif rem < -0.4: print('WARNING over segment',i,self.timings[i]['id'],rem)

    def p(self,*anims,run_time=2.0,**kw):
        self.play(*anims,run_time=run_time,**kw); self._used+=run_time
    def w(self,t): self.wait(t); self._used+=t
    def beat(self,n=13): return max(1.3,min(4.0,self._segdur/n))
    def clear(self,rt=1.2):
        mobs=list(self.mobjects)
        if mobs: self.p(*[FadeOut(m) for m in mobs],run_time=rt)
    def title(self,text,sub=None):
        t=Text(text,font_size=42,color=WHITE2,weight=BOLD).to_edge(UP)
        self.p(FadeIn(t,shift=DOWN*.2),run_time=self.beat(16))
        if sub:
            s=Text(sub,font_size=24,color=MUTED).next_to(t,DOWN,buff=.18)
            self.p(FadeIn(s),run_time=self.beat(18)); return t,s
        return t,None

    def hook(self):
        b=self.beat(15)
        title=Text('FRACTALS',font_size=78,color=WHITE2,weight=BOLD)
        sub=Text('simple rules  →  endless detail',font_size=30,color=MUTED).next_to(title,DOWN)
        self.p(Write(title),run_time=b); self.p(FadeIn(sub,shift=UP*.2),run_time=b)
        curve=path_from_points(koch_points(1),CYAN,5).shift(DOWN*1.7)
        self.p(Create(curve),run_time=b*1.2)
        for level in (2,3,4):
            nxt=path_from_points(koch_points(level),CYAN,3.2).shift(DOWN*1.7)
            self.p(Transform(curve,nxt),run_time=b*1.1)
        frame=SurroundingRectangle(curve.copy().scale(.22).move_to(curve.get_center()+RIGHT*1.5),color=YELLOW,buff=.08)
        self.p(Create(frame),run_time=b*.8)
        self.p(curve.animate.scale(1.8).shift(LEFT*.8),FadeOut(title),FadeOut(sub),run_time=b*1.4)
        self.p(FadeOut(frame),run_time=b*.6); self.w(b*.6)

    def coastline(self):
        self.clear(); b=self.beat(16); self.title('Scale changes the answer','The coastline problem')
        coast=rough_coast(6).shift(DOWN*.2); self.p(Create(coast),run_time=b*1.5)
        ruler=Line(LEFT*2,RIGHT*2,color=YELLOW,stroke_width=7).shift(DOWN*2.5)
        lab=Text('100 km ruler',font_size=28,color=YELLOW).next_to(ruler,DOWN)
        self.p(GrowFromCenter(ruler),FadeIn(lab),run_time=b)
        marks=VGroup(*[Dot(coast.point_from_proportion(i/6),color=YELLOW,radius=.05) for i in range(7)])
        self.p(LaggedStart(*[FadeIn(d) for d in marks],lag_ratio=.12),run_time=b*1.3)
        for label,scale,n in [('10 km ruler',.45,15),('1 km ruler',.22,35)]:
            nl=Text(label,font_size=28,color=YELLOW).move_to(lab)
            nr=ruler.copy().scale(scale)
            nm=VGroup(*[Dot(coast.point_from_proportion(i/(n-1)),color=YELLOW,radius=.028) for i in range(n)])
            self.p(Transform(ruler,nr),Transform(lab,nl),Transform(marks,nm),run_time=b*1.3)
        q=Text('length depends on scale',font_size=38,color=WHITE2).move_to(DOWN*2.2)
        self.p(FadeOut(ruler),FadeOut(lab),Transform(marks,q),run_time=b)
        arrow=Arrow(LEFT*4.5,RIGHT*4.5,color=MUTED).shift(DOWN*3)
        sm=Text('smaller ruler',font_size=22,color=MUTED).next_to(arrow,DOWN)
        lg=Text('more measured detail',font_size=22,color=CYAN).next_to(arrow,UP)
        self.p(Create(arrow),FadeIn(sm),FadeIn(lg),run_time=b); self.w(b*.6)

    def recursion(self):
        self.clear(); b=self.beat(15); self.title('Recursion','Feed the output back into the rule')
        curve=path_from_points(koch_points(0),CYAN,6); self.p(Create(curve),run_time=b)
        rule=VGroup(Text('replace each segment',font_size=26,color=MUTED),MathTex(r'1\;\to\;4',color=YELLOW).scale(1.2)).arrange(DOWN).to_edge(DOWN)
        self.p(FadeIn(rule),run_time=b)
        counter=Text('1 segment',font_size=28,color=WHITE2).to_corner(UL).shift(DOWN*1.2)
        self.p(FadeIn(counter),run_time=b*.7)
        for level,n in [(1,4),(2,16),(3,64),(4,256)]:
            nxt=path_from_points(koch_points(level),CYAN,max(2.0,6-level)).scale(.9)
            nc=Text(f'{n} segments',font_size=28,color=WHITE2).move_to(counter)
            self.p(Transform(curve,nxt),Transform(counter,nc),run_time=b*1.3); self.w(b*.3)
        simple=Text('the rule stays simple',font_size=32,color=GREEN).next_to(rule,UP,buff=.5)
        complex_=Text('the geometry does not',font_size=32,color=RED).next_to(simple,DOWN)
        self.p(FadeIn(simple),run_time=b*.8); self.p(FadeIn(complex_),run_time=b*.8); self.w(b*.5)

    def koch(self):
        self.clear(); b=self.beat(16); self.title('The Koch curve','Length multiplies by 4/3 every iteration')
        curve=path_from_points(koch_points(1),CYAN,5).shift(UP*.4); self.p(Create(curve),run_time=b)
        eq=MathTex(r'L_{n+1}=\frac{4}{3}L_n',color=YELLOW).scale(1.25).shift(DOWN*2.1); self.p(Write(eq),run_time=b)
        values=VGroup(*[MathTex(s,color=WHITE2) for s in [r'L_0=1',r'L_1=\frac43',r'L_2=\left(\frac43\right)^2',r'L_3=\left(\frac43\right)^3']]).arrange(RIGHT,buff=.7).scale(.8).shift(DOWN*1.1)
        for i,level in enumerate((1,2,3,4)):
            nxt=path_from_points(koch_points(level),CYAN,max(2.2,5-level*.6)).scale(.85).shift(UP*.4)
            self.p(Transform(curve,nxt),FadeIn(values[i],shift=UP*.2),run_time=b*1.05)
        infinity=MathTex(r'\lim_{n\to\infty}L_n=\infty',color=RED).scale(1.25).move_to(eq)
        self.p(Transform(eq,infinity),run_time=b*1.2); self.w(b*.5)

    def self_similarity(self):
        self.clear(); b=self.beat(14); self.title('Self-similarity','Structure survives a change of scale')
        whole=path_from_points(koch_points(4),CYAN,2.5).scale(.9); self.p(Create(whole),run_time=b*1.3)
        box=Rectangle(width=2.3,height=1.5,color=YELLOW).move_to(whole.get_center()+LEFT*1.9); self.p(Create(box),run_time=b)
        clone=whole.copy().scale(2.2).shift(RIGHT*2.3+DOWN*.2)
        self.p(whole.animate.shift(LEFT*3.0).scale(.85),box.animate.shift(LEFT*3.0).scale(.85),FadeIn(clone),run_time=b*1.6)
        exact=Text('exact self-similarity',font_size=30,color=YELLOW).to_edge(DOWN); self.p(FadeIn(exact),run_time=b)
        smooth=Circle(radius=1.4,color=MUTED).shift(RIGHT*2.5)
        tangent=Line(LEFT*1.6,RIGHT*1.6,color=WHITE2).move_to(smooth.get_right()).rotate(PI/2)
        self.p(FadeOut(clone),FadeIn(smooth),run_time=b)
        z=Text('zoom a smooth curve → line',font_size=26,color=MUTED).next_to(smooth,DOWN)
        self.p(FadeIn(tangent),FadeIn(z),run_time=b)
        rough=Text('zoom a fractal → more structure',font_size=30,color=GREEN).move_to(exact)
        self.p(Transform(exact,rough),run_time=b); self.w(b*.6)

    def dimension_intuition(self):
        self.clear(); b=self.beat(17); self.title('Dimension is a scaling exponent')
        line=Line(LEFT*1.2,RIGHT*1.2,color=CYAN,stroke_width=7).shift(LEFT*4+UP*.5)
        sq=Square(2.2,color=GREEN).shift(UP*.5)
        cube=Cube(2.0,fill_opacity=.05,stroke_color=PURPLE).shift(RIGHT*4+UP*.5)
        self.p(Create(line),Create(sq),Create(cube),run_time=b*1.2)
        nums=VGroup(Text('2 pieces',font_size=28,color=CYAN),Text('4 pieces',font_size=28,color=GREEN),Text('8 pieces',font_size=28,color=PURPLE))
        for n,obj in zip(nums,[line,sq,cube]): n.next_to(obj,DOWN,buff=.6)
        self.p(FadeIn(nums),run_time=b)
        powers=VGroup(MathTex(r'2^1',color=CYAN),MathTex(r'2^2',color=GREEN),MathTex(r'2^3',color=PURPLE)).scale(1.1)
        for p,n in zip(powers,nums): p.move_to(n)
        self.p(Transform(nums,powers),run_time=b)
        eq=MathTex(r'N=s^D',color=YELLOW).scale(1.5).shift(DOWN*2.0); self.p(Write(eq),run_time=b)
        solved=MathTex(r'D=\frac{\log N}{\log s}',color=YELLOW).scale(1.5).move_to(eq); self.p(Transform(eq,solved),run_time=b*1.2)
        frac=Text('D does not have to be an integer',font_size=34,color=WHITE2).to_edge(DOWN)
        self.p(FadeIn(frac,shift=UP*.2),run_time=b); self.w(b*.7)

    def koch_dimension(self):
        self.clear(); b=self.beat(15); self.title('Fractal dimension of the Koch curve')
        big=path_from_points(koch_points(3),CYAN,4).scale(.8).shift(UP*.8); self.p(Create(big),run_time=b)
        cols=VGroup(*[path_from_points(koch_points(2),c,3).scale(.18) for c in [RED,YELLOW,GREEN,PURPLE]]).arrange(RIGHT,buff=.4).shift(DOWN*.7)
        self.p(LaggedStart(*[FadeIn(x,scale=.6) for x in cols],lag_ratio=.12),run_time=b*1.2)
        n=MathTex(r'N=4',color=WHITE2).shift(LEFT*2.5+DOWN*1.8); s=MathTex(r's=3',color=WHITE2).shift(RIGHT*2.5+DOWN*1.8)
        self.p(Write(n),Write(s),run_time=b)
        eq=MathTex(r'D=\frac{\log 4}{\log 3}',color=YELLOW).scale(1.3).to_edge(DOWN); self.p(Write(eq),run_time=b*1.1)
        ans=MathTex(r'D\approx1.2618',color=GREEN).scale(1.45).move_to(eq); self.p(Transform(eq,ans),run_time=b*1.1)
        caption=Text('more than a line, less than a surface',font_size=30,color=MUTED).next_to(ans,UP,buff=.5)
        self.p(FadeIn(caption),run_time=b); self.w(b*.6)

    def sierpinski(self):
        self.clear(); b=self.beat(16); self.title('The Sierpiński triangle','Complexity by subtraction')
        tri=sierpinski_triangles(0,size=5.5).shift(UP*.2); self.p(FadeIn(tri),run_time=b)
        for level in (1,2,3,4):
            nxt=sierpinski_triangles(level,size=5.5).shift(UP*.2); self.p(Transform(tri,nxt),run_time=b*1.15)
        eq=MathTex(r'N=3,\quad s=2',color=WHITE2).shift(DOWN*2.4); self.p(Write(eq),run_time=b)
        dim=MathTex(r'D=\frac{\log 3}{\log 2}\approx1.585',color=YELLOW).scale(1.2).move_to(eq); self.p(Transform(eq,dim),run_time=b*1.2)
        holes=Text('holes appear at every scale',font_size=30,color=GREEN).to_edge(DOWN); self.p(FadeIn(holes),run_time=b); self.w(b*.5)

    def snowflake(self):
        self.clear(); b=self.beat(16); self.title('Infinite perimeter. Finite area.')
        verts=[3*np.array([math.cos(a),math.sin(a),0]) for a in [PI/2,PI/2-2*PI/3,PI/2-4*PI/3]]
        pts=[]
        for a,c in zip(verts,verts[1:]+verts[:1]): pts += koch_points(0,a[:2],c[:2])[:-1]
        pts.append(pts[0]); snow=path_from_points(pts,CYAN,4).scale(.85).shift(UP*.4); self.p(Create(snow),run_time=b)
        for level in (1,2,3):
            pts=[]
            for a,c in zip(verts,verts[1:]+verts[:1]): pts += koch_points(level,a[:2],c[:2])[:-1]
            pts.append(pts[0]); nxt=path_from_points(pts,CYAN,max(2.2,4-level*.5)).scale(.85).shift(UP*.4)
            self.p(Transform(snow,nxt),run_time=b*1.2)
        per=MathTex(r'P_n=P_0\left(\frac43\right)^n\to\infty',color=RED).shift(LEFT*3+DOWN*2.1)
        area=MathTex(r'A_n\to A_\infty<\infty',color=GREEN).shift(RIGHT*3+DOWN*2.1)
        self.p(Write(per),Write(area),run_time=b*1.4); self.p(Indicate(per,color=RED),run_time=b); self.p(Indicate(area,color=GREEN),run_time=b); self.w(b*.5)

    def fern(self):
        self.clear(); b=self.beat(14); self.title('Randomness can draw order','The Barnsley fern')
        img=ImageMobject(barnsley_image()).set_height(5.2).shift(RIGHT*1.6+DOWN*.2)
        dot=Dot(LEFT*4+DOWN*2,color=YELLOW,radius=.08); self.p(FadeIn(dot),run_time=b)
        arrows=VGroup(*[Arrow(LEFT*4+UP*y,LEFT*2.7+UP*y,color=c,buff=.1,max_tip_length_to_length_ratio=.15) for y,c in zip([1.5,.5,-.5,-1.5],[CYAN,GREEN,PURPLE,RED])])
        labels=VGroup(*[Text(t,font_size=24,color=c).next_to(a,LEFT) for t,c,a in zip(['85%','7%','7%','1%'],[CYAN,GREEN,PURPLE,RED],arrows)])
        self.p(LaggedStart(*[Create(a) for a in arrows],lag_ratio=.1),FadeIn(labels),run_time=b*1.3)
        self.p(dot.animate.move_to(LEFT*2.6+UP*1.2),run_time=b); self.p(dot.animate.move_to(LEFT*3.0+UP*.2),run_time=b); self.p(dot.animate.move_to(LEFT*2.5+UP*1.8),run_time=b)
        self.p(FadeOut(dot),FadeOut(arrows),FadeOut(labels),FadeIn(img),run_time=b*1.6)
        text=Text('local random choices → global attractor',font_size=30,color=WHITE2).to_edge(DOWN); self.p(FadeIn(text),run_time=b); self.w(b*.7)

    def ifs(self):
        self.clear(); b=self.beat(15); self.title('The chaos game','Three contractions, one attractor')
        corners=[np.array([-3,-2,0]),np.array([3,-2,0]),np.array([0,3.1,0])]
        tri=Polygon(*corners,color=MUTED,stroke_width=2); self.p(Create(tri),run_time=b)
        labels=VGroup(*[Text(chr(65+i),font_size=25,color=YELLOW).move_to(c+UP*.3) for i,c in enumerate(corners)]); self.p(FadeIn(labels),run_time=b)
        rng=np.random.default_rng(2); p=np.array([.2,.1,0]); dots=VGroup(Dot(p,color=WHITE2,radius=.035)); self.p(FadeIn(dots),run_time=b*.6)
        for batch in [12,35,110]:
            new=[]
            for _ in range(batch):
                c=corners[rng.integers(0,3)]; p=(p+c)/2; new.append(Dot(p,color=CYAN,radius=.018))
            dots.add(*new); self.p(LaggedStart(*[FadeIn(d) for d in new],lag_ratio=.015),run_time=b*1.3)
        full=sierpinski_triangles(5,size=5.9).shift(UP*.35)
        self.p(FadeOut(dots),Transform(tri,full),FadeOut(labels),run_time=b*1.4)
        cap=Text('random sequence, non-random geometry',font_size=32,color=GREEN).to_edge(DOWN); self.p(FadeIn(cap),run_time=b); self.w(b*.6)

    def logistic(self):
        self.clear(); b=self.beat(16); self.title('Deterministic chaos','xₙ₊₁ = r xₙ(1 − xₙ)')
        axes=Axes(x_range=[0,1,0.2],y_range=[0,1,0.2],x_length=5.2,y_length=4.3,tips=False,axis_config={'color':MUTED}).shift(LEFT*2.8+DOWN*.2); self.p(Create(axes),run_time=b)
        r=3.7; graph=axes.plot(lambda x:r*x*(1-x),x_range=[0,1],color=CYAN,stroke_width=4); diag=axes.plot(lambda x:x,x_range=[0,1],color=YELLOW,stroke_width=2)
        self.p(Create(graph),Create(diag),run_time=b*1.1)
        x=.2; segs=VGroup()
        for _ in range(8):
            y=r*x*(1-x); segs.add(Line(axes.c2p(x,x),axes.c2p(x,y),color=GREEN,stroke_width=2),Line(axes.c2p(x,y),axes.c2p(y,y),color=GREEN,stroke_width=2)); x=y
        self.p(LaggedStart(*[Create(s) for s in segs],lag_ratio=.08),run_time=b*2.0)
        seq=VGroup(*[Text(t,font_size=25,color=c) for t,c in [('fixed point',GREEN),('2-cycle',YELLOW),('4-cycle',PURPLE),('chaos',RED)]]).arrange(DOWN,aligned_edge=LEFT,buff=.5).shift(RIGHT*3.2)
        self.p(LaggedStart(*[FadeIn(x,shift=LEFT*.2) for x in seq],lag_ratio=.18),run_time=b*1.5)
        chaos=Text('same rule, explosive sensitivity',font_size=28,color=WHITE2).next_to(seq,DOWN,buff=.7); self.p(FadeIn(chaos),run_time=b); self.w(b*.5)

    def bifurcation(self):
        self.clear(); b=self.beat(13); self.title('The bifurcation diagram','A fossil record of iteration')
        img=ImageMobject(bifurcation_image()).set_width(11.5).shift(DOWN*.2); self.p(FadeIn(img),run_time=b*1.4)
        labels=VGroup(Text('1',font_size=27,color=GREEN),Text('2',font_size=27,color=YELLOW),Text('4',font_size=27,color=PURPLE),Text('chaos',font_size=27,color=RED))
        for l,x in zip(labels,[-4.2,-2.3,-1.2,2.5]): l.move_to([x,2.4,0])
        self.p(LaggedStart(*[FadeIn(l) for l in labels],lag_ratio=.2),run_time=b*1.2)
        box=Rectangle(width=1.25,height=2.6,color=YELLOW).move_to([2.1,-.1,0]); self.p(Create(box),run_time=b)
        self.p(box.animate.scale(1.8).shift(LEFT*.5),img.animate.scale(1.12).shift(LEFT*.4),run_time=b*1.6)
        mini=Text('windows of order inside chaos',font_size=30,color=WHITE2).to_edge(DOWN); self.p(FadeIn(mini),run_time=b); self.w(b*.8)

    def complex_numbers(self):
        self.clear(); b=self.beat(16); self.title('Move the iteration into the complex plane')
        plane=ComplexPlane(x_range=[-2.5,2.5,1],y_range=[-2.2,2.2,1],x_length=6,y_length=5,background_line_style={'stroke_color':'#263042','stroke_width':1}).shift(LEFT*2.8); self.p(Create(plane),run_time=b)
        eq=MathTex(r'z_{n+1}=z_n^2+c',color=YELLOW).scale(1.4).shift(RIGHT*3.4+UP*1.8); self.p(Write(eq),run_time=b)
        c=-.72+.22j; z=0j; dots=VGroup(); lines=VGroup(); prev=plane.n2p(z)
        for k in range(8):
            z=z*z+c; cur=plane.n2p(z); dots.add(Dot(cur,color=[CYAN,GREEN,YELLOW,PURPLE][k%4],radius=.055)); lines.add(Line(prev,cur,color=MUTED,stroke_width=2)); prev=cur
        self.p(LaggedStart(*[AnimationGroup(Create(l),FadeIn(d)) for l,d in zip(lines,dots)],lag_ratio=.15),run_time=b*2.2)
        bounded=Text('bounded orbit?',font_size=31,color=GREEN).shift(RIGHT*3.4); escape=Text('or escape to infinity?',font_size=31,color=RED).next_to(bounded,DOWN,buff=.5)
        self.p(FadeIn(bounded),run_time=b); self.p(FadeIn(escape),run_time=b); self.w(b*.5)

    def mandelbrot_rule(self):
        self.clear(); b=self.beat(15); self.title('The Mandelbrot set','One equation, one repeated question')
        img=ImageMobject(mandelbrot_image()).set_width(9.0).shift(LEFT*1.5+DOWN*.2); self.p(FadeIn(img),run_time=b*1.5)
        eq=VGroup(MathTex(r'z_0=0',color=WHITE2),MathTex(r'z_{n+1}=z_n^2+c',color=YELLOW),MathTex(r'|z_n|>2\Rightarrow\text{escape}',color=RED)).arrange(DOWN,aligned_edge=LEFT,buff=.5).scale(.9).shift(RIGHT*4.2)
        self.p(LaggedStart(*[Write(x) for x in eq],lag_ratio=.3),run_time=b*1.6)
        pixel=Square(.16,color=YELLOW,fill_opacity=.6).move_to(img.get_center()+RIGHT*.7+UP*.15); self.p(FadeIn(pixel),run_time=b)
        trail=VGroup(*[Circle(radius=.18+.12*i,color=[CYAN,PURPLE,RED][i%3],stroke_opacity=.65).move_to(pixel.get_center()) for i in range(4)])
        self.p(LaggedStart(*[Create(c) for c in trail],lag_ratio=.15),run_time=b*1.2)
        cap=Text('color = escape time',font_size=30,color=WHITE2).to_edge(DOWN); self.p(FadeIn(cap),run_time=b); self.w(b*.7)

    def boundary(self):
        self.clear(); b=self.beat(14); self.title('The boundary is where the story lives')
        img=ImageMobject(mandelbrot_image(w=1000,h=600,max_iter=220)).set_width(11.5).shift(DOWN*.2); self.p(FadeIn(img),run_time=b*1.3)
        inside=Dot(img.get_center()+LEFT*2.0,color=GREEN,radius=.09); outside=Dot(img.get_center()+RIGHT*3.5,color=RED,radius=.09); edge=Dot(img.get_center()+RIGHT*.8+UP*.4,color=YELLOW,radius=.1)
        self.p(FadeIn(inside),FadeIn(outside),FadeIn(edge),run_time=b)
        labs=VGroup(Text('stable interior',font_size=25,color=GREEN).next_to(inside,UP),Text('fast escape',font_size=25,color=RED).next_to(outside,UP),Text('sensitive boundary',font_size=25,color=YELLOW).next_to(edge,UP))
        self.p(LaggedStart(*[FadeIn(x) for x in labs],lag_ratio=.2),run_time=b*1.2)
        ring=Circle(radius=.7,color=YELLOW).move_to(edge); self.p(Create(ring),run_time=b)
        self.p(img.animate.scale(1.55).shift(LEFT*.8+DOWN*.3),ring.animate.scale(1.55).shift(LEFT*.8+DOWN*.3),FadeOut(labs),FadeOut(inside),FadeOut(outside),run_time=b*1.8)
        cap=Text('tiny parameter changes → different futures',font_size=31,color=WHITE2).to_edge(DOWN); self.p(FadeIn(cap),run_time=b); self.w(b*.7)

    def zoom(self):
        self.clear(); b=self.beat(13); self.title('Zooming never reaches a final layer')
        centers=[(-.5,0,1.7),(-.7436439,.1318259,.32),(-.7436439,.1318259,.065),(-.743643887,.131825904,.013)]
        imgs=[ImageMobject(mandelbrot_image(w=900,h=560,center=(x,y),scale=s,max_iter=240)).set_width(11.5).shift(DOWN*.2) for x,y,s in centers]
        cur=imgs[0]; self.p(FadeIn(cur),run_time=b)
        factor=Text('× 1',font_size=28,color=YELLOW).to_corner(DR).shift(UP*.5); self.p(FadeIn(factor),run_time=b*.6)
        for k,nxt in enumerate(imgs[1:],start=1):
            nf=Text(f'× {5**k:,}',font_size=28,color=YELLOW).move_to(factor)
            self.p(cur.animate.scale(1.25),FadeOut(cur),FadeIn(nxt,scale=.8),Transform(factor,nf),run_time=b*1.8); cur=nxt
        note=Text('computer precision ends; the mathematical definition does not',font_size=27,color=WHITE2).to_edge(DOWN); self.p(FadeIn(note),run_time=b); self.w(b*.7)

    def julia(self):
        self.clear(); b=self.beat(15); self.title('Julia sets','Freeze c. Vary the starting point z.')
        left=ImageMobject(julia_image(-.8+.156j)).set_width(5.2).shift(LEFT*3); right=ImageMobject(julia_image(.285+.01j)).set_width(5.2).shift(RIGHT*3)
        self.p(FadeIn(left),FadeIn(right),run_time=b*1.4)
        l1=MathTex(r'c=-0.8+0.156i',color=CYAN).next_to(left,DOWN); l2=MathTex(r'c=0.285+0.01i',color=PURPLE).next_to(right,DOWN)
        self.p(Write(l1),Write(l2),run_time=b)
        eq=MathTex(r'z_{n+1}=z_n^2+c',color=YELLOW).scale(1.25).to_edge(UP).shift(DOWN*.8); self.p(Write(eq),run_time=b)
        bridge=Arrow(left.get_right()+RIGHT*.2,right.get_left()+LEFT*.2,color=MUTED); self.p(Create(bridge),run_time=b)
        rule=Text('c inside Mandelbrot → connected Julia set',font_size=29,color=GREEN).to_edge(DOWN); self.p(FadeIn(rule),run_time=b*1.1)
        dust=Text('c outside → disconnected Julia set',font_size=29,color=RED).move_to(rule); self.p(Transform(rule,dust),run_time=b*1.1); self.w(b*.6)

    def nature(self):
        self.clear(); b=self.beat(16); self.title('Nature is fractal-like, not infinitely fractal')
        trunk=Line(DOWN*2.7,DOWN*.8,color=WHITE2,stroke_width=9); self.p(Create(trunk),run_time=b)
        branches=VGroup()
        def grow(origin,length,angle,depth):
            if depth==0:return
            end=origin+length*np.array([math.sin(angle),math.cos(angle),0]); line=Line(origin,end,color=GREEN,stroke_width=max(1.2,depth*1.5)); branches.add(line)
            grow(end,length*.68,angle-.45,depth-1); grow(end,length*.68,angle+.42,depth-1)
        grow(np.array([0,-.8,0]),1.45,0,5)
        self.p(LaggedStart(*[Create(x) for x in branches],lag_ratio=.035),run_time=b*2.3)
        scales=VGroup(*[Text(t,font_size=25,color=c) for t,c in [('trunk',WHITE2),('branch',GREEN),('twig',CYAN),('leaf scale',YELLOW)]]).arrange(RIGHT,buff=.8).to_edge(DOWN)
        self.p(LaggedStart(*[FadeIn(x) for x in scales],lag_ratio=.15),run_time=b*1.3)
        limit=Text('physical scale limits stop the recursion',font_size=31,color=RED).shift(UP*2.5); self.p(FadeIn(limit),run_time=b)
        measure=Text('ask for a scaling law, not just a resemblance',font_size=30,color=WHITE2).next_to(scales,UP,buff=.5); self.p(FadeIn(measure),run_time=b); self.w(b*.5)

    def applications(self):
        self.clear(); b=self.beat(16); self.title('Fractal thinking in practice')
        cards=[]
        for name,sub,c in [('ANTENNAS','multiple scales',CYAN),('TERRAIN','synthetic roughness',GREEN),('MATERIALS','porosity / texture',PURPLE),('TIME SERIES','scaling, with caution',YELLOW)]:
            r=RoundedRectangle(width=3.0,height=2.0,corner_radius=.15,stroke_color=c,fill_color='#10151E',fill_opacity=.75)
            tx=Text(name,font_size=26,color=c,weight=BOLD); st=Text(sub,font_size=20,color=WHITE2); g=VGroup(r,tx,st); tx.move_to(r.get_center()+UP*.3); st.move_to(r.get_center()+DOWN*.35); cards.append(g)
        vg=VGroup(*cards).arrange_in_grid(rows=2,cols=2,buff=.55)
        self.p(LaggedStart(*[FadeIn(c,shift=UP*.2) for c in vg],lag_ratio=.15),run_time=b*1.8)
        old=Text('How big is it?',font_size=36,color=MUTED).to_edge(DOWN); self.p(FadeIn(old),run_time=b)
        new=Text('How does it change with scale?',font_size=38,color=YELLOW).move_to(old); self.p(Transform(old,new),run_time=b*1.3)
        self.p(*[Indicate(c[0]) for c in vg],run_time=b*1.4); self.w(b*.8)

    def closing(self):
        self.clear(); b=self.beat(16)
        words=VGroup(*[Text(t,font_size=38,color=c) for t,c in [('RECURSION',CYAN),('SCALING',YELLOW),('DIMENSION',GREEN),('CHAOS',RED),('ITERATION',PURPLE)]]).arrange(RIGHT,buff=.65).scale(.7).to_edge(UP)
        self.p(LaggedStart(*[FadeIn(w,shift=DOWN*.2) for w in words],lag_ratio=.15),run_time=b*1.5)
        koch=path_from_points(koch_points(4),CYAN,2.2).scale(.35).shift(LEFT*4+DOWN*.8); sier=sierpinski_triangles(4,size=3.5).scale(.65).shift(DOWN*.8); mand=ImageMobject(mandelbrot_image(w=500,h=350,max_iter=180)).set_width(4.0).shift(RIGHT*4+DOWN*.8)
        self.p(Create(koch),FadeIn(sier),FadeIn(mand),run_time=b*1.8)
        arrow1=Arrow(koch.get_right(),sier.get_left(),buff=.35,color=MUTED); arrow2=Arrow(sier.get_right(),mand.get_left(),buff=.35,color=MUTED); self.p(Create(arrow1),Create(arrow2),run_time=b)
        thesis=Text('simple rules  →  repeated transformation  →  complex worlds',font_size=32,color=WHITE2).to_edge(DOWN); self.p(Write(thesis),run_time=b*1.4)
        final=Text('SIMPLICITY CAN GENERATE COMPLEXITY',font_size=48,color=YELLOW,weight=BOLD)
        self.p(FadeOut(koch),FadeOut(sier),FadeOut(mand),FadeOut(arrow1),FadeOut(arrow2),FadeOut(words),Transform(thesis,final),run_time=b*1.8)
        self.p(Indicate(thesis,color=WHITE2,scale_factor=1.04),run_time=b); self.w(b*.8)
