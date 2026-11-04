from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from archreview.fixtures import NAMES,load_fixture
root=Path(__file__).resolve().parents[1]/'examples'
root.mkdir(exist_ok=True)
for name in NAMES:
    graph=load_fixture(name)
    root.joinpath(name+'.json').write_text(graph.model_dump_json(indent=2))
    image=Image.new('RGB',(1200,820),'#f3f6fb'); d=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',27)
    except OSError:
        font=title=ImageFont.load_default()
    d.text((30,20),'Architecture test diagram: '+name,fill='#142442',font=title)
    d.text((30,66),'Synthetic test diagram. Live extraction must read these labels.',fill='#45546c',font=font)
    positions={'internet':(70,140),'app':(450,300),'db':(840,470),'alb':(450,140),
               'auth':(70,650),'secrets':(450,650),'monitoring':(840,650)}
    for edge in graph.connections:
        a=positions[edge.source];b=positions[edge.target]
        start=(a[0]+120,a[1]+70);end=(b[0]+120,b[1])
        d.line((start,end),fill='#3566a3',width=4)
        d.polygon([end,(end[0]-8,end[1]-12),(end[0]+8,end[1]-12)],fill='#3566a3')
    for c in graph.components:
        x,y=positions[c.id]
        d.rounded_rectangle((x,y,x+270,y+90),12,fill='white',outline='#3566a3',width=2)
        text=c.label
        if c.instances: text+=' x'+str(c.instances)
        d.text((x+10,y+8),text,fill='#142442',font=font)
        if c.type in ('database','application_server'):
            d.text((x+10,y+34),c.exposure,fill='#45546c',font=font)
        if c.type=='database':
            d.text((x+10,y+60),'Failover: '+c.failover,fill='#45546c',font=font)
    image.save(root/(name+'.png'))
