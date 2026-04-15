// settings.js — All game constants (ported from settings.py)
export const W = 900, H = 700, FPS = 60;
export const HUD_H = 50;
export const AREA = { left:10, top:HUD_H+10, right:W-10, bottom:H-10 };

// Colors [r,g,b,a] 0-1 floats
export const C_BG    = [0.04,0.04,0.12,1], C_GRID = [0.07,0.07,0.17,0.5];
export const C_PLAYER = [0,0.9,1,1], C_PGLOW = [0,0.9,1,0.12], C_AIM = [0,0.9,1,0.45];
export const C_BCORE = [1,1,0.95,1], C_BGLOW = [1,0.84,0,0.3], C_TRAIL = [1,0.55,0,0.6];
export const C_ENEMY = [1,0,0.4,1], C_EMOV  = [1,0.45,0,1];
export const C_WALL  = [0.29,0.35,0.43,1];
export const C_TEXT  = [1,1,1,1], C_TITLE = [1,0.84,0,1], C_SUB = [0.65,0.65,0.75,1];
export const C_OK    = [0,1,0.53,1], C_DANGER = [1,0.2,0.27,1];
export const C_FOOT  = [0.35,0.35,0.45,1], C_DIM = [0.25,0.25,0.35,1];
export const C_CROSS = [0,0.9,1,0.2], C_SPARK = [1,0.9,0.3,1];

export const BSPEED=7, BRADIUS=5, MAX_BOUNCE=6, TRAIL_LEN=25;
export const AIM_SPD=2, AIM_MIN=185, AIM_MAX=355, AIM_START=270;
export const PSIZE=22, ESIZE=28;
export const SC_ENEMY=10, SC_PEN=2, SC_BONUS=50;
export const FADE_SPD=0.04;
export const S_MENU='MENU',S_INST='INST',S_PLAY='PLAY',S_LVLC='LVLC',S_WIN='WIN',S_OVER='OVER';
