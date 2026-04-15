// enemy.js — Enemy class (ported from enemy.py)
import { drawRect3d, drawGlow } from './renderer.js';
import { C_ENEMY, C_EMOV, ESIZE } from './settings.js';

export class Enemy {
  constructor(x,y,type='static',axis='x',range=[0,0],speed=2){
    this.x=x; this.y=y; this.type=type; this.size=ESIZE;
    this.alive=true; this.pulse=Math.random()*Math.PI*2;
    this.axis=axis; this.range=range; this.speed=speed; this.dir=1;
  }
  get rect(){
    const h=this.size/2;
    return {x:this.x-h,y:this.y-h,w:this.size,h:this.size,
            left:this.x-h,top:this.y-h,right:this.x+h,bottom:this.y+h};
  }
  update(){
    this.pulse+=0.05;
    if(this.type==='moving'&&this.alive){
      if(this.axis==='x'){
        this.x+=this.speed*this.dir;
        if(this.x<=this.range[0]){this.x=this.range[0];this.dir=1;}
        else if(this.x>=this.range[1]){this.x=this.range[1];this.dir=-1;}
      } else {
        this.y+=this.speed*this.dir;
        if(this.y<=this.range[0]){this.y=this.range[0];this.dir=1;}
        else if(this.y>=this.range[1]){this.y=this.range[1];this.dir=-1;}
      }
    }
  }
  hit(){ this.alive=false; return true; }
  draw(ctx){
    if(!this.alive) return;
    const color = this.type==='static' ? C_ENEMY : C_EMOV;
    const p = 0.5+0.5*Math.sin(this.pulse);
    const ga = 0.08+0.14*p;
    drawGlow(ctx,this.x,this.y,this.size*1.2,[color[0],color[1],color[2],ga],3);
    const h=this.size/2;
    drawRect3d(ctx,this.x-h,this.y-h,this.size,this.size,color);
  }
}
