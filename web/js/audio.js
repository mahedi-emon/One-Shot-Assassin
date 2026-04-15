// audio.js — Web Audio API procedural sound effects
let ctx = null;
const buffers = {};
let ready = false;

function genBuf(sr, len, fn) {
  const buf = ctx.createBuffer(1, len, sr);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = fn(i, len, sr);
  return buf;
}

export function init() {
  if (ready) return;
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
  } catch(e) { return; }
  const sr = ctx.sampleRate;

  buffers.shoot = genBuf(sr, sr*0.15|0, (i,l,sr)=>{
    const t=i/sr; let f=1200-8000*t; if(f<100)f=100;
    const env=1-i/l;
    return (Math.sin(2*Math.PI*f*t)>0?1:-1)*env*0.3;
  });
  buffers.bounce = genBuf(sr, sr*0.05|0, (i,l,sr)=>{
    const t=i/sr;
    return Math.sin(2*Math.PI*1000*t)*Math.exp(-i/(sr*0.015))*0.3;
  });
  buffers.explosion = genBuf(sr, sr*0.3|0, (i,l)=>{
    return (Math.random()*2-1)*(1-i/l)*0.3;
  });
  buffers.select = genBuf(sr, sr*0.1|0, (i,l,sr)=>{
    return Math.sin(2*Math.PI*600*i/sr)*(1-i/l)*0.3;
  });
  buffers.win = genBuf(sr, sr*0.5|0, (i,l,sr)=>{
    const t=i/sr; const f=300+1000*t;
    const env=i<l*0.7?1:1-((i-l*0.7)/(l*0.3));
    return Math.sin(2*Math.PI*f*t)*env*0.3;
  });
  buffers.game_over = genBuf(sr, sr*0.8|0, (i,l,sr)=>{
    const t=i/sr; let f=250-200*t; if(f<40)f=40;
    return (Math.sin(2*Math.PI*f*t)+0.5*Math.sin(2*Math.PI*f*2*t))*(1-i/l)*0.3;
  });
  ready = true;
}

export function play(name) {
  if (!ready || !buffers[name]) return;
  const src = ctx.createBufferSource();
  src.buffer = buffers[name];
  src.connect(ctx.destination);
  src.start();
}
