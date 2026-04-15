// levels.js — Level data (ported from level.py)
export const LEVELS = [
  {
    name:"Level 1 — Warm Up", bullets:3, player:[450,650],
    enemies:[
      {x:200,y:150,type:"static"},{x:450,y:100,type:"static"},{x:700,y:150,type:"static"}
    ], walls:[]
  },
  {
    name:"Level 2 — Ricochet", bullets:3, player:[450,650],
    enemies:[
      {x:150,y:120,type:"static"},{x:400,y:200,type:"static"},
      {x:600,y:120,type:"static"},{x:750,y:380,type:"static"}
    ],
    walls:[{x:100,y:280,w:250,h:18},{x:550,y:280,w:250,h:18}]
  },
  {
    name:"Level 3 — Moving Targets", bullets:4, player:[450,650],
    enemies:[
      {x:200,y:100,type:"static"},{x:700,y:100,type:"static"},{x:450,y:200,type:"static"},
      {x:250,y:350,type:"moving",axis:"x",range:[150,400],speed:2},
      {x:650,y:350,type:"moving",axis:"x",range:[500,750],speed:3}
    ],
    walls:[{x:440,y:250,w:18,h:150},{x:120,y:450,w:200,h:18},{x:580,y:450,w:200,h:18}]
  }
];
