// player.js — Player class with aim + raycasting (ported from player.py)
import { drawTriangle, drawGlow, drawDotted, drawCircle } from './renderer.js';
import { Bullet } from './bullet.js';
import { AIM_SPD, AIM_MIN, AIM_MAX, AIM_START, PSIZE, C_PLAYER, C_PGLOW, C_AIM } from './settings.js';

export class Player {
  constructor(x,y,bullets){
    this.x=x; this.y=y; this.aim=AIM_START;
    this.bullets=bullets; this.size=PSIZE;
  }

  rotate(dir){ this.aim+=dir*AIM_SPD; this.aim=Math.max(AIM_MIN,Math.min(AIM_MAX,this.aim)); }

  shoot(){
    if(this.bullets>0){ this.bullets--; return new Bullet(this.x,this.y,this.aim); }
    return null;
  }

  draw(ctx,walls,area){
    drawGlow(ctx,this.x,this.y,this.size*1.8,C_PGLOW,3);
    drawTriangle(ctx,this.x,this.y,this.size,this.aim,C_PLAYER);
    this._drawAim(ctx,walls,area);
  }

  _drawAim(ctx,walls,area,maxB=2,maxLen=500){
    const pts=this._raycast(walls,area,maxB,maxLen);
    for(let i=0;i<pts.length-1;i++){
      let a=C_AIM[3]*(1-i*0.3);
      if(a<=0.05) break;
      a=Math.max(0.05,a);
      drawDotted(ctx,pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1],[C_AIM[0],C_AIM[1],C_AIM[2],a],8,6);
      if(i>0) drawCircle(ctx,pts[i][0],pts[i][1],3,[1,1,1,a*0.5]);
    }
  }

  _raycast(walls,area,maxB=2,maxLen=500){
    const pts=[[this.x,this.y]];
    let dx=Math.cos(this.aim*Math.PI/180), dy=Math.sin(this.aim*Math.PI/180);
    let x=this.x, y=this.y, rem=maxLen;

    for(let b=0;b<=maxB;b++){
      let minT=rem, hitType=null;

      // Play area edges
      if(dx>0){const t=(area.right-x)/dx; if(t>0.01&&t<minT){const hy=y+t*dy; if(hy>=area.top&&hy<=area.bottom){minT=t;hitType='v';}}}
      else if(dx<0){const t=(area.left-x)/dx; if(t>0.01&&t<minT){const hy=y+t*dy; if(hy>=area.top&&hy<=area.bottom){minT=t;hitType='v';}}}
      if(dy<0){const t=(area.top-y)/dy; if(t>0.01&&t<minT){const hx=x+t*dx; if(hx>=area.left&&hx<=area.right){minT=t;hitType='h';}}}
      else if(dy>0){const t=(area.bottom-y)/dy; if(t>0.01&&t<minT){const hx=x+t*dx; if(hx>=area.left&&hx<=area.right){minT=t;hitType='h';}}}

      // Walls
      for(const wall of walls){
        const wr=wall.rect;
        if(dx>0){const t=(wr.left-x)/dx; if(t>0.01&&t<minT){const hy=y+t*dy; if(hy>=wr.top&&hy<=wr.bottom){minT=t;hitType='v';}}}
        else if(dx<0){const t=(wr.right-x)/dx; if(t>0.01&&t<minT){const hy=y+t*dy; if(hy>=wr.top&&hy<=wr.bottom){minT=t;hitType='v';}}}
        if(dy>0){const t=(wr.top-y)/dy; if(t>0.01&&t<minT){const hx=x+t*dx; if(hx>=wr.left&&hx<=wr.right){minT=t;hitType='h';}}}
        else if(dy<0){const t=(wr.bottom-y)/dy; if(t>0.01&&t<minT){const hx=x+t*dx; if(hx>=wr.left&&hx<=wr.right){minT=t;hitType='h';}}}
      }

      x+=dx*minT; y+=dy*minT; pts.push([x,y]); rem-=minT;
      if(rem<=0||!hitType) break;
      if(hitType==='v') dx*=-1; else dy*=-1;
    }
    return pts;
  }
}
