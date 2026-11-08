import json
TR={}
for f in ['tr_0.json','tr_1.json']: TR.update(json.load(open(f)))
d=json.load(open('vclips.json'))
OV={'frol_tupost':(7.75,11.8),'kolya_dr':(1.5,6.2),'pol_banya':(3.45,8.9),'sudba':(15.8,21.6),
'larp_egor':(1.9,7.0),'pol_gora':(10.8,13.4),'tropa':(9.5,23.4),'peak_drink':(1.3,14.0)}
d['aaa']=dict(file='voice_messages/audio_177@11-09-2026_21-21-00.ogg',who='Егор Гусев',date='11.09.2026',t0=0,t1=4.4,words=[])
d['goyda_s']=dict(d['goyda']); OV['goyda_s']=(8.1,9.35)
d['burbur_s']=dict(d['burbur'])
for k,(a,b) in OV.items():
  v=d[k]; ws=[w for s in TR[v['file']] for w in s['words']]
  v['t0'],v['t1']=a,b
  v['words']=[(round(w[0]-a,2),round(w[1]-a,2),w[2].strip()) for w in ws if w[0]>=a-0.05 and w[1]<=b+0.1]
  print(k,' '.join(w[2] for w in v['words']))
json.dump(d,open('vclips.json','w'),ensure_ascii=False)
