import cv2, numpy as np, random, math
from PIL import Image, ImageDraw, ImageFont

W, H   = 660, 400
FPS    = 30

# ============================================================
# ASSET LOADING
# ============================================================
def load_sprite(path, scale, rm_white=True):
    img = Image.open(path).convert('RGBA')
    if rm_white:
        a = np.array(img)
        wm = (a[:,:,0]>235)&(a[:,:,1]>235)&(a[:,:,2]>235)
        a[wm,3] = 0
        img = Image.fromarray(a)
    return img.resize(scale, Image.NEAREST)

def colorize_mario(img_path, scale=(54,54)):
    """Color sprite by vertical zone: hat=red, face=skin, body=red, legs=blue"""
    img = Image.open(img_path).convert('RGBA')
    arr = np.array(img)
    wm = (arr[:,:,0]>235)&(arr[:,:,1]>235)&(arr[:,:,2]>235)
    arr[wm,3] = 0
    sprite = Image.fromarray(arr).resize(scale, Image.NEAREST)
    sa = np.array(sprite)
    mask = sa[:,:,3] > 30
    SH, SW = sa.shape[:2]
    result = sa.copy()
    for y in range(SH):
        for x in range(SW):
            if not mask[y,x]: continue
            frac = y/SH
            if frac < 0.30:
                result[y,x,:3] = [210, 50,  20]   # red hat
            elif frac < 0.50:
                result[y,x,:3] = [240,180, 130]   # skin face
            elif frac < 0.72:
                result[y,x,:3] = [210, 50,  20]   # red body
            else:
                result[y,x,:3] = [ 50, 80, 200]   # blue legs
    return Image.fromarray(result)

SPR = 54
manRun  = colorize_mario('/mnt/user-data/uploads/manRun.jpg')
manJump = colorize_mario('/mnt/user-data/uploads/manJump.jpg')

# Ground outline sprites (black line art, white bg)
gL_raw = load_sprite('/mnt/user-data/uploads/ground2L.jpg', (60,60))
gC_raw = load_sprite('/mnt/user-data/uploads/ground2C.jpg', (60,60))
gR_raw = load_sprite('/mnt/user-data/uploads/ground2R.jpg', (60,60))

# Obstacle (brick+? block)
obs_src  = Image.open('/mnt/user-data/uploads/1782199074490_image.png').convert('RGBA')
TILE = 36
brick_tile = obs_src.crop((0,0,80,88)).resize((TILE,TILE), Image.LANCZOS)
q_tile     = obs_src.crop((68,0,148,88)).resize((TILE,TILE), Image.LANCZOS)

def make_platform_img(nb, has_q=True):
    cols = nb*2 + (1 if has_q else 0)
    plat = Image.new('RGBA',(TILE*cols, TILE),(0,0,0,0))
    x=0
    for _ in range(nb):
        plat.paste(brick_tile,(x,0),brick_tile); x+=TILE
    if has_q:
        plat.paste(q_tile,(x,0),q_tile); x+=TILE
    for _ in range(nb):
        plat.paste(brick_tile,(x,0),brick_tile); x+=TILE
    return plat

# ============================================================
# BACKGROUND: bright Mario-like sky
# ============================================================
def make_sky():
    sky = Image.new('RGBA',(W,H),(92, 148, 252, 255))  # Mario blue
    d = ImageDraw.Draw(sky)
    # Clouds - white fluffy
    def cloud(cx, cy, sc=1.0):
        for ox,oy,rx,ry in [(0,0,28,18),(-22,6,20,14),(22,6,20,14),(-10,12,18,12),(10,12,18,12)]:
            d.ellipse([cx+ox*sc-rx*sc, cy+oy*sc-ry*sc,
                       cx+ox*sc+rx*sc, cy+oy*sc+ry*sc], fill=(255,255,255,240))
    cloud(120, 60, 1.2)
    cloud(310, 45, 1.0)
    cloud(500, 70, 1.3)
    cloud(80,  90, 0.8)
    cloud(420, 90, 0.9)
    return sky

sky_img = make_sky()

# ============================================================
# GROUND DRAWING: filled green+brown + outline on top
# ============================================================
GROUND_TOP = H - 70   # y where green ground surface begins
GROUND_H   = 70       # height of ground block

def draw_ground(canvas, scroll):
    d = ImageDraw.Draw(canvas)
    # Fill ground: green top band + brown body
    d.rectangle([0, GROUND_TOP, W, GROUND_TOP+12], fill=(76, 180, 48))   # bright green
    d.rectangle([0, GROUND_TOP+12, W, H],           fill=(168, 100, 48))  # brown body
    # Horizontal brick lines
    for y in range(GROUND_TOP+12, H, 20):
        d.line([0,y,W,y], fill=(140,80,35), width=1)
    # Vertical brick lines (offset every other row)
    row = 0
    for y in range(GROUND_TOP+12, H, 20):
        offset = (int(scroll) + row*30) % 60
        x = -offset
        while x < W:
            d.line([x,y,x,y+20], fill=(140,80,35), width=1)
            x += 60
        row += 1
    # Grass tufts on top using ground tile outline
    tw = 60
    x = -int(scroll) % tw - tw
    while x < W:
        canvas.paste(gC_raw, (x, GROUND_TOP-12), gC_raw)
        x += tw

def paste(canvas, sprite, x, y):
    ix,iy = int(x),int(y)
    sw,sh = sprite.size
    if ix>=W or iy>=H or ix+sw<=0 or iy+sh<=0: return
    canvas.paste(sprite,(ix,iy),sprite)

def txt(canvas, text, x, y, size=16, color=(255,255,255), bold=False, shadow=True):
    draw = ImageDraw.Draw(canvas)
    try:
        fn = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold \
             else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        font = ImageFont.truetype(fn, size)
    except:
        font = ImageFont.load_default()
    if shadow:
        draw.text((x+2,y+2), text, fill=(0,0,0,180), font=font)
    draw.text((x,y), text, fill=(*color,255), font=font)

def draw_coin_sprite(canvas, cx, cy, r=11, frame=0):
    d = ImageDraw.Draw(canvas)
    # Animated coin (squish effect)
    squish = abs(math.sin(frame*0.3))
    rw = max(4, int(r * squish))
    rh = r
    d.ellipse([cx-rw,cy-rh,cx+rw,cy+rh], fill=(255,200,0), outline=(220,130,0))
    if rw > 6:
        d.ellipse([cx-rw+3,cy-rh+3,cx+rw-3,cy+rh-3], fill=(255,240,120))

# ============================================================
# PHYSICS
# ============================================================
PLAYER_X  = 85
GROUND_Y  = GROUND_TOP - SPR   # player top-y when standing on ground
GRAVITY   = 1600.0
JUMP_VY   = -530.0
JUMP2_VY  = -420.0
SCROLL_V  = 270.0
MAX_JUMP  = int(JUMP_VY**2 / (2*GRAVITY))  # ~87px

class Platform:
    def __init__(self, x, y, nb, has_q, with_coins):
        self.x   = float(x)
        self.y   = float(y)
        self.img = make_platform_img(nb, has_q)
        self.w   = float(self.img.width)
        self.h   = float(TILE)
        self.nb  = nb
        self.coins = []
        if with_coins:
            # coins float above the ? block
            qx_center = nb * TILE + TILE//2
            for i in range(random.randint(1,4)):
                self.coins.append([qx_center - 15 + i*14, False, 0])

    def update(self, dt):
        self.x -= SCROLL_V * dt

    def alive(self):
        return self.x + self.w > -20

class Game:
    def __init__(self, level):
        self.level   = level
        self.py      = float(GROUND_Y)
        self.vy      = 0.0
        self.on_gnd  = True
        self.jcount  = 0
        self.plat_id = None
        self.scroll  = 0.0
        self.score   = 0
        self.coins   = 0
        self.plats   = []
        self.over    = False
        self.t       = 0.0
        self.frame   = 0
        self.next_sp = 1.2

    def jump(self, double=False):
        self.vy      = JUMP2_VY if double else JUMP_VY
        self.on_gnd  = False
        self.plat_id = None
        self.jcount  = 2 if double else 1

    def update(self, dt):
        if self.over: return
        self.t     += dt
        self.frame += 1
        self.scroll = (self.scroll + SCROLL_V*dt) % 60
        self.score += 1

        # ---- Spawn ----
        if self.t >= self.next_sp:
            nb   = random.randint(1,2)
            # Height: reachable by single jump, at various heights
            h_range = min(MAX_JUMP-15, 70)
            py   = GROUND_Y - random.randint(25, h_range)
            py   = max(30, py)
            wc   = (self.level >= 3)
            self.plats.append(Platform(W+20, py, nb, True, wc))
            self.next_sp = self.t + random.uniform(1.6, 2.6)

        for p in self.plats: p.update(dt)
        self.plats = [p for p in self.plats if p.alive()]

        # ---- AI jump ----
        for p in self.plats:
            d = p.x - (PLAYER_X + SPR)
            # Jump to reach platform
            if self.on_gnd and 50 < d < 150:
                self.jump()
            # Double jump if level 2+ and platform is higher
            if self.level>=2 and not self.on_gnd and self.jcount==1 and 20<d<90:
                need_h = GROUND_Y - p.y
                if need_h > 40:
                    self.jump(double=True)

        # ---- Physics ----
        prev_py = self.py
        if not self.on_gnd:
            self.vy += GRAVITY * dt
        self.py += self.vy * dt

        # Land on ground
        if self.py >= GROUND_Y:
            self.py     = float(GROUND_Y)
            self.vy     = 0.0
            self.on_gnd = True
            self.plat_id= None
            self.jcount = 0

        # Platform collisions
        landed = False
        for p in self.plats:
            px1 = PLAYER_X + 6;  px2 = PLAYER_X + SPR - 6
            feet_now  = self.py + SPR
            feet_prev = prev_py  + SPR
            ptop = p.y
            if (px2 > p.x+4 and px1 < p.x+p.w-4 and
                self.vy >= 0 and feet_prev <= ptop+6 and feet_now >= ptop-6):
                self.py      = ptop - SPR
                self.vy      = 0.0
                self.on_gnd  = True
                self.plat_id = id(p)
                self.jcount  = 0
                landed       = True
                break

        # Fall off platform edge
        if self.plat_id and not landed:
            on_it = False
            for p in self.plats:
                if id(p)==self.plat_id:
                    if PLAYER_X+6 < p.x+p.w and PLAYER_X+SPR-6 > p.x:
                        on_it = True
                    break
            if not on_it:
                self.on_gnd  = False
                self.plat_id = None
                if self.vy == 0: self.vy = 2.0

        # Side collision = game over (level 2+)
        if self.level >= 2:
            for p in self.plats:
                if id(p)==self.plat_id: continue
                px1=PLAYER_X+10; px2=PLAYER_X+SPR-10
                py1=self.py+8;   py2=self.py+SPR-4
                if px1<p.x+p.w and px2>p.x and py1<p.y+p.h and py2>p.y:
                    self.over = True

        # Collect coins
        if self.level >= 3:
            for p in self.plats:
                for c in p.coins:
                    if c[1]: continue
                    cx = p.x + c[0]
                    cy = p.y - 25
                    if (PLAYER_X < cx+12 and PLAYER_X+SPR > cx-12 and
                        self.py   < cy+12 and self.py+SPR  > cy-12):
                        c[1] = True
                        self.coins += 10

        # Animate coins
        for p in self.plats:
            for c in p.coins:
                c[2] += 1

    def render(self):
        canvas = sky_img.copy().convert('RGBA')
        draw_ground(canvas, self.scroll)

        # Platforms
        for p in self.plats:
            paste(canvas, p.img, p.x, p.y)
            # Coins above ? block
            if self.level >= 3:
                for c in p.coins:
                    if not c[1]:
                        cx = int(p.x + c[0])
                        cy = int(p.y) - 25
                        draw_coin_sprite(canvas, cx, cy, 11, c[2])

        # Player
        spr = manRun if self.on_gnd else manJump
        paste(canvas, spr, PLAYER_X, int(self.py))

        # ---- HUD ----
        d = ImageDraw.Draw(canvas)
        # Score box top-left
        d.rectangle([6,6,150,36], fill=(0,0,0,140))
        if self.level >= 3:
            total = self.score//10 + self.coins
            txt(canvas,f'SCORE  {total:05d}', 12, 11, 14,(255,255,255),True,False)
        else:
            txt(canvas,f'SCORE  {self.score//10:05d}', 12, 11, 14,(255,255,255),True,False)

        if self.level >= 3 and self.coins > 0:
            d.rectangle([6,40,130,62], fill=(0,0,0,120))
            txt(canvas,f'🪙 x{self.coins//10}  +{self.coins}pts', 12, 43, 12,(255,220,40),True,False)

        # Level badge top-right
        lvl_colors=[(80,255,80),(80,180,255),(255,220,40),(255,100,100)]
        lc = lvl_colors[self.level-1]
        d.rectangle([W-90,6,W-6,36], fill=(0,0,0,140))
        txt(canvas,f'LEVEL  {self.level}', W-84, 11, 14, lc, True, False)

        # Game Over
        if self.over:
            ov = Image.new('RGBA',(W,H),(0,0,0,170))
            canvas.alpha_composite(ov)
            txt(canvas,'GAME OVER', W//2-115, H//2-40, 38,(255,50,50),True)
            sc = self.score//10 + self.coins
            txt(canvas,f'SCORE: {sc}', W//2-65, H//2+15, 20,(255,255,100),True)

        return np.array(canvas.convert('RGB'))

# ============================================================
# RENDER VIDEO
# ============================================================
out = cv2.VideoWriter('/home/claude/gameplay_raw.mp4',
                      cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W,H))

sections = [
    (1,'LEVEL 1 - Run!',           8),
    (2,'LEVEL 2 - Jump & Dodge!',  8),
    (3,'LEVEL 3 - Collect Coins!', 8),
    (4,'LEVEL 4 - Full Challenge!',9),
]

for level, title, secs in sections:
    game = Game(level)
    for f in range(FPS*secs):
        game.update(1.0/FPS)
        frame_rgb = game.render()
        pil_f = Image.fromarray(frame_rgb).convert('RGBA')

        # Title card first 1.5s
        if f < FPS*1.5:
            alpha = min(1.0, f/(FPS*0.3))  # fade in
            ov = Image.new('RGBA',(W,H),(0,0,0,int(160*alpha)))
            pil_f.alpha_composite(ov)
            fc = [(80,255,80),(80,200,255),(255,220,40),(255,100,100)][level-1]
            txt(pil_f, title, W//2-len(title)*8, H//2-16, 26, fc, True)

        out.write(cv2.cvtColor(np.array(pil_f.convert('RGB')), cv2.COLOR_RGB2BGR))

out.release()
print(f"Done - {W}x{H} @{FPS}fps")
