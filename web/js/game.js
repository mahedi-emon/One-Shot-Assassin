// game.js — Main game controller with retry system & best score
import { W, H, FPS, AREA, FADE_SPD, SC_ENEMY, SC_PEN, SC_BONUS,
         RETRY_COUNTS, RETRY_PENS,
         S_MENU, S_INST, S_PLAY, S_LVLC, S_WIN, S_OVER } from './settings.js';
import { clearScreen, drawGrid, drawBorder, drawFade } from './renderer.js';
import { init as audioInit, play as audioPlay } from './audio.js';
import { LEVELS } from './levels.js';
import { Player } from './player.js';
import { Enemy } from './enemy.js';
import { Wall } from './wall.js';
import { ParticleSystem } from './particles.js';
import { UI } from './ui.js';

class Game {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    canvas.width = W; canvas.height = H;

    this.ui = new UI();
    this.state = S_MENU;
    this.frame = 0;

    // Fade
    this.fadeAlpha = 1; this.fadeDir = -1;
    this.pendingState = null; this.pendingAction = null;

    // Game objects
    this.player = null; this.bullets = []; this.enemies = []; this.walls = [];
    this.particles = new ParticleSystem();
    this.score = 0; this.level = 0;
    this.bestScore = 0;
    this.retriesLeft = 0;

    // Demo bullets
    this.demoBullets = [
      {x:200,y:300,vx:3.5,vy:2.5,trail:[]},
      {x:650,y:450,vx:-2.8,vy:-3.2,trail:[]}
    ];
    this.menuParticles = new ParticleSystem();

    // Input
    this.keys = {};
    window.addEventListener('keydown', e => {
      audioInit();
      if (this.fadeDir === 0) this._onKey(e.key);
      this.keys[e.key] = true;
      e.preventDefault();
    });
    window.addEventListener('keyup', e => { this.keys[e.key] = false; });

    this._loop();
  }

  _fadeTo(state, action) {
    this.fadeDir = 1; this.pendingState = state; this.pendingAction = action;
  }

  _updateFade() {
    if (this.fadeDir === 0) return;
    this.fadeAlpha += this.fadeDir * FADE_SPD;
    if (this.fadeAlpha >= 1 && this.fadeDir === 1) {
      this.fadeAlpha = 1;
      if (this.pendingAction) { this.pendingAction(); this.pendingAction = null; }
      if (this.pendingState) { this.state = this.pendingState; this.pendingState = null; }
      this.fadeDir = -1;
    } else if (this.fadeAlpha <= 0 && this.fadeDir === -1) {
      this.fadeAlpha = 0; this.fadeDir = 0;
    }
  }

  _onKey(key) {
    if (this.state === S_MENU) {
      if (key === 'Enter') { audioPlay('select'); this._fadeTo(S_PLAY, ()=>this._newGame()); }
      else if (key === 'i' || key === 'I') { audioPlay('select'); this._fadeTo(S_INST); }
    } else if (this.state === S_INST) {
      if (key==='Escape'||key==='Backspace'||key==='Enter') { audioPlay('select'); this._fadeTo(S_MENU); }
    } else if (this.state === S_PLAY) {
      if (key === ' ') this._shoot();
      else if (key === 'r' || key === 'R') { audioPlay('select'); this._fadeTo(S_PLAY, ()=>this._newGame()); }
      else if (key === 'Escape') { audioPlay('select'); this._fadeTo(S_MENU); }
    } else if (this.state === S_LVLC) {
      if (key === 'Enter') { audioPlay('select'); this._fadeTo(S_PLAY, ()=>this._nextLevel()); }
      else if (key === 'Escape') { audioPlay('select'); this._fadeTo(S_MENU); }
    } else if (this.state === S_WIN) {
      if (key === 'r' || key === 'R') { audioPlay('select'); this._fadeTo(S_PLAY, ()=>this._newGame()); }
      else if (key === 'Escape') { audioPlay('select'); this._fadeTo(S_MENU); }
    } else if (this.state === S_OVER) {
      if (key === 'r' || key === 'R') {
        audioPlay('select');
        if (this.retriesLeft > 0) {
          this._fadeTo(S_PLAY, ()=>this._retryLevel());
        } else {
          this._fadeTo(S_PLAY, ()=>this._newGame());
        }
      } else if (key === 'Escape') { audioPlay('select'); this._fadeTo(S_MENU); }
    }
  }

  _shoot() {
    if (this.player && this.player.bullets > 0) {
      const b = this.player.shoot();
      if (b) { audioPlay('shoot'); this.bullets.push(b); this.score -= SC_PEN; }
    }
  }

  _newGame() {
    this.bestScore = Math.max(this.bestScore, this.score);
    this.score = 0; this.level = 0;
    this.retriesLeft = RETRY_COUNTS[0];
    this._loadLevel(0);
  }

  _nextLevel() {
    this.level++;
    if (this.level < LEVELS.length) {
      this.retriesLeft = RETRY_COUNTS[this.level];
      this._loadLevel(this.level);
    }
  }

  _retryLevel() {
    this.score -= RETRY_PENS[this.level];
    this.retriesLeft--;
    this._loadLevel(this.level);
  }

  _loadLevel(idx) {
    const d = LEVELS[idx];
    this.player = new Player(d.player[0], d.player[1], d.bullets);
    this.bullets = [];
    this.enemies = d.enemies.map(e => new Enemy(e.x, e.y, e.type, e.axis||'x', e.range||[0,0], e.speed||2));
    this.walls = d.walls.map(w => new Wall(w.x, w.y, w.w, w.h));
    this.particles = new ParticleSystem();
  }

  // === UPDATE ===
  _update() {
    this._updateFade();
    if (this.state === S_PLAY) this._updatePlay();
    else this._updateMenu();
  }

  _updatePlay() {
    if (this.keys['ArrowLeft']) this.player.rotate(-1);
    if (this.keys['ArrowRight']) this.player.rotate(1);
    for (const b of [...this.bullets]) {
      const hits = b.update(this.walls, this.enemies, this.particles, AREA);
      this.score += hits * SC_ENEMY;
      if (!b.alive) this.bullets.splice(this.bullets.indexOf(b), 1);
    }
    for (const e of this.enemies) e.update();
    this.particles.update();

    const alive = this.enemies.filter(e => e.alive).length;
    if (alive === 0) {
      this.score += SC_BONUS;
      if (this.level >= LEVELS.length - 1) {
        if (this.state !== S_WIN) { audioPlay('win'); this.bestScore = Math.max(this.bestScore, this.score); }
        this.state = S_WIN;
      } else {
        if (this.state !== S_LVLC) audioPlay('win');
        this.state = S_LVLC;
      }
    } else if (this.player.bullets === 0 && this.bullets.length === 0) {
      if (this.state !== S_OVER) { audioPlay('game_over'); this.bestScore = Math.max(this.bestScore, this.score); }
      this.state = S_OVER;
    }
  }

  _updateMenu() {
    for (const db of this.demoBullets) {
      db.trail.push([db.x,db.y]); if (db.trail.length > 40) db.trail.shift();
      db.x += db.vx; db.y += db.vy;
      if (db.x < 15 || db.x > W-15) db.vx *= -1;
      if (db.y < 15 || db.y > H-15) db.vy *= -1;
    }
    if (this.frame % 6 === 0) this.menuParticles.spawnAmbient(W, H, 1);
    this.menuParticles.update();
  }

  // === RENDER ===
  _render() {
    const c = this.ctx;
    clearScreen(c); drawGrid(c);

    if (this.state === S_MENU) {
      this.menuParticles.draw(c);
      for (const db of this.demoBullets) this.ui.drawDemoBullet(c, db.trail, db.x, db.y);
      this.ui.drawMenu(c, this.frame, this.bestScore);
    } else if (this.state === S_INST) {
      this.menuParticles.draw(c);
      this.ui.drawInstructions(c, this.frame);
    } else if (this.state === S_PLAY) {
      this._renderPlay(c);
    } else if (this.state === S_LVLC) {
      this.menuParticles.draw(c);
      this.ui.drawLevelComplete(c, this.level+1, this.score, this.frame, this.bestScore);
    } else if (this.state === S_WIN) {
      this.menuParticles.draw(c);
      this.ui.drawWin(c, this.score, this.frame, this.bestScore);
    } else if (this.state === S_OVER) {
      this.menuParticles.draw(c);
      this.ui.drawGameOver(c, this.score, this.frame, this.retriesLeft, RETRY_PENS[this.level], this.bestScore);
    }

    if (this.fadeAlpha > 0) drawFade(c, this.fadeAlpha);
  }

  _renderPlay(c) {
    drawBorder(c, AREA);
    for (const w of this.walls) w.draw(c);
    for (const e of this.enemies) e.draw(c);
    for (const b of this.bullets) b.draw(c);
    this.player.draw(c, this.walls, AREA);
    this.particles.draw(c);
    this.ui.drawHud(c, LEVELS[this.level].name, this.score, this.player.bullets, this.bestScore);
  }

  _loop() {
    this.frame++;
    this._update();
    this._render();
    requestAnimationFrame(() => this._loop());
  }
}

// === ENTRY POINT ===
window.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('game');
  new Game(canvas);
});
