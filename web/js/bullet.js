// bullet.js — Bullet with ricochet physics (ported from bullet.py)
import { drawCircle, drawGlow } from './renderer.js';
import { play } from './audio.js';
import { BSPEED, BRADIUS, MAX_BOUNCE, TRAIL_LEN, C_BCORE, C_BGLOW, C_TRAIL, C_ENEMY, C_EMOV } from './settings.js';

function rectsOverlap(a,b){
  return a.left<b.right && a.right>b.left && a.top<b.bottom && a.bottom>b.top;
}

export class Bullet {
  constructor(x,y,angleDeg){
    const rad=angleDeg*Math.PI/180;
    this.x=x; this.y=y;
    this.vx=Math.cos(rad)*BSPEED; this.vy=Math.sin(rad)*BSPEED;
    this.radius=BRADIUS; this.bounces=0; this.alive=true;
    this.trail=[];
  }

  get rect(){
    return {left:this.x-this.radius,top:this.y-this.radius,
            right:this.x+this.radius,bottom:this.y+this.radius};
  }

  update(walls,enemies,particles,area){
    this.trail.push([this.x,this.y]);
    if(this.trail.length>TRAIL_LEN) this.trail.shift();

    this.x+=this.vx; this.y+=this.vy;

    // Edge bouncing
    if(this.x-this.radius<area.left){this.x=area.left+this.radius;this.vx*=-1;this.bounces++;play('bounce');particles.spawnSparks(this.x,this.y);}
    else if(this.x+this.radius>area.right){this.x=area.right-this.radius;this.vx*=-1;this.bounces++;play('bounce');particles.spawnSparks(this.x,this.y);}
    if(this.y-this.radius<area.top){this.y=area.top+this.radius;this.vy*=-1;this.bounces++;play('bounce');particles.spawnSparks(this.x,this.y);}
    else if(this.y+this.radius>area.bottom){this.y=area.bottom-this.radius;this.vy*=-1;this.bounces++;play('bounce');particles.spawnSparks(this.x,this.y);}

    // Wall bouncing
    const br = this.rect;
    for(const wall of walls){
      const wr = wall.rect;
      if(rectsOverlap(br,wr)){
        this._resolveWall(wall,particles); break;
      }
    }

    // Enemy collision (pass-through)
    let hits=0;
    const br2=this.rect;
    for(const e of enemies){
      if(e.alive && rectsOverlap(br2,e.rect)){
        e.hit(); play('explosion');
        const c=e.type==='static'?C_ENEMY:C_EMOV;
        particles.spawnExplosion(e.x,e.y,c);
        hits++;
      }
    }
    if(this.bounces>=MAX_BOUNCE) this.alive=false;
    return hits;
  }

  _resolveWall(wall,particles){
    const wr=wall.rect;
    const ol=this.x+this.radius-wr.left;
    const or_=wr.right-(this.x-this.radius);
    const ot=this.y+this.radius-wr.top;
    const ob=wr.bottom-(this.y-this.radius);
    const m=Math.min(ol,or_,ot,ob);
    if(m===ol){this.vx=-Math.abs(this.vx);this.x=wr.left-this.radius;}
    else if(m===or_){this.vx=Math.abs(this.vx);this.x=wr.right+this.radius;}
    else if(m===ot){this.vy=-Math.abs(this.vy);this.y=wr.top-this.radius;}
    else{this.vy=Math.abs(this.vy);this.y=wr.bottom+this.radius;}
    this.bounces++; play('bounce'); particles.spawnSparks(this.x,this.y);
  }

  draw(ctx){
    const n=this.trail.length;
    for(let i=0;i<n;i++){
      const t=(i+1)/Math.max(n,1);
      const a=t*0.5, r=this.radius*0.4*t+0.5;
      drawCircle(ctx,this.trail[i][0],this.trail[i][1],r,[C_TRAIL[0],C_TRAIL[1],C_TRAIL[2],a]);
    }
    drawGlow(ctx,this.x,this.y,this.radius*3,C_BGLOW,3);
    drawCircle(ctx,this.x,this.y,this.radius,C_BCORE);
  }
}
