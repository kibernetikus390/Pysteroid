import sys, math, random
from pathlib import Path
import pygame
from pygame.locals import *
from assets import Assets
import numpy as np

ASSETS = None
WINDOW_W = 920
WINDOW_H = 720
WINDOW_OUT = 30
FPS = 60
BLINK_SPEED = 8
GAMESTATE = {"title":0, "game":1, "exploding":2, "gameover":3, "pause":4}
g_gamestate = GAMESTATE["title"]
g_level = 0
# 背景
g_bg_pos        = {"x":0, "y":0}
BG_SCROLL_SPEED = {"x":1, "y":1}
# プレイヤー
PLAYER_SESPAWN_TIME = 3 * FPS
g_timer = 0
g_player_pos = {"x":WINDOW_W/2, "y":WINDOW_H/2}
g_player_angle = 0
g_player_life = 3
g_respawn_timer = -PLAYER_SESPAWN_TIME
g_player_velosity = {"x":0, "y":0}
CTRL_ROTATE_SPEED = 2.5
CTRL_MOVE_SPEED = 0.2
CTRL_VELOSITY_MAX = 10.0
CTRL_VELOSITY_DECADANCE = 0.99
BURNER_OFFSET = 30
SMOKE_OFFSET = 30
# 弾丸
MAX_BULLETS = 100
obj_bullets = [None]*MAX_BULLETS
BULLET_TYPE = {"player":0, "enemy1":1, "enemy2":2}
BULLET_OFFSET = 40
BULLET_SPEED_PLAYER = 10
BULLET_SPEED_ENEMY = 3
# 隕石
LVUP_RATE = 30*FPS
g_spawnrate = 3*FPS
MAX_ASTEROIDS = 100
obj_asteroids = [None]*MAX_ASTEROIDS
ASTEROID_HIT_RADIUS = 40
ASTEROID_HIT_RADIUS_SMALL = 25
ASTEROID_SIZE = {"big":1.5, "mid":1.0, "small":0.75}
ASTEROID_TYPE = {"big":0, "small":1, "enemyship1":2, "enemyship2":3}
ASTEROID_NUM_DEBRIS = {"big":3, "mid":2, "small":1}
FLY_TO_PLAYER = 4   # プレイヤーに向かって飛ぶ確立(0:100% ~ )
# エフェクト
MAX_EFFECTS = 30
obj_effects = [None]*MAX_EFFECTS
ANIMATION_COUNT = 3
EFFECT_EXPLOSION_FRAMES = 5
EFFECT_TYPE = {"explosion":0, "fire":1}
# ピックアップ
MAX_PICKUP = 10
obj_pickups = [None]*MAX_PICKUP
DIAMOND_DROP_RATE = 5
PICKUP_RADIUS = 50
DIAMOND_LIFE = 10 * FPS
DIAMOND_BLINK = 5 * FPS
# スコア
g_score = 0
SCORE_HIT_BIG = 100
SCORE_DIAMOND = 1000
# お金
g_money = 0
MONEY_DIAMOND = 1000

def draw_text(screen, text, x, y, color, font, anchor_center=True):
    """
    影付きの文字を描画する
    """
    surface = font.render(text, True, (0,0,0))
    if anchor_center:
        x -= surface.get_width()/2
        y -= surface.get_height()/2
    # 影を描画
    screen.blit(surface, [x+2,y+2])
    # 本体を描画
    surface = font.render(text, True, color)
    screen.blit(surface, [x, y])

def get_dis(x1, y1, x2, y2):
    """
    二点間の距離を取得
    """
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 )

def create_effect(x, y, type):
    for i in range(MAX_EFFECTS):
        if obj_effects[i] is None:
            obj_effects[i] = {"x":x, "y":y, "count":0, "type":type}
            return

def create_enemy(pos=None, new_size=None, new_type=ASTEROID_TYPE["big"]):
    """
    隕石を作成(単体)
    """
    global obj_asteroids
    x = y = size = 0
    for i in range(MAX_ASTEROIDS):
        if obj_asteroids[i] is None:
            spawn_place = random.randint(0,1)
            x = y = 0
            if spawn_place == 0:
                # 上下辺
                if pos is None:
                    x = random.randint(-WINDOW_OUT, WINDOW_W+WINDOW_OUT)
                    y = random.choice([random.randint(-WINDOW_OUT, WINDOW_OUT), random.randint(WINDOW_H-WINDOW_OUT, WINDOW_H+WINDOW_OUT)])
                else:
                    x, y = pos[0], pos[1]
            elif spawn_place == 1:
                # 左右辺
                if pos is None:
                    x = random.choice([random.randint(-WINDOW_OUT, WINDOW_OUT), random.randint(WINDOW_W-WINDOW_OUT, WINDOW_W+WINDOW_OUT)])
                    y = random.randint(-WINDOW_OUT, WINDOW_H+WINDOW_OUT)
                else:
                    x, y = pos[0], pos[1]
            # サイズを決定
            # デブリを作成する場合は親から受け継ぐ
            if new_type == ASTEROID_TYPE["enemyship1"]:
                size = 0.6
            elif new_type == ASTEROID_TYPE["enemyship2"]:
                size = 0.8
            else:
                if new_size is None:
                    size = ASTEROID_SIZE[random.choice(("big","mid","small"))]
                else:
                    size = new_size
            # 飛行角度を決定
            # 確立でプレイヤーに向かって飛ぶ
            if random.randint(0,FLY_TO_PLAYER) == 0:
                rv = math.degrees(math.atan2(-(g_player_pos["y"]-y), (g_player_pos["x"]-x) ))-90
            else:
                rv = random.randint(0,359)

            # 描画角度
            if new_type in (ASTEROID_TYPE["enemyship1"], ASTEROID_TYPE["enemyship2"]):
                r = rv
            else:
                r = random.randint(0,359)

            obj_asteroids[i] = {
                "x": x, 
                "y": y, 
                "r": r, 
                "rv": rv, 
                "s": size,
                "type": new_type,
                "timer": g_timer-random.randint(0,FPS)
                }
            break

def create_enemies():
    """
    隕石を作成
    """
    global g_spawnrate, g_level
    sec = g_timer / 60
    if g_level == 0:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            g_level += 1
            g_spawnrate = int(2*FPS)
        if g_timer%g_spawnrate == 0:
            create_enemy()
    elif g_level == 1:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            g_level += 1
            g_spawnrate = int(2*FPS)
        if g_timer%g_spawnrate == 0:
            rand = random.randint(0,3)
            if rand == 0:
                create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
            else:
                create_enemy()
    elif g_level == 2:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            g_level += 1
            g_spawnrate = int(1.75*FPS)
        if g_timer%g_spawnrate == 0:
            rand = random.randint(0,5)
            if rand == 0:
                create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
            elif rand == 1:
                create_enemy(new_type=ASTEROID_TYPE["enemyship2"])
            else:
                create_enemy()
    else:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            g_level += 1
            g_spawnrate = int(g_spawnrate*0.9)
        if g_timer%g_spawnrate == 0:
            rand = random.randint(0,5)
            if rand == 0:
                create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
            elif rand == 1:
                create_enemy(new_type=ASTEROID_TYPE["enemyship2"])
            else:
                create_enemy()
   
def destry_asteroid(index):
    # エフェクトを作成
    create_effect(obj_asteroids[index]["x"], obj_asteroids[index]["y"], type=EFFECT_TYPE["explosion"])
    ASSETS.play("rock")
    if obj_asteroids[index]["type"] == ASTEROID_TYPE["big"]:
        # デブリを作成
        size = obj_asteroids[index]["s"]
        if size == ASTEROID_SIZE["big"]:
            for i in range(2):
                pos = [obj_asteroids[index]["x"] + random.randint(-40,40), obj_asteroids[index]["y"] + random.randint(-40,40)]
                create_enemy(pos, ASTEROID_SIZE["mid"], ASTEROID_TYPE["big"])
        elif size == ASTEROID_SIZE["mid"]:
            if random.randint(0,1) == 0:
                for i in range(2):
                    pos = [obj_asteroids[index]["x"] + random.randint(-40,40), obj_asteroids[index]["y"] + random.randint(-40,40)]
                    create_enemy(pos, ASTEROID_SIZE["small"], ASTEROID_TYPE["big"])
            else:
                for i in range(3):
                    size = obj_asteroids[index]["s"]
                    pos = [obj_asteroids[index]["x"] + random.randint(-40,40), obj_asteroids[index]["y"] + random.randint(-40,40)]
                    create_enemy(pos, size, ASTEROID_TYPE["small"])
        elif size == ASTEROID_SIZE["small"]:
            for i in range(random.randint(2,3)):
                pos = [obj_asteroids[index]["x"] + random.randint(-40,40), obj_asteroids[index]["y"] + random.randint(-40,40)]
                size = obj_asteroids[index]["s"]
                create_enemy(pos, size, ASTEROID_TYPE["small"])
        # ダイアモンドを作成
        if random.randint(0,DIAMOND_DROP_RATE) == 0:
            for i in range(MAX_PICKUP):
                if obj_pickups[i] is None:
                    obj_pickups[i] = {"x":obj_asteroids[index]["x"], "y":obj_asteroids[index]["y"], "type":"diamond", "r":0, "s":1, "rv":random.randint(0,359), "timer":g_timer}
                    break
        obj_asteroids[index] = None
    else:
        obj_asteroids[index] = None

def shoot_bullet(type=BULLET_TYPE["player"], pos=None, angle=None):
    """
    弾を発射
    """
    global obj_bullets
    for i in range(MAX_BULLETS):
        if obj_bullets[i] is None:
            if type == BULLET_TYPE["player"]:
                bullet_x = g_player_pos["x"] - BULLET_OFFSET * math.sin(math.radians(g_player_angle))
                bullet_y = g_player_pos["y"] - BULLET_OFFSET * math.cos(math.radians(g_player_angle))
                angle = g_player_angle
                ASSETS.play("shot")
                size = 0.4
            else:
                bullet_x = pos[0] - BULLET_OFFSET * math.sin(math.radians(angle))
                bullet_y = pos[1] - BULLET_OFFSET * math.cos(math.radians(angle))
                ASSETS.play("shot2")
                size = 0.6
            obj_bullets[i] = {"x":bullet_x, "y":bullet_y, "r":angle, "s":size, "type":type, "timer":g_timer}
            
            break

def update_objects(screen):
    """
    オブジェクトの更新処理
    """
    global g_score, g_money
    # 敵の更新
    for i in range(MAX_ASTEROIDS):
        obj = obj_asteroids[i]
        if obj is not None:
            # 敵の移動
            obj["x"] -= 1 * math.sin(math.radians(obj["rv"]))
            obj["y"] -= 1 * math.cos(math.radians(obj["rv"]))
            if obj["x"] < -WINDOW_OUT:
                obj["x"] = WINDOW_W + WINDOW_OUT
            if WINDOW_W + WINDOW_OUT < obj["x"]:
                obj["x"] = -WINDOW_OUT
            if obj["y"] < -WINDOW_OUT:
                obj["y"] = WINDOW_H + WINDOW_OUT
            if WINDOW_H + WINDOW_OUT < obj["y"]:
                obj["y"] = -WINDOW_OUT
            # 敵の描画
            sprite = ASSETS.imgs_asteroid[obj["type"]]
            blit_rotate_center(
                screen, 
                sprite, 
                (obj["x"]-sprite.get_width()/2, obj["y"]-sprite.get_height()/2), 
                obj["r"], 
                obj["s"])
            # 敵船1
            if obj["type"] == ASTEROID_TYPE["enemyship1"] or obj["type"] == ASTEROID_TYPE["enemyship2"]:
                # 敵弾を発射
                if obj["type"] == ASTEROID_TYPE["enemyship2"]:
                    type = BULLET_TYPE["enemy2"]
                    r = math.degrees(math.atan2(-(g_player_pos["y"]-obj["y"]), (g_player_pos["x"]-obj["x"]) ))-90
                else:
                    type = BULLET_TYPE["enemy1"]
                    r = obj["r"]
                if (obj["timer"] - g_timer) % (3*FPS)  == 0:
                    shoot_bullet(type, (obj["x"], obj["y"]), r)
    # 弾
    for i in range(MAX_BULLETS):
        bullet = obj_bullets[i]
        if bullet is not None:
            draw = False
            type = bullet["type"]
            if type == BULLET_TYPE["player"]:
                speed = BULLET_SPEED_PLAYER
            else:
                speed = BULLET_SPEED_ENEMY
            # 移動
            bullet["x"] -= speed * math.sin(math.radians(bullet["r"]))
            bullet["y"] -= speed * math.cos(math.radians(bullet["r"]))
            # 画面外に行ったら消える
            if not -WINDOW_OUT <= bullet["x"] <= WINDOW_W + WINDOW_OUT or not -WINDOW_OUT <= bullet["y"] <= WINDOW_H + WINDOW_OUT:
                obj_bullets[i] = None
                continue
            if type == BULLET_TYPE["player"]:
                # プレイヤーの弾
                # 隕石との衝突判定
                for j in range(MAX_ASTEROIDS):
                    asteroid = obj_asteroids[j]
                    if asteroid is not None:
                        if asteroid["type"] == ASTEROID_TYPE["small"]:      
                            hit_radius = ASTEROID_HIT_RADIUS_SMALL     
                        else:      
                            hit_radius = ASTEROID_HIT_RADIUS
                        if (get_dis(asteroid["x"], asteroid["y"], bullet["x"], bullet["y"]) < hit_radius*obj_asteroids[j]["s"]):
                            destry_asteroid(j)
                            obj_bullets[i] = None
                            g_score += SCORE_HIT_BIG
                            break
                else:
                    draw = True
            else:
                # 敵の弾 プレイヤーとの衝突を判定
                if (get_dis(bullet["x"], bullet["y"], g_player_pos["x"], g_player_pos["y"]) < 20.0):
                    player_damage()
                    obj_bullets[i] = None
                    continue
                draw = True
            if draw:
                # 弾を描画
                sprite = ASSETS.img_bullet[type]
                x, y = bullet["x"]-sprite.get_width()/2, bullet["y"]-sprite.get_height()/2
                blit_rotate_center(screen, sprite, (x, y), bullet["r"], bullet["s"])
    # エフェクト
    for i in range(MAX_EFFECTS):
        effect = obj_effects[i]
        if effect is not None:
            effect["count"] += 1
            length = size = 0
            img = None
            index = max( 0, int(effect["count"] / ANIMATION_COUNT) )
            if effect["type"] == EFFECT_TYPE["explosion"]:
                length = len(ASSETS.imgs_explode)
                img = ASSETS.imgs_explode
                size = 1.0
            elif effect["type"] == EFFECT_TYPE["fire"]:
                length = len(ASSETS.imgs_fire)
                img = ASSETS.imgs_fire
                size = 0.7
            if int(effect["count"] / ANIMATION_COUNT) >= length:
                obj_effects[i] = None
                continue
            else:
                img_effect = pygame.transform.rotozoom(img[index], 0, size)
                screen.blit(img_effect, [effect["x"]-img_effect.get_width()/2, effect["y"]-img_effect.get_height()/2])
    # ピックアップの更新
    for i in range(MAX_PICKUP):
        pickup = obj_pickups[i]
        if pickup is not None:
            pickup["x"] -= 1 * math.sin(math.radians(pickup["rv"]))
            pickup["y"] -= 1 * math.cos(math.radians(pickup["rv"]))
            # 座標調整
            if pickup["x"] < - 0:
                # 左辺に接触
                pickup["x"] = 0
                pickup["rv"] *= -1
            if WINDOW_W < pickup["x"]:
                # 右辺に接触
                pickup["x"] = WINDOW_W
                pickup["rv"] *= -1
            if pickup["y"] < 0:
                # 上辺に接触
                pickup["y"] = 0
                if 0 <= pickup["rv"] <= 90:
                    pickup["rv"] += 90
                elif 270 <= pickup["rv"] <= 360:
                    pickup["rv"] -= 90
            if WINDOW_H < pickup["y"]:
                # 下辺に接触
                pickup["y"] = WINDOW_H
                if 90 <= pickup["rv"] < 180:
                    pickup["rv"] -= 90
                elif 180 < pickup["rv"] <= 270:
                    pickup["rv"] += 90
                elif pickup["rv"] == 180:
                    pickup["rv"] = 0
            if get_dis(pickup["x"], pickup["y"], g_player_pos["x"], g_player_pos["y"]) < PICKUP_RADIUS:
                # 拾う
                ASSETS.play("pickup")
                g_score += SCORE_DIAMOND
                g_money += MONEY_DIAMOND
                obj_pickups[i] = None
                continue
            # 描画
            passed_time = g_timer - pickup["timer"]
            if passed_time > DIAMOND_LIFE + DIAMOND_BLINK:
                # 消滅
                pickup = None
                continue
            elif passed_time > DIAMOND_LIFE:
                # 点滅
                if  0 <= (g_timer % BLINK_SPEED) <= BLINK_SPEED / 2:
                    continue
            #描画
            sprite =  ASSETS.imgs_diamond[int(g_timer % (len(ASSETS.imgs_diamond)* ANIMATION_COUNT) / ANIMATION_COUNT)]
            sprite = pygame.transform.rotozoom(sprite, 0, 1.25)
            screen.blit(sprite, [pickup["x"]-sprite.get_width()/2, pickup["y"]-sprite.get_height()/2])
            

def blit_rotate_center(surf, image, topleft, angle, scale=1.0):
    """
    画像中心を基準としたトランスフォームを適用して描画する
    """
    img = pygame.transform.rotozoom(image, angle, scale)
    new_rect = img.get_rect(center = image.get_rect(topleft = topleft).center)
    surf.blit(img, new_rect.topleft)

def move_starship(screen, key):
    """
    プレイヤーの操作
    """
    global g_player_pos, g_player_angle, g_player_velosity, g_player_life, g_respawn_timer
    if key[K_UP] or key[K_w]:
        # 加速
        g_player_velosity["x"] += CTRL_MOVE_SPEED * math.sin(math.radians(g_player_angle))
        g_player_velosity["y"] += CTRL_MOVE_SPEED * math.cos(math.radians(g_player_angle))
        # スラスター
        burner_x = g_player_pos["x"] + BURNER_OFFSET * math.sin(math.radians(g_player_angle))
        burner_y = g_player_pos["y"] + BURNER_OFFSET * math.cos(math.radians(g_player_angle))
        sprite = ASSETS.img_burner
        blit_rotate_center(screen, sprite, (burner_x-sprite.get_width()/2, burner_y-sprite.get_height()/2), g_player_angle, 0.7)
        if int(g_timer % 3) == 0:
            smoke_x = g_player_pos["x"] + SMOKE_OFFSET * math.sin(math.radians(g_player_angle))
            smoke_y = g_player_pos["y"] + SMOKE_OFFSET * math.cos(math.radians(g_player_angle))
            create_effect(smoke_x, smoke_y, EFFECT_TYPE["fire"])
    
    # 旋回
    if key[K_RIGHT] or key[K_d]:
        g_player_angle -= CTRL_ROTATE_SPEED
        #print("angle:"+str(g_player_angle))
    elif key[K_LEFT] or key[K_a]:
        g_player_angle += CTRL_ROTATE_SPEED
        #print("angle:"+str(g_player_angle))

    # 加速度の最大を制限
    if g_player_velosity["x"] ** 2 + g_player_velosity["y"] ** 2 > CTRL_VELOSITY_MAX ** 2:
        norm = np.linalg.norm([g_player_velosity["x"], g_player_velosity["y"]])
        g_player_velosity["x"] = g_player_velosity["x"]/norm*CTRL_VELOSITY_MAX
        g_player_velosity["y"] = g_player_velosity["y"]/norm*CTRL_VELOSITY_MAX

    # 座標を更新
    g_player_pos["x"] -= g_player_velosity["x"]
    g_player_pos["y"] -= g_player_velosity["y"]
    g_player_velosity["x"] *= CTRL_VELOSITY_DECADANCE
    g_player_velosity["y"] *= CTRL_VELOSITY_DECADANCE

    # 座標・角度を丸める
    pl_half_width = ASSETS.imgs_player_ship[0].get_width()/2
    pl_half_height = ASSETS.imgs_player_ship[0].get_height()/2
    x_center = g_player_pos["x"] - pl_half_width
    y_center = g_player_pos["y"] - pl_half_height
    if g_player_pos["x"] < 0:
        g_player_pos["x"] = 0
    elif WINDOW_W < x_center:
        g_player_pos["x"] = WINDOW_W + pl_half_width
    if g_player_pos["y"] < 0:
        g_player_pos["y"] = 0
    elif WINDOW_H < g_player_pos["y"]:
        g_player_pos["y"] = WINDOW_H
    if abs(g_player_angle) > 360:
        g_player_angle %= 360
    
    # 船と敵との衝突判定
    for j in range(MAX_ASTEROIDS):
        if obj_asteroids[j] is not None and (get_dis(obj_asteroids[j]["x"], obj_asteroids[j]["y"], g_player_pos["x"], g_player_pos["y"]) < ASTEROID_HIT_RADIUS*obj_asteroids[j]["s"]):                    
            if g_timer - g_respawn_timer > PLAYER_SESPAWN_TIME:
                player_damage()
                destry_asteroid(j)

def player_damage():
    global g_player_life, g_respawn_timer
    ASSETS.play("rock")
    create_effect(g_player_pos["x"], g_player_pos["y"], EFFECT_TYPE["explosion"])
    g_player_life -= 1
    g_respawn_timer = g_timer

def main():
    global g_timer, g_respawn_timer, g_level, g_player_velosity, g_score, g_money, g_bg_pos, ASSETS, g_gamestate, g_player_pos, g_player_angle, g_player_life
    global obj_bullets, obj_asteroids, obj_effects, obj_pickups
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Pysteroid")
    screen = pygame.display.set_mode((960, 720))
    clock = pygame.time.Clock()
    ASSETS = Assets(pygame)
    fnt_m = pygame.font.SysFont("monospace", 40)
    fnt_s = pygame.font.SysFont("monospace", 30)
    fnt_ss = pygame.font.SysFont("Arial", 16)
    fnt_l = pygame.font.Font(None, 120)
    ASSETS.play_main_bgm()

    fullscreen = False
    timer_pause = 0
    while True:
        if g_gamestate == GAMESTATE["pause"]:
            timer_pause += 1
        else:
            g_timer += 1
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                # F1キー
                if event.key == K_F1:
                    if fullscreen:
                        fullscreen = False
                        screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
                    else:
                        fullscreen = True
                        screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), FULLSCREEN)
                # ESCキー
                if event.key == K_ESCAPE:
                    if g_gamestate == GAMESTATE["title"]:
                        pygame.quit()
                        sys.exit()
                    elif g_gamestate == GAMESTATE["pause"]:
                        g_gamestate = GAMESTATE["title"]
                    elif g_gamestate == GAMESTATE["game"]:
                        timer_pause = 0
                        g_gamestate = GAMESTATE["pause"]
                # SPACEキー
                if event.key == K_SPACE:
                    if g_gamestate == GAMESTATE["game"]:
                        shoot_bullet()
                    elif g_gamestate == GAMESTATE["pause"]:
                        g_gamestate = GAMESTATE["game"]
            if event.type == KEYUP:
                if event.key == K_SPACE:
                    if g_gamestate == GAMESTATE["title"]:
                        g_timer = 0
                        g_level = 0
                        g_score = 0
                        g_money = 0
                        timer_pause = 0
                        g_spawnrate = 2*FPS
                        g_player_pos = {"x":WINDOW_W/2, "y":WINDOW_H/2}
                        g_player_velosity = {"x":0, "y":0}
                        g_player_angle = 0
                        g_player_life = 3
                        g_respawn_timer = -PLAYER_SESPAWN_TIME
                        obj_bullets = [None]*MAX_BULLETS
                        obj_asteroids = [None]*MAX_ASTEROIDS
                        obj_effects = [None]*MAX_EFFECTS
                        obj_pickups = [None]*MAX_PICKUP
                        g_gamestate = GAMESTATE["game"]
                    elif g_gamestate == GAMESTATE["gameover"]:
                        g_timer = 0
                        g_gamestate = GAMESTATE["title"]
        # 背景のスクロール
        g_bg_pos["x"] = (g_bg_pos["x"] + BG_SCROLL_SPEED["x"]) % WINDOW_W
        g_bg_pos["y"] = (g_bg_pos["y"] + BG_SCROLL_SPEED["y"]) % WINDOW_H
        screen.blit(ASSETS.img_bg, [g_bg_pos["x"] - WINDOW_W, g_bg_pos["y"] - WINDOW_H])
        screen.blit(ASSETS.img_bg, [g_bg_pos["x"] - WINDOW_W, g_bg_pos["y"]])
        screen.blit(ASSETS.img_bg, [g_bg_pos["x"], g_bg_pos["y"] - WINDOW_H])
        screen.blit(ASSETS.img_bg, [g_bg_pos["x"], g_bg_pos["y"]])

        # キー入力
        key = pygame.key.get_pressed()

        if g_gamestate == GAMESTATE["title"]:
            # タイトルの描画
            screen.blit(ASSETS.img_title, [WINDOW_W/2-ASSETS.img_title.get_width()/2, WINDOW_H/2-ASSETS.img_title.get_height()/2])
            draw_text(screen, "[ESC] pause / quit", WINDOW_W-150, WINDOW_H-30, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[F1] Fullscreen", WINDOW_W-150, WINDOW_H-60, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[SPACE] Fire", WINDOW_W-150, WINDOW_H-90, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[WAD,Arrowkey] Ship ctrl", WINDOW_W-150, WINDOW_H-120, (255,255,255), fnt_ss, anchor_center=False)
            if blink_timer(5):
                draw_text(screen, "Press [SPACE] to start", WINDOW_W/2 + 20, WINDOW_H/2+200, (255,255,255), fnt_m)
        if g_gamestate == GAMESTATE["game"]:
            if g_player_life < 0:
                g_timer = 0
                g_gamestate = GAMESTATE["exploding"]
            else:
                move_starship(screen, key)
                # 隕石を作成
                create_enemies()
                # オブジェクトのアップデートと描画
                update_objects(screen)
                # プレイヤーの描画
                if g_timer - g_respawn_timer < PLAYER_SESPAWN_TIME and blink_timer():
                    pass
                else:
                    sprite = ASSETS.imgs_player_ship[0]
                    blit_rotate_center(screen, sprite, (g_player_pos["x"] - sprite.get_width()/2, g_player_pos["y"] - sprite.get_height()/2), g_player_angle, 0.5)
                # UIの描画
                draw_text(screen, "SCORE:{:09}".format(g_score), 150, 30, (255,255,255), fnt_s)
                # draw_text(screen, "MONEY:{:09}".format(g_money), 150, 60, (255,255,255), fnt_s)
                img_rotozoom = pygame.transform.rotozoom(ASSETS.imgs_player_ship[0], 0, 0.4)
                if g_player_life > 0:
                    for i in range(g_player_life):
                        x = 30 + 50 * i
                        y = 60
                        screen.blit(img_rotozoom, [x, y])
        if g_gamestate == GAMESTATE["exploding"]:
            # 爆発
            # オブジェクトのアップデートと描画
            update_objects(screen)
            if g_timer % 10 == 0:
                ASSETS.play("rock")
                create_effect(g_player_pos["x"]+random.randint(-40,40), g_player_pos["y"]+random.randint(-40,40), EFFECT_TYPE["explosion"])
            # プレイヤーの描画
            if g_timer - g_respawn_timer < PLAYER_SESPAWN_TIME and blink_timer():
                pass
            else:
                sprite = ASSETS.imgs_player_ship[0]
                blit_rotate_center(screen, sprite, (g_player_pos["x"] - sprite.get_width()/2, g_player_pos["y"] - sprite.get_height()/2), g_player_angle, 0.5)
            # UIの描画
            draw_text(screen, "SCORE:{:09}".format(g_score), 150, 30, (255,255,255), fnt_s)
            img_rotozoom = pygame.transform.rotozoom(ASSETS.imgs_player_ship[0], 0, 0.4)
            if g_timer > 4*FPS:
                timer = 0
                g_gamestate = GAMESTATE["gameover"]
        if g_gamestate == GAMESTATE["gameover"]:
            # ゲームオーバー
            screen.blit(ASSETS.img_gameover, [WINDOW_W/2-ASSETS.img_gameover.get_width()/2, WINDOW_H/2-ASSETS.img_gameover.get_height()/2])
            draw_text(screen, "SCORE:{}".format(g_score), WINDOW_W/2 + 20, WINDOW_H/2+100, (255,255,255), fnt_m)
            if blink_timer(5):
                draw_text(screen, "Press [SPACE] to continue", WINDOW_W/2 + 20, WINDOW_H/2+200, (255,255,255), fnt_m)
        if g_gamestate == GAMESTATE["pause"]:
            # ポーズ
            draw_text(screen, "PAUSE", WINDOW_W/2 + 20, WINDOW_H/2, (255,255,255), fnt_l)
            if blink_timer(5, timer_pause):
                draw_text(screen, "Press [ESC] to title", WINDOW_W/2 + 20, WINDOW_H/2+200, (255,255,255), fnt_m)
                draw_text(screen, "Press [SPACE] to continue", WINDOW_W/2 + 20, WINDOW_H/2+250, (255,255,255), fnt_m)
        pygame.display.update()
        clock.tick(FPS)

def blink_timer(multiplier = 1, timer=None):
    """
    一定フレームおきに真偽を入れ替える
    点滅に使う
    """
    if timer is None:
        timer = g_timer
    return 0 <= (timer % (BLINK_SPEED * multiplier)) <= (BLINK_SPEED*multiplier)/2

if __name__ == "__main__":
    main()