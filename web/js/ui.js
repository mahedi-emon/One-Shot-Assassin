// ui.js — All UI screens with touch support (ported from ui.py)
import { W, H, HUD_H, SC_BONUS, C_TEXT, C_TITLE, C_SUB, C_OK, C_DANGER,
         C_BCORE, C_BGLOW, C_TRAIL, C_FOOT, C_DIM, C_CROSS } from './settings.js';
import { drawCircle, drawGlow, drawRadialGrad, drawCrosshair, drawLineGrad,
         drawLine, drawRectGradV, drawText, measureText, drawFade } from './renderer.js';

export class UI {
  drawDemoBullet(ctx, trail, x, y) {
    const n = trail.length;
    for (let i=0;i<n;i++) {
      const t=(i+1)/Math.max(n,1);
      drawCircle(ctx,trail[i][0],trail[i][1],1.5+t*3,[C_TRAIL[0],C_TRAIL[1],C_TRAIL[2],t*0.2]);
    }
    drawGlow(ctx,x,y,16,C_BGLOW,3);
    drawCircle(ctx,x,y,5,C_BCORE);
  }

  drawMenu(ctx, frame, bestScore=0, mobile=false) {
    const cx=W/2;
    const ga=0.06+0.02*Math.sin(frame*0.015);
    drawRadialGrad(ctx,cx,200,320,[1,0.75,0.2,ga]);
    drawCrosshair(ctx,cx,195,110,C_CROSS,frame*0.008);
    const gla=0.2+0.1*Math.sin(frame*0.04);
    drawGlow(ctx,cx,170,160,[1,0.84,0,gla],5);
    drawText(ctx,"ONE SHOT ASSASSIN",cx,160,54,C_TITLE,{centered:true});
    drawText(ctx,"A Ricochet Puzzle Game",cx,222,22,C_SUB,{centered:true});

    const ly=255, lh=160;
    const cc=[0.5,0.5,0.65,0.6], ec=[0.2,0.2,0.3,0];
    drawLineGrad(ctx,cx-lh,ly,cx,ly,ec,cc); drawLineGrad(ctx,cx,ly,cx+lh,ly,cc,ec);
    drawCircle(ctx,cx,ly,2.5,[0.5,0.5,0.7,0.5]);

    const my=310;
    const blink=0.55+0.45*Math.sin(frame*0.06);

    drawText(ctx,"Press ENTER or Tap to Start",cx,my,28,C_TEXT,{centered:true,alpha:blink});
    drawText(ctx,"Press I or Tap Here for Instructions",cx,my+55,21,C_SUB,{centered:true});
    if (!mobile) drawText(ctx,"Press ESC to Quit",cx,my+100,19,C_DIM,{centered:true});

    if (bestScore > 0) {
      const bsy = mobile ? my+115 : my+145;
      drawText(ctx,`Best Score: ${bestScore}`,cx,bsy,20,C_TITLE,{centered:true});
    }

    this._drawFooter(ctx,frame);
  }

  _drawFooter(ctx,frame) {
    const cx=W/2, sy=H-110, sh=120;
    const sc=[0.3,0.3,0.4,0.3], se=[0.1,0.1,0.15,0];
    drawLineGrad(ctx,cx-sh,sy,cx,sy,se,sc); drawLineGrad(ctx,cx,sy,cx+sh,sy,sc,se);
    drawText(ctx,"Developed for Computer Graphics Course",cx,H-90,16,C_FOOT,{centered:true});
    drawText(ctx,"Department of Computer Science & Engineering",cx,H-68,15,C_FOOT,{centered:true});
    drawText(ctx,"Daffodil International University, 2026",cx,H-46,15,C_FOOT,{centered:true});
    drawText(ctx,"Developed using JavaScript & HTML5 Canvas",cx,H-18,12,C_DIM,{centered:true});
  }

  drawInstructions(ctx, frame=0, mobile=false) {
    const cx=W/2;
    drawGlow(ctx,cx,58,80,[1,0.84,0,0.08],3);
    drawText(ctx,"HOW TO PLAY",cx,55,40,C_TITLE,{centered:true});
    drawLineGrad(ctx,cx-100,88,cx,88,[0.2,0.2,0.3,0],[0.4,0.4,0.55,0.6]);
    drawLineGrad(ctx,cx,88,cx+100,88,[0.4,0.4,0.55,0.6],[0.2,0.2,0.3,0]);

    let y=118;
    // Show unified controls section
    drawText(ctx,"CONTROLS",cx,y,22,C_TEXT,{centered:true}); y+=38;
    const ctrls=[
      ["LEFT / RIGHT (or ◀ / ▶)","Rotate Aim Direction"],
      ["SPACE (or 🎯 BUTTON)","Fire Bullet"],
      ["R (or Replay Button)","Restart Game"],
      ["ESC (or Menu Button)","Return to Menu"]
    ];
    for(const [k,a] of ctrls){
      drawText(ctx,k,cx-90,y,17,C_TITLE); drawText(ctx,a,cx+70,y,17,C_SUB); y+=28;
    }

    y+=15; drawLine(ctx,cx-80,y,cx+80,y,[0.25,0.25,0.35,0.4]); y+=18;
    drawText(ctx,"GAME RULES",cx,y,22,C_TEXT,{centered:true}); y+=38;
    const rules=["Destroy all enemies with your limited bullets","Bullets ricochet off walls — use this wisely!",
                  "A single bullet can hit multiple enemies","Plan your angles carefully before each shot"];
    for(const l of rules){ drawText(ctx,l,cx,y,18,C_SUB,{centered:true}); y+=28; }

    y+=15; drawLine(ctx,cx-80,y,cx+80,y,[0.25,0.25,0.35,0.4]); y+=18;
    drawText(ctx,"SCORING",cx,y,22,C_TEXT,{centered:true}); y+=38;
    drawText(ctx,"+10  per enemy destroyed",cx,y,19,C_OK,{centered:true}); y+=28;
    drawText(ctx,"-2   per bullet used",cx,y,19,C_DANGER,{centered:true}); y+=28;
    drawText(ctx,"+50  level completion bonus",cx,y,19,C_TITLE,{centered:true});

    const bl=0.4+0.3*Math.sin(frame*0.05);
    const backText = mobile ? "Tap to go back" : "Press ESC to go back";
    drawText(ctx,backText,cx,H-35,17,C_DIM,{centered:true,alpha:bl});
  }

  drawHud(ctx, name, score, bullets, bestScore=0, mobile=false) {
    drawRectGradV(ctx,0,0,W,HUD_H,[0,0,0,0.85],[0,0,0.05,0.5]);
    drawText(ctx,name,15,14+HUD_H/2-10,20,C_TEXT);
    
    let st = `Score: ${score}`;
    if (bestScore > 0) st += `    Best: ${Math.max(score, bestScore)}`;
    drawText(ctx,st,W/2,14+HUD_H/2-10,24,C_TITLE,{centered:true});
    const col=bullets===0?C_DANGER:C_TEXT;
    const bt=`Bullets: ${bullets}`;
    const tw=measureText(ctx,bt,20);
    drawText(ctx,bt,W-tw-15,14+HUD_H/2-10,20,col);
    drawLineGrad(ctx,0,HUD_H,W/2,HUD_H,[0.15,0.2,0.3,0],[0.25,0.35,0.5,0.8]);
    drawLineGrad(ctx,W/2,HUD_H,W,HUD_H,[0.25,0.35,0.5,0.8],[0.15,0.2,0.3,0]);

    // Mobile: draw MENU button in top-right
    if (mobile) {
      this._drawTouchBtn(ctx, W-95, 7, 85, 36, 'MENU', false, 16);
    }
  }

  /** Draw on-screen touch controls at bottom of play area */
  drawTouchControls(ctx, touchState) {
    const btns = [
      { x: 15,  y: 595, w: 265, h: 90, label: '◀  ROTATE', key: 'left' },
      { x: 310, y: 595, w: 280, h: 90, label: '🎯  FIRE',  key: 'fire' },
      { x: 620, y: 595, w: 265, h: 90, label: 'ROTATE  ▶', key: 'right' }
    ];
    for (const btn of btns) {
      const pressed = touchState[btn.key] || false;
      this._drawTouchBtn(ctx, btn.x, btn.y, btn.w, btn.h, btn.label, pressed, 22);
    }
  }

  /** Reusable rounded touch button */
  _drawTouchBtn(ctx, x, y, w, h, label, pressed=false, fontSize=22) {
    const alpha = pressed ? 0.3 : 0.12;
    const borderAlpha = pressed ? 0.55 : 0.2;
    const textAlpha = pressed ? 0.9 : 0.55;
    const r = 14;

    // Filled rounded rect
    ctx.fillStyle = `rgba(255,255,255,${alpha})`;
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y); ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r); ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h); ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r); ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath(); ctx.fill();

    // Border
    ctx.strokeStyle = `rgba(0,150,255,${borderAlpha})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y); ctx.quadraticCurveTo(x+w,y,x+w,y+r);
    ctx.lineTo(x+w,y+h-r); ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
    ctx.lineTo(x+r,y+h); ctx.quadraticCurveTo(x,y+h,x,y+h-r);
    ctx.lineTo(x,y+r); ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath(); ctx.stroke();
    ctx.lineWidth = 1;

    // Label text
    ctx.fillStyle = `rgba(255,255,255,${textAlpha})`;
    ctx.font = `bold ${fontSize}px 'Segoe UI', Arial, sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label, x + w/2, y + h/2);
  }

  drawLevelComplete(ctx, lvl, score, frame=0, bestScore=0, mobile=false) {
    const cx=W/2, cy=H/2;
    drawRadialGrad(ctx,cx,cy-40,200,[0,1,0.5,0.06]);
    drawGlow(ctx,cx,cy-60,120,[0,1,0.5,0.1],4);
    drawText(ctx,"LEVEL COMPLETE!",cx,cy-80,44,C_OK,{centered:true});
    drawText(ctx,`Level ${lvl} Cleared`,cx,cy-25,24,C_SUB,{centered:true});
    drawLine(ctx,cx-60,cy+5,cx+60,cy+5,[0.3,0.5,0.4,0.5]);
    drawText(ctx,`Score: ${score}`,cx,cy+25,28,C_TITLE,{centered:true});
    drawText(ctx,`+${SC_BONUS} Level Bonus!`,cx,cy+65,22,C_TITLE,{centered:true});
    
    if (bestScore > 0) {
      drawText(ctx,`Best Score: ${Math.max(score, bestScore)}`,cx,cy+105,20,C_TITLE,{centered:true});
    }

    const bl=0.5+0.5*Math.sin(frame*0.06);
    const nextText = mobile ? "Tap to Continue" : "Press ENTER for Next Level";
    drawText(ctx,nextText,cx,cy+140,24,C_TEXT,{centered:true,alpha:bl});
    const backText = mobile ? "": "Press ESC for Menu";
    if (backText) drawText(ctx,backText,cx,cy+180,20,C_SUB,{centered:true});
  }

  drawWin(ctx, score, frame=0, bestScore=0, mobile=false) {
    const cx=W/2, cy=H/2;
    drawRadialGrad(ctx,cx,cy-60,250,[1,0.84,0,0.06]);
    drawGlow(ctx,cx,cy-80,180,[1,0.84,0,0.1],5);
    drawCrosshair(ctx,cx,cy-70,90,[1,0.84,0,0.12],frame*0.005);
    drawText(ctx,"VICTORY!",cx,cy-100,56,C_TITLE,{centered:true});
    drawText(ctx,"All Levels Cleared!",cx,cy-30,26,C_OK,{centered:true});
    drawLineGrad(ctx,cx-100,cy+5,cx,cy+5,[0.2,0.2,0.3,0],[0.5,0.5,0.65,0.6]);
    drawLineGrad(ctx,cx,cy+5,cx+100,cy+5,[0.5,0.5,0.65,0.6],[0.2,0.2,0.3,0]);
    drawText(ctx,`Final Score: ${score}`,cx,cy+30,32,C_TEXT,{centered:true});
    
    if (bestScore > 0) {
      drawText(ctx,`Best Score: ${Math.max(score, bestScore)}`,cx,cy+70,24,C_TITLE,{centered:true});
    }

    const bl=0.5+0.5*Math.sin(frame*0.06);
    const playText = mobile ? "Tap to Play Again" : "Press R to Play Again";
    drawText(ctx,playText,cx,cy+110,24,C_TEXT,{centered:true,alpha:bl});
    const backText = mobile ? "" : "Press ESC for Menu";
    if (backText) drawText(ctx,backText,cx,cy+155,20,C_SUB,{centered:true});
  }

  drawGameOver(ctx, score, frame=0, retriesLeft=0, retryPenalty=0, bestScore=0, mobile=false) {
    const cx=W/2, cy=H/2;
    drawRadialGrad(ctx,cx,cy-60,250,[1,0.1,0.15,0.06]);
    drawGlow(ctx,cx,cy-80,160,[1,0.1,0.15,0.1],5);
    drawText(ctx,"GAME OVER",cx,cy-100,56,C_DANGER,{centered:true});
    drawText(ctx,"Bullets Exhausted!",cx,cy-30,24,C_SUB,{centered:true});
    drawLineGrad(ctx,cx-80,cy,cx,cy,[0.2,0.2,0.3,0],[0.5,0.3,0.35,0.6]);
    drawLineGrad(ctx,cx,cy,cx+80,cy,[0.5,0.3,0.35,0.6],[0.2,0.2,0.3,0]);
    drawText(ctx,`Score: ${score}`,cx,cy+25,28,C_TEXT,{centered:true});
    
    if (bestScore > 0) {
      drawText(ctx,`Best Score: ${Math.max(score, bestScore)}`,cx,cy+65,24,C_TITLE,{centered:true});
    }

    const bl=0.5+0.5*Math.sin(frame*0.06);
    if (retriesLeft > 0) {
      const retryText = mobile
        ? `Tap to Retry (${retriesLeft} left, -${retryPenalty} pts)`
        : `Press R to Retry (${retriesLeft} left, -${retryPenalty} pts)`;
      drawText(ctx,retryText,cx,cy+100,24,C_TEXT,{centered:true,alpha:bl});
    } else {
      const restartText = mobile
        ? "Tap to Restart from Level 1"
        : "Press R to Restart from Level 1";
      drawText(ctx,restartText,cx,cy+100,24,C_DANGER,{centered:true,alpha:bl});
    }
    const backText = mobile ? "" : "Press ESC for Menu";
    if (backText) drawText(ctx,backText,cx,cy+150,20,C_SUB,{centered:true});
  }
}
