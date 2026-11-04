import numpy as np, wave, sys
SR=44100; T=15.1; n=int(SR*T); out=np.zeros(n)
rng=np.random.default_rng(1)
def add(t0,sig,g=1.0):
    i=int(t0*SR); j=min(n,i+len(sig)); out[i:j]+=g*sig[:j-i]
def tt(d): return np.arange(int(d*SR))/SR
def boom(d=0.9):
    t=tt(d); f=120*np.exp(-t*5)+38; ph=2*np.pi*np.cumsum(f)/SR
    return np.tanh(2.5*np.sin(ph)*np.exp(-t*3.2))
def pshh(d=0.35):
    t=tt(d); x=rng.standard_normal(len(t)); x=np.diff(np.concatenate([[0],x]))  # highpassish
    env=np.minimum(1,t/0.005)*np.exp(-t*9); return 0.6*x*env
def ding():
    t=tt(0.35); e=np.exp(-t*12)
    return 0.5*(np.sin(2*np.pi*1320*t)*e + np.sin(2*np.pi*1760*np.clip(t-0.08,0,None))*np.exp(-np.clip(t-0.08,0,None)*12)*(t>0.08))
def beep(d=0.16,f=2000):
    t=tt(d); return 0.35*np.sign(np.sin(2*np.pi*f*t))*np.minimum(1,(d-t)/0.005)
add(0.07,boom(),0.9)
for k in range(4): add(4.07+0.5*k,pshh(),0.8)
add(6.07,boom(1.2),1.0)
for k in range(4): add(8.07+0.5*k,ding(),0.7)
add(10.57,boom(0.6),0.7)
t=tt(0.56); add(10.88,0.3*np.sin(2*np.pi*1000*t)*np.minimum(1,(0.56-t)/0.01),1)
t=tt(0.5); f=300+2500*t; add(11.44,0.12*np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*np.exp(-t*3),1)
add(13.3,boom(1.0),0.8)
for k in range(3): add(14.25+0.22*k,beep(),1)
out=np.clip(out,-1,1)
st=(np.repeat(out[:,None],2,1)*32767*0.7).astype(np.int16)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
