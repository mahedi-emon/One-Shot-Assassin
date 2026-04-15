// particles.js — Particle system (ported from particles.py)
import { drawCircle, drawGlow } from './renderer.js';
import { C_SPARK } from './settings.js';

class Particle {
  constructor(x,y,vx,vy,color,radius,life) {
    this.x=x; this.y=y; this.vx=vx; this.vy=vy;
    this.color=color; this.radius=radius;
    this.life=life; this.maxLife=life; this.alive=true;
  }
  update() {
    this.x+=this.vx; this.y+=this.vy;
    this.vx*=0.97; this.vy*=0.97;
    this.life--;
    if(this.life<=0) this.alive=false;
  }
  get alpha(){ return Math.max(0, this.life/this.maxLife); }
  get cr(){ return this.radius*this.alpha; }
}

export class ParticleSystem {
  constructor(){ this.particles=[]; }

  spawnExplosion(x,y,color,count=20){
    for(let i=0;i<count;i++){
      const a=Math.random()*Math.PI*2, s=1.5+Math.random()*4;
      const r=2+Math.random()*3, life=20+Math.random()*30|0;
      const c=[
        Math.max(0,Math.min(1,color[0]+Math.random()*0.2-0.1)),
        Math.max(0,Math.min(1,color[1]+Math.random()*0.2-0.1)),
        Math.max(0,Math.min(1,color[2]+Math.random()*0.2-0.1)),
        color[3]
      ];
      this.particles.push(new Particle(x,y,Math.cos(a)*s,Math.sin(a)*s,c,r,life));
    }
  }

  spawnSparks(x,y,count=8){
    for(let i=0;i<count;i++){
      const a=Math.random()*Math.PI*2, s=2+Math.random()*5;
      const life=8+Math.random()*14|0, r=1+Math.random()*2;
      this.particles.push(new Particle(x,y,Math.cos(a)*s,Math.sin(a)*s,C_SPARK,r,life));
    }
  }

  spawnAmbient(w,h,count=1){
    for(let i=0;i<count;i++){
      const x=Math.random()*w, y=Math.random()*h;
      const vx=Math.random()*0.6-0.3, vy=Math.random()*0.6-0.3;
      const life=60+Math.random()*70|0, r=1+Math.random()*2.5;
      this.particles.push(new Particle(x,y,vx,vy,[0.2,0.3,0.55,0.3],r,life));
    }
  }

  update(){ for(const p of this.particles) p.update(); this.particles=this.particles.filter(p=>p.alive); }

  draw(ctx){
    for(const p of this.particles){
      const a=p.alpha*0.8, c=[p.color[0],p.color[1],p.color[2],a], cr=p.cr;
      if(cr>1.5) drawGlow(ctx,p.x,p.y,cr,c,2);
      else drawCircle(ctx,p.x,p.y,Math.max(0.5,cr),c);
    }
  }
}
