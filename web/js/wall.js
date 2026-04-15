// wall.js — Wall class (ported from wall.py)
import { drawRect3d } from './renderer.js';
import { C_WALL } from './settings.js';

export class Wall {
  constructor(x,y,w,h){ this.x=x; this.y=y; this.w=w; this.h=h; }
  get rect(){ return {x:this.x, y:this.y, w:this.w, h:this.h, left:this.x, top:this.y, right:this.x+this.w, bottom:this.y+this.h}; }
  draw(ctx){ drawRect3d(ctx, this.x, this.y, this.w, this.h, C_WALL); }
}
