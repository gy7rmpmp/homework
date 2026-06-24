import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

CW, CH = 1200, 600
FPS    = 30

def load(path, size=None):
    img = Image.open(path).convert('RGBA')
    if size: img = img.resize(size, Image.LANCZOS)
    return img

def paste(canvas, sprite, x, y):
    ix, iy = int(x), int(y)
    sw, sh = sprite.size
    sx,sy = max(0,-ix), max(0,-iy)
    ex,ey = min(sw,CW-ix), min(sh,CH-iy)
    if ex>sx and ey>sy:
        canvas.paste(sprite.crop((sx,sy,ex,ey)), (ix+sx, iy+sy), sprite.crop((sx,sy,ex,ey)))

def txt(canvas, text, x, y, size=20, color=(255,255,255), bold=True):
    d = ImageDraw.Draw(canvas)
    try:
        fn = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold \
             else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        font = ImageFont.truetype(fn, size)
    except:
        font = ImageFont.load_default()
    d.text((x+2,y+2), text, fill=(0,0,0,180), font=font)
    d.text((x,y),   text, fill=(*color,255), font=font)

# ---- Assets ----
circleA = load('/mnt/user-data/uploads/circleA.jpg', (80,80))
circleB = load('/mnt/user-data/uploads/circleB.jpg', (80,80))
pA  = load('/mnt/user-data/uploads/playerA.jpg',  (200,400))
pAW = load('/mnt/user-data/uploads/playerAW.jpg', (200,400))
pAB = load('/mnt/user-data/uploads/playerAB.jpg', (200,400))
pAT = load('/mnt/user-data/uploads/playerAT.jpg', (200,400))
pB  = load('/mnt/user-data/uploads/playerB.jpg',  (200,400))
pBW = load('/mnt/user-data/uploads/playerBW.jpg', (200,400))
pBB = load('/mnt/user-data/uploads/playerBB.jpg', (200,400))
pBT = load('/mnt/user-data/uploads/playerBT.jpg', (200,400))

# ---- Board ----
BSIZE  = 9
MARGIN = 45
CELL   = (560 - 2*MARGIN) // (BSIZE-1)   # ~58

def gxy(r, c):
    return MARGIN + c*CELL, MARGIN + r*CELL

def draw_board(canvas, pieces, highlight=None, last=None):
    """
    pieces: list of (r, c, player)  -- drawn IN ORDER, NO overwrite checking here
    We guarantee caller never passes duplicates
    """
    d = ImageDraw.Draw(canvas)
    # Board background
    d.rectangle([0,0,600,600], fill=(45,160,45))
    d.rectangle([28,28,572,572], fill=(205,165,80))
    # Grid
    for i in range(BSIZE):
        x,y   = gxy(0,i); x2,y2 = gxy(BSIZE-1,i)
        d.line([x,y,x2,y2], fill=(130,90,40), width=2)
        x,y   = gxy(i,0); x2,y2 = gxy(i,BSIZE-1)
        d.line([x,y,x2,y2], fill=(130,90,40), width=2)
    # Star points
    for sr,sc in [(4,4),(2,2),(2,6),(6,2),(6,6)]:
        px,py = gxy(sr,sc)
        d.ellipse([px-5,py-5,px+5,py+5], fill=(90,55,25))

    # Draw all pieces
    R = CELL//2 - 3
    for (r,c,player) in pieces:
        px,py = gxy(r,c)
        if player == 1:   # BLACK
            d.ellipse([px-R,py-R,px+R,py+R], fill=(15,15,15), outline=(60,60,60))
            d.ellipse([px-R+4,py-R+4,px-R+10,py-R+10], fill=(70,70,70))
        else:             # WHITE
            d.ellipse([px-R,py-R,px+R,py+R], fill=(245,245,245), outline=(160,160,160))
            d.ellipse([px-R+4,py-R+4,px-R+10,py-R+10], fill=(255,255,255))

    # Highlight winning 5
    if highlight:
        for (r,c) in highlight:
            px,py = gxy(r,c)
            d.ellipse([px-R-4,py-R-4,px+R+4,py+R+4], outline=(255,40,40), width=3)

    # Last move red dot
    if last:
        r,c = last
        px,py = gxy(r,c)
        d.ellipse([px-5,py-5,px+5,py+5], fill=(255,0,0))

def draw_right(canvas, turn, sa, sb, log, scoreA, scoreB, bubble=None):
    d = ImageDraw.Draw(canvas)
    d.rectangle([600,0,1200,600], fill=(25,25,45))

    imgs = {'A':{'n':pA,'w':pAW,'l':pAB,'t':pAT},
            'B':{'n':pB,'w':pBW,'l':pBB,'t':pBT}}
    paste(canvas, imgs['A'][sa], 600, 95)
    paste(canvas, imgs['B'][sb], 1000, 95)
    paste(canvas, circleA, 630, 8)
    paste(canvas, circleB, 1090, 8)

    txt(canvas, 'VS', 865, 240, 52, (255,210,40))
    txt(canvas, str(scoreA), 690, 520, 38, (255,255,80))
    txt(canvas, str(scoreB), 1095, 520, 38, (255,255,80))
    txt(canvas, 'Score', 688, 560, 13, (180,180,180), False)
    txt(canvas, 'Score', 1090, 560, 13, (180,180,180), False)

    if turn == 1:
        d.rectangle([596,0,605,600], fill=(40,220,40))
        txt(canvas, '▶ YOUR TURN', 612, 570, 13, (40,255,40))
    else:
        d.rectangle([1195,0,1200,600], fill=(40,220,40))
        txt(canvas, 'YOUR TURN ◀', 975, 570, 13, (40,255,40))

    txt(canvas, 'Move Log:', 798, 4, 13, (160,160,160), False)
    for i,(pl,r,c,w) in enumerate(log[-7:]):
        col = (160,210,255) if pl==1 else (255,200,160)
        txt(canvas, f'{"A" if pl==1 else "B"}→({r+1},{c+1}) "{w}"',
            788, 20+i*14, 11, col, False)

    if bubble:
        pl, w = bubble
        bx = 618 if pl==1 else 1008
        by = 75
        bw, bh = 175, 48
        d.rounded_rectangle([bx,by,bx+bw,by+bh], radius=12, fill=(255,255,210,235))
        d.rounded_rectangle([bx,by,bx+bw,by+bh], radius=12, outline=(190,170,90), width=2)
        tx = bx+bw//2
        d.polygon([(tx-8,by+bh),(tx,by+bh+14),(tx+8,by+bh)], fill=(255,255,210,235))
        txt(canvas, f'"{w}"', bx+12, by+12, 17, (40,40,40))

# ============================================================
# GAME LOGIC - pieces stored as list, never overwrite
# ============================================================
def check_five(pieces, r, c, player):
    pos = {(rr,cc) for rr,cc,pp in pieces if pp==player}
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    for dr,dc in dirs:
        cells = [(r,c)]
        for sign in [1,-1]:
            nr,nc = r+dr*sign, c+dc*sign
            while (nr,nc) in pos:
                cells.append((nr,nc))
                nr+=dr*sign; nc+=dc*sign
        if len(cells)>=5:
            return cells
    return None

# ---- Scripted moves (verified no overlaps) ----
# A wins diagonally; B tries to block
moves = [
    (1,4,4,'五五'), (2,4,5,'五六'),
    (1,3,3,'四四'), (2,5,5,'六六'),
    (1,2,2,'三三'), (2,6,5,'七六'),
    (1,5,5,'六六'), # wait (5,5) free? yes  -- but (4,5) is B, (5,5) free
    # Actually let's be super careful:
]

# Build from scratch, checking uniqueness
raw = [
    (1,4,4,'五五'),
    (2,3,5,'四六'),
    (1,3,3,'四四'),
    (2,2,5,'三六'),
    (1,2,2,'三三'),
    (2,1,5,'二六'),
    (1,5,5,'六六'),
    (2,6,5,'七六'),
    (1,6,6,'七七'),  # A wins diagonal: (2,2)(3,3)(4,4)(5,5)(6,6)
]

# Verify
used = set()
ok = True
for pl,r,c,w in raw:
    if (r,c) in used:
        print(f"DUPLICATE: ({r},{c})")
        ok = False
    used.add((r,c))
print("Moves OK:", ok)

# ---- Render ----
out = cv2.VideoWriter('/home/claude/gomoku_raw2.mp4',
                      cv2.VideoWriter_fourcc(*'mp4v'), FPS, (CW,CH))

def add_frames(canvas, n):
    arr = cv2.cvtColor(np.array(canvas.convert('RGB')), cv2.COLOR_RGB2BGR)
    for _ in range(n):
        out.write(arr)

pieces = []   # list of (r, c, player)
log    = []
scoreA = scoreB = 0

# Intro
canvas = Image.new('RGBA',(CW,CH))
draw_board(canvas, pieces)
draw_right(canvas, 1, 'n','n', log, scoreA, scoreB)
add_frames(canvas, FPS*2)

for pl,r,c,word in raw:
    turn_next = 2 if pl==1 else 1

    # Speech bubble
    canvas = Image.new('RGBA',(CW,CH))
    draw_board(canvas, pieces, last=(r,c) if pieces else None)
    draw_right(canvas, pl, 'n','n', log, scoreA, scoreB, (pl,word))
    add_frames(canvas, FPS)

    # Place piece (verify not duplicate)
    assert all(not(rr==r and cc==c) for rr,cc,pp in pieces), f"DUPE ({r},{c})!"
    pieces.append((r,c,pl))
    log.append((pl,r,c,word))

    # Check win
    five = check_five(pieces, r, c, pl)
    if five:
        if pl==1: scoreA+=1; sa,sb='w','l'
        else:     scoreB+=1; sa,sb='l','w'
        canvas = Image.new('RGBA',(CW,CH))
        draw_board(canvas, pieces, highlight=five, last=(r,c))
        draw_right(canvas, pl, sa,sb, log, scoreA, scoreB)
        add_frames(canvas, FPS*4)
        # Congrats
        d = ImageDraw.Draw(canvas)
        d.rectangle([150,200,850,400], fill=(0,0,0,190))
        txt(canvas, f'Player {"A" if pl==1 else "B"} Wins! 🎉', 170,220,42,(255,220,50))
        txt(canvas, '語音五子棋 - Voice Gomoku', 200,300,20,(180,255,180),False)
        add_frames(canvas, FPS*3)
        break
    else:
        canvas = Image.new('RGBA',(CW,CH))
        draw_board(canvas, pieces, last=(r,c))
        draw_right(canvas, turn_next, 'n','n', log, scoreA, scoreB)
        add_frames(canvas, int(FPS*0.9))

out.release()
print("Done!")
