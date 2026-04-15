// renderer.js — Canvas2D drawing utilities (replaces OpenGL renderer.py)
import { W, H, C_BG, C_GRID } from './settings.js';

/** Convert [r,g,b,a] (0-1 floats) to CSS rgba string */
export function rgba(c, aOverride) {
  const a = aOverride !== undefined ? aOverride : c[3];
  return `rgba(${c[0]*255|0},${c[1]*255|0},${c[2]*255|0},${a})`;
}

export function clearScreen(ctx) {
  ctx.fillStyle = rgba(C_BG);
  ctx.fillRect(0, 0, W, H);
}

export function drawGrid(ctx, spacing=40) {
  ctx.strokeStyle = rgba(C_GRID);
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x <= W; x += spacing) { ctx.moveTo(x,0); ctx.lineTo(x,H); }
  for (let y = 0; y <= H; y += spacing) { ctx.moveTo(0,y); ctx.lineTo(W,y); }
  ctx.stroke();
}

export function drawCircle(ctx, cx, cy, r, color) {
  if (r <= 0) return;
  ctx.fillStyle = rgba(color);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2); ctx.fill();
}

export function drawRect(ctx, x, y, w, h, color) {
  ctx.fillStyle = rgba(color);
  ctx.fillRect(x, y, w, h);
}

export function drawRectGradV(ctx, x, y, w, h, c1, c2) {
  const g = ctx.createLinearGradient(x, y, x, y+h);
  g.addColorStop(0, rgba(c1)); g.addColorStop(1, rgba(c2));
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
}

export function drawRect3d(ctx, x, y, w, h, color) {
  const lt = [Math.min(1,color[0]*1.3),Math.min(1,color[1]*1.3),Math.min(1,color[2]*1.3),color[3]];
  const dk = [color[0]*0.6,color[1]*0.6,color[2]*0.6,color[3]];
  drawRectGradV(ctx, x, y, w, h, lt, dk);
  const b = 2;
  const hi = [Math.min(1,color[0]*1.6),Math.min(1,color[1]*1.6),Math.min(1,color[2]*1.6),0.8];
  const sh = [color[0]*0.3,color[1]*0.3,color[2]*0.3,0.8];
  drawRect(ctx,x,y,w,b,hi); drawRect(ctx,x,y,b,h,[hi[0],hi[1],hi[2],0.5]);
  drawRect(ctx,x,y+h-b,w,b,sh); drawRect(ctx,x+w-b,y,b,h,[sh[0],sh[1],sh[2],0.5]);
}

export function drawTriangle(ctx, cx, cy, size, angleDeg, color) {
  const rad = angleDeg * Math.PI/180;
  const ca = Math.cos(rad), sa = Math.sin(rad);
  const pc = Math.cos(rad+Math.PI/2), ps = Math.sin(rad+Math.PI/2);
  const tx=cx+ca*size, ty=cy+sa*size;
  const bk=size*0.4, bs=size*0.6;
  const b1x=cx-ca*bk+pc*bs, b1y=cy-sa*bk+ps*bs;
  const b2x=cx-ca*bk-pc*bs, b2y=cy-sa*bk-ps*bs;

  const g = ctx.createLinearGradient(b1x,b1y,tx,ty);
  const bright=[Math.min(1,color[0]*1.4),Math.min(1,color[1]*1.4),Math.min(1,color[2]*1.4),color[3]];
  const dark=[color[0]*0.7,color[1]*0.7,color[2]*0.7,color[3]];
  g.addColorStop(0,rgba(dark)); g.addColorStop(1,rgba(bright));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(tx,ty); ctx.lineTo(b1x,b1y); ctx.lineTo(b2x,b2y); ctx.closePath(); ctx.fill();
}

export function drawGlow(ctx, cx, cy, radius, color, layers=3) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = layers; i > 0; i--) {
    const a = color[3] * (i/layers) * 0.5;
    const r = radius * (0.5 + i*0.4);
    drawCircle(ctx, cx, cy, r, [color[0],color[1],color[2],a]);
  }
  ctx.restore();
}

export function drawRadialGrad(ctx, cx, cy, radius, color) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(cx,cy,0,cx,cy,radius);
  g.addColorStop(0, rgba(color));
  g.addColorStop(1, rgba([color[0],color[1],color[2],0]));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(cx,cy,radius,0,Math.PI*2); ctx.fill();
  ctx.restore();
}

export function drawCrosshair(ctx, cx, cy, size, color, rot=0) {
  ctx.lineWidth = 1.5;
  for (let i = 0; i < 4; i++) {
    const a = Math.PI/2*i;
    const dx=Math.cos(a+rot)*size, dy=Math.sin(a+rot)*size;
    const inner = 0.35;
    const g = ctx.createLinearGradient(cx+dx*inner,cy+dy*inner,cx+dx,cy+dy);
    g.addColorStop(0, rgba(color, color[3]*0.7));
    g.addColorStop(1, rgba(color, color[3]*0.15));
    ctx.strokeStyle = g;
    ctx.beginPath(); ctx.moveTo(cx+dx*inner,cy+dy*inner); ctx.lineTo(cx+dx,cy+dy); ctx.stroke();
  }
  // Outer ring
  ctx.strokeStyle = rgba(color, color[3]*0.3);
  ctx.beginPath(); ctx.arc(cx,cy,size*0.8,0,Math.PI*2); ctx.stroke();
  // Inner ring
  ctx.strokeStyle = rgba(color, color[3]*0.15);
  ctx.beginPath(); ctx.arc(cx,cy,size*0.35,0,Math.PI*2); ctx.stroke();
  ctx.lineWidth = 1;
}

export function drawLine(ctx, x1, y1, x2, y2, color, width=1) {
  ctx.strokeStyle = rgba(color); ctx.lineWidth = width;
  ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
  ctx.lineWidth = 1;
}

export function drawLineGrad(ctx, x1, y1, x2, y2, c1, c2, width=1) {
  const g = ctx.createLinearGradient(x1,y1,x2,y2);
  g.addColorStop(0,rgba(c1)); g.addColorStop(1,rgba(c2));
  ctx.strokeStyle = g; ctx.lineWidth = width;
  ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
  ctx.lineWidth = 1;
}

export function drawDotted(ctx, x1, y1, x2, y2, color, seg=8, gap=6) {
  const dx=x2-x1, dy=y2-y1;
  const len = Math.sqrt(dx*dx+dy*dy);
  if (len < 0.01) return;
  const ux=dx/len, uy=dy/len;
  ctx.strokeStyle = rgba(color); ctx.lineWidth = 1.5;
  ctx.beginPath();
  let pos = 0;
  while (pos < len) {
    const end = Math.min(pos+seg, len);
    ctx.moveTo(x1+ux*pos, y1+uy*pos);
    ctx.lineTo(x1+ux*end, y1+uy*end);
    pos += seg+gap;
  }
  ctx.stroke(); ctx.lineWidth = 1;
}

export function drawBorder(ctx, area) {
  const x=area.left, y=area.top, w=area.right-area.left, h=area.bottom-area.top;
  ctx.strokeStyle = 'rgba(38,51,77,0.8)'; ctx.lineWidth = 2;
  ctx.strokeRect(x,y,w,h); ctx.lineWidth = 1;
}

export function drawFade(ctx, alpha) {
  if (alpha <= 0) return;
  ctx.fillStyle = `rgba(0,0,0,${Math.min(1,alpha)})`;
  ctx.fillRect(0,0,W,H);
}

export function drawText(ctx, text, x, y, size, color, opts={}) {
  const { centered=false, alpha=1 } = opts;
  ctx.save();
  ctx.font = `bold ${size}px 'Segoe UI', Arial, sans-serif`;
  ctx.fillStyle = rgba(color, color[3]*alpha);
  ctx.textBaseline = 'middle';
  if (centered) { ctx.textAlign = 'center'; ctx.fillText(text, x, y); }
  else { ctx.textAlign = 'left'; ctx.fillText(text, x, y); }
  ctx.restore();
}

export function measureText(ctx, text, size) {
  ctx.font = `bold ${size}px 'Segoe UI', Arial, sans-serif`;
  return ctx.measureText(text).width;
}
