import random, math, time, os
from pygame import Rect

# Config
TITLE, WIDTH, HEIGHT = "WAR BLOCKS", 800, 600
TILE, SPEED, ENEMY_SPEED = 40, 4, 1
BG, WALL, FLOOR = (0, 0, 0), (80, 75, 70), (0, 0, 0)
TEXT, BTN, BTN_HOVER = (230, 235, 30), (10, 110, 5), (5, 35, 5)
PCOLOR, ECOLOR, EXITCOLOR = (50, 180, 100), (200, 70, 80), (20, 25, 30)


class Button:
    def __init__(self, x, y, w, h, text, action):
        self.rect, self.text, self.action, self.hovered = Rect(x, y, w, h), text, action, False

    def draw(self):
        screen.draw.filled_rect(self.rect, BTN_HOVER if self.hovered else BTN)
        screen.draw.text(self.text, center=self.rect.center, color=TEXT, fontsize=24)

    def check_hover(self, pos): self.hovered = self.rect.collidepoint(pos)
    def check_click(self, pos): return self.rect.collidepoint(pos)


class Character:
    def __init__(self, x, y, color, speed):
        self.x, self.y, self.color, self.speed = x, y, color, speed
        self.direction, self.frame, self.counter, self.moving = [0, 0], 0, 0, False

    def move(self, walls):
        nx, ny = self.x + self.direction[0]*self.speed, self.y + self.direction[1]*self.speed
        rect = Rect(nx, ny, TILE*0.8, TILE*0.8)
        if not any(rect.colliderect(w) for w in walls): self.x, self.y, self.moving = nx, ny, True
        else: self.moving = False
        self.counter = (self.counter+1) % 5 if self.moving else 0
        if not self.moving: self.frame = 0
        elif self.counter == 0: self.frame = (self.frame+1) % 4

    def draw(self):
        screen.draw.filled_rect(Rect(self.x, self.y, TILE*0.8, TILE*0.8), self.color)
        if self.moving: offset = math.sin(self.frame*0.5)*3
        else: offset = 0
        screen.draw.filled_rect(Rect(self.x+10, self.y-5+offset, 12, 10), self.color)
        dx, dy = self.direction
        if dx: screen.draw.filled_rect(Rect(self.x+(TILE*0.7 if dx>0 else -5), self.y+15, 8, 10), self.color)
        elif dy: screen.draw.filled_rect(Rect(self.x+15, self.y+(TILE*0.7 if dy>0 else -5), 10, 8), self.color)


class Enemy(Character):
    def __init__(self, x, y):
        super().__init__(x, y, ECOLOR, ENEMY_SPEED)
        self.last, self.dir, self.timer, self.stuck = (x, y), random.choice([(1,0),(-1,0),(0,1),(0,-1)]), 60, 0

    def update(self, walls, player):
        if abs(self.x-self.last[0]) < .5 and abs(self.y-self.last[1]) < .5: self.stuck += 1
        else: self.stuck, self.last = 0, (self.x, self.y)
        if self.stuck > 30 or self.timer <= 0 or not self.moving: self.find_dir(walls, player); self.timer, self.stuck = 60, 0
        else: self.timer -= 1
        self.direction, _r = list(self.dir), random.random()
        self.move(walls)
        if _r < .02: self.dir = random.choice([(1,0),(-1,0),(0,1),(0,-1)])

    def find_dir(self, walls, player):
        dx, dy, dist = player.x-self.x, player.y-self.y, math.hypot(player.x-self.x, player.y-self.y)
        if dist > 0:
            nx, ny = dx/dist, dy/dist
            rect = Rect(self.x+nx*self.speed*5, self.y+ny*self.speed*5, TILE*0.8, TILE*0.8)
            if not any(rect.colliderect(w) for w in walls): self.dir = (nx, ny); return
        dirs = []
        for d in [(1,0),(-1,0),(0,1),(0,-1)]:
            rect = Rect(self.x+d[0]*self.speed*5, self.y+d[1]*self.speed*5, TILE*0.8, TILE*0.8)
            if not any(rect.colliderect(w) for w in walls):
                dot = (d[0]*(dx/dist)+d[1]*(dy/dist)) if dist else 0
                dirs.append((d, dot))
        self.dir = max(dirs, key=lambda x:x[1])[0] if dirs else random.choice([(1,0),(-1,0),(0,1),(0,-1)])


class Game:
    def __init__(self):
        self.state, self.sound_on, self.score, self.level = "menu", True, 0, 1
        self.start_time, self.last_score, self.exit, self.walls, self.enemies = 0, 0, None, [], []
        self.player = Character(WIDTH//2, HEIGHT//2, PCOLOR, SPEED)
        self.menu_btns = [Button(WIDTH//2-100, HEIGHT//2-50, 200, 50, "Start Game", self.start),
                          Button(WIDTH//2-100, HEIGHT//2+20, 200, 50, "Sound: ON", self.toggle_sound),
                          Button(WIDTH//2-100, HEIGHT//2+90, 200, 50, "Exit", exit)]
        self.over_btns = [Button(WIDTH//2-100, HEIGHT//2+10, 200, 50, "Play Again", self.start),
                          Button(WIDTH//2-100, HEIGHT//2+80, 200, 50, "Main Menu", self.menu)]
        self.generate(); self.play("menu_bg", loop=True)

    def play(self, name, loop=False):
        if self.sound_on:
            try: getattr(sounds, name).play(-1 if loop else 0)
            except Exception as e: print("Som falhou:", name, e)

    def stop(self, name):
        try: getattr(sounds, name).stop()
        except: pass

    def valid(self, x, y, size, mind=100):
        r = Rect(x,y,size,size)
        if any(r.colliderect(w) for w in self.walls): return False
        if self.exit and math.hypot(x-self.exit[0], y-self.exit[1]) < mind: return False
        if math.hypot(x-self.player.x,y-self.player.y)<mind: return False
        return True

    def generate(self):
        self.walls = [Rect(x, 0, TILE, TILE) for x in range(0, WIDTH, TILE)] + \
                     [Rect(x, HEIGHT-TILE, TILE, TILE) for x in range(0, WIDTH, TILE)] + \
                     [Rect(0, y, TILE, TILE) for y in range(0, HEIGHT, TILE)] + \
                     [Rect(WIDTH-TILE, y, TILE, TILE) for y in range(0, HEIGHT, TILE)]
        for _ in range(20): self.walls.append(Rect(random.randint(2, WIDTH//TILE-2)*TILE, random.randint(2, HEIGHT//TILE-2)*TILE, TILE, TILE))
        while True:
            x, y = random.randint(3, WIDTH//TILE-3)*TILE, random.randint(3, HEIGHT//TILE-3)*TILE
            if self.valid(x,y,TILE*.8,50): self.player=Character(x,y,PCOLOR,SPEED); break
        while True:
            x,y = random.randint(3, WIDTH//TILE-3)*TILE, random.randint(3, HEIGHT//TILE-3)*TILE
            if self.valid(x,y,TILE,200) and math.hypot(x-self.player.x,y-self.player.y)>200: self.exit=(x,y); break
        self.enemies=[]; 
        for _ in range(2+(self.level-1)):
            for _a in range(50):
                x,y=random.randint(3, WIDTH//TILE-3)*TILE, random.randint(3, HEIGHT//TILE-3)*TILE
                if self.valid(x,y,TILE*.8,150): self.enemies.append(Enemy(x,y)); break

    def start(self):
        self.play("button_click"); self.stop("menu_bg"); self.play("game_bg", loop=True)
        self.state, self.score, self.level = "game", 0, 1
        self.start_time = self.last_score = time.time(); self.generate()

    def toggle_sound(self):
        self.sound_on = not self.sound_on; self.play("button_click")
        self.menu_btns[1].text = "Sound: ON" if self.sound_on else "Sound: OFF"
        if not self.sound_on: self.stop("menu_bg"); self.stop("game_bg")
        elif self.state=="menu": self.play("menu_bg", loop=True)
        elif self.state=="game": self.play("game_bg", loop=True)

    def menu(self): self.play("button_click"); self.stop("game_bg"); self.play("menu_bg", loop=True); self.state="menu"

    def update(self):
        if self.state!="game": return
        if time.time()-self.last_score>=1: self.score+=1; self.last_score=time.time()
        dx,dy=(-1 if keyboard.left else 0)+(1 if keyboard.right else 0),(-1 if keyboard.up else 0)+(1 if keyboard.down else 0)
        if dx and dy: dx,dy=dx*.7071,dy*.7071
        self.player.direction=[dx,dy]; self.player.move(self.walls)
        if self.exit and Rect(self.exit[0],self.exit[1],TILE,TILE).colliderect(Rect(self.player.x,self.player.y,TILE*.8,TILE*.8)):
            self.play("exit_found"); bonus=max(0,500-int((time.time()-self.start_time)*10))
            self.score+=100*self.level+bonus; self.level+=1; self.start_time=time.time(); self.play("level_complete"); self.generate()
        for e in self.enemies:
            e.update(self.walls,self.player)
            if Rect(e.x,e.y,TILE*.8,TILE*.8).colliderect(Rect(self.player.x,self.player.y,TILE*.8,TILE*.8)):
                self.play("collision"); self.stop("game_bg"); self.state="game_over"

    def draw_btns(self, btns): [b.draw() for b in btns]
    def draw(self):
        screen.fill(BG)
        if self.state=="menu":
            screen.draw.text("WAR BLOCKS",center=(WIDTH//2,HEIGHT//4),color=TEXT,fontsize=48); self.draw_btns(self.menu_btns)
        elif self.state=="game":
            [screen.draw.filled_rect(Rect(x,y,TILE,TILE),FLOOR) for x in range(0,WIDTH,TILE) for y in range(0,HEIGHT,TILE)]
            [screen.draw.filled_rect(w,WALL) for w in self.walls]
            if self.exit: screen.draw.filled_rect(Rect(*self.exit,TILE,TILE),EXITCOLOR); screen.draw.text("EXIT",center=(self.exit[0]+TILE//2,self.exit[1]+TILE//2),color=TEXT,fontsize=20)
            self.player.draw(); [e.draw() for e in self.enemies]
            hud=[("Use arrow keys",10,10),("Find the EXIT",10,40),(f"Score: {self.score}",WIDTH-150,10),(f"Level: {self.level}",WIDTH-150,40),
                 (f"Enemies: {len(self.enemies)}",WIDTH-150,70),(f"Time: {int(time.time()-self.start_time)}s",WIDTH-150,100)]
            [screen.draw.text(t,(x,y),color=TEXT) for t,x,y in hud]
        elif self.state=="game_over":
            screen.draw.text("GAME OVER",center=(WIDTH//2,HEIGHT//3),color=TEXT,fontsize=48)
            screen.draw.text(f"Final Score: {self.score}\n\n\n",center=(WIDTH//2,HEIGHT//2-30),color=TEXT,fontsize=32)
            screen.draw.text(f"Reached Level: {self.level}\n\n\n\n",center=(WIDTH//2,HEIGHT//2+10),color=TEXT,fontsize=24); self.draw_btns(self.over_btns)

    def on_mouse_move(self,pos): [b.check_hover(pos) for b in (self.menu_btns if self.state=="menu" else self.over_btns if self.state=="game_over" else [])]
    def on_mouse_down(self,pos): [b.action() for b in (self.menu_btns if self.state=="menu" else self.over_btns if self.state=="game_over" else []) if b.check_click(pos)]


game=Game()
def update(): game.update()
def draw(): game.draw()
def on_mouse_move(pos): game.on_mouse_move(pos)
def on_mouse_down(pos): game.on_mouse_down(pos)
