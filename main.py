import sys, math, random
from pathlib import Path
import pygame
from pygame.locals import *
from assets import Assets
import numpy as np

DEBUG_START_LEVEL = 0

ASSETS = None
WINDOW_W = 920
WINDOW_H = 720
WINDOW_OUT = 50
FPS = 60
BLINK_SPEED = 8
GAMESTATE = {"title":0, "game":1, "exploding":2, "gameover":3, "pause":4}
g_gamestate = GAMESTATE["title"]
g_level = DEBUG_START_LEVEL
# 背景
g_bg_pos        = {"x":0, "y":0}
BG_SCROLL_SPEED = {"x":1, "y":1}
# プレイヤー
PLAYER_SESPAWN_TIME = 3 * FPS
g_timer = 0
g_timer_ui = 0
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
BULLET_TYPE = {"player":0, "enemy1":1, "enemy2":2, "player_piercing":3, "enemy_missile":4}
BULLET_OFFSET = 40
BULLET_SPEED_PLAYER = 10
BULLET_SPEED_ENEMY_INTERCEPTOR = 3
BULLET_SPEED_ENEMY_FIGHTER = 5
BULLET_SPEED_ELITE_FIGHTER = 4
MISSILE_ROTATE_SPEED = 1
MISSILE_SPEED = 5
# 隕石・敵機
LVUP_RATE = 20*FPS
g_spawnrate = 3*FPS
MAX_ASTEROIDS = 100
obj_asteroids = [None]*MAX_ASTEROIDS
ASTEROID_HIT_RADIUS = 40
ASTEROID_HIT_RADIUS_SMALL = 25
ASTEROID_SIZE = {"big":1.5, "mid":1.0, "small":0.75}
ASTEROID_TYPE = {"big":0, "small":1, "enemyship1":2, "enemyship2":3, "enemy_elite_fighter":4, "enemy_bomber":5}
ASTEROID_NUM_DEBRIS = {"big":3, "mid":2, "small":1}
FLY_TO_PLAYER = 4   # プレイヤーに向かって飛ぶ確立(0:100% ~ )
ENEMY_IMMU_TIMER = 0.25 * FPS # シールドを持つ敵の無敵時間
SPEED_ENEMY_INTERCEPTOR = 2
SPEED_ENEMY_FIGHTER = 2
SPEED_ENEMY_ELITE_FIGHTER = 3
SPEED_ENEMY_BOMBER = 1.5
SHIELD_ENEMY_ELITE_FIGHTER = 3
SHIELD_ENEMY_BOMBER = 3
FIRERATE_ENEMY_INTERCEPTOR = 2*FPS
FIRERATE_ENEMY_FIGHTER = 3*FPS
FIRERATE_ENEMY_ELITE_FIGHTER = 4*FPS
FIRERATE_ENEMY_BOMBER = 3*FPS
TURNRATE_ENEMY_ELITE_FIGHTER = 3*FPS
TURNRATE_ENEMY_BOMBER = 3*FPS
# エフェクト
MAX_EFFECTS = 50
obj_effects = [None]*MAX_EFFECTS
ANIMATION_COUNT = 3
EFFECT_EXPLOSION_FRAMES = 5
EFFECT_TYPE = {"explosion":0, "fire":1, "missile_explosion":2, "pl_bomb":3, "flash":4}
# ピックアップ
MAX_PICKUP = 20
PICKUP_TYPE = {"diamond":100}
POWERUP_TYPE = {"three_shot":0, "piercing_shot":1, "auto_shot":2}
POWERUP_NUM = 3
g_player_pickup_effects = [0]*POWERUP_NUM
obj_pickups = [None]*MAX_PICKUP
DROP_RATE_BIG = 7
DROP_RATE_SMALL = 14
DROP_RATE_INTERSEPTOR = 6
DROP_RATE_FIGHTER     = 4
DROP_RATE_ELITE       = 3
PICKUP_RADIUS = 50
DIAMOND_LIFE = 10 * FPS
DIAMOND_BLINK = 5 * FPS
POWERUP_DURATION = 10 * FPS
# スコア
g_score = 0
g_previous_frame_score = 0
SCORE_ASTEROID_SMALL = 50
SCORE_ASTEROID_BIG = 100
SCORE_ENEMY_INTERSEPTOR = 100
SCORE_ENEMY_FIGHTER = 200
SCORE_ENEMY_ELITE_FIGHTER = 2000
SCORE_ENEMY_BOMBER = 2000
SCORE_DIAMOND = 1000
SCORE_BONUS_PICKUP = 10000
SCORE_BONUS_1UP = 50000
# お金
g_money = 0
MONEY_DIAMOND = 1000

# メッセージ
g_message_timer = 0
g_message = ""
g_pickup_msg = ""
g_pickup_msg_timer = 0
g_pickup_pos = {"x":0,"y":0}

# フォント
fnt_m = None
fnt_s = None
fnt_ss = None
fnt_l = None

# ボム
g_bomb_max = 300
g_bomb_energy = 100
g_bomb_heal_ratio = 1 / FPS
BOMB_COST = 100
BOMB_CHARGE_DIAMOND = 5

def init_bomb():
    """
    ボムを初期化
    """
    global g_bomb_energy
    g_bomb_energy = BOMB_COST
def is_bomb_ready():
    """
    ボムが使用可能
    """
    return int(g_bomb_energy) >= BOMB_COST

def delete_bullets(remain_player_bullet=True):
    """
    弾を消去
    """
    for i in range(MAX_BULLETS):
        if obj_bullets[i] is None: continue
        if remain_player_bullet and obj_bullets[i]["type"] == BULLET_TYPE["player"]: continue
        obj_bullets[i] = None

def fire_bomb():
    """
    ボムを使用
    """
    global g_bomb_energy, g_respawn_timer
    g_bomb_energy -= BOMB_COST
    create_effect(0,0, type=EFFECT_TYPE["flash"])
    create_effect(g_player_pos["x"],g_player_pos["y"], type=EFFECT_TYPE["pl_bomb"])
    ASSETS.play("explosion")
    delete_bullets()
    g_respawn_timer = g_timer
    #全オブジェクトにダメージ
    for i in range(MAX_ASTEROIDS):
        if obj_asteroids[i] is not None:
            # 大岩は方向を変えるだけ
            if obj_asteroids[i]["type"] == ASTEROID_TYPE["big"]:
                obj_asteroids[i]["rv"] = get_target_degree(obj_asteroids[i]["x"], obj_asteroids[i]["y"])-180
                continue
            # ダメージ
            destry_asteroid(i, playsound=False)
            # バリアを消去
            if obj_asteroids[i] is not None:
                obj_asteroids[i]["shield"] = 0
def charge_bomb(value = g_bomb_heal_ratio):
    """
    ボムをチャージ
    """
    global g_bomb_energy
    g_bomb_energy += + value
    if g_bomb_max <= g_bomb_energy: g_bomb_energy = g_bomb_max
               

def score_bonus():
    """
    スコアボーナス
    """
    global g_previous_frame_score, g_player_life
    if g_previous_frame_score % SCORE_BONUS_PICKUP > g_score % SCORE_BONUS_PICKUP:
        create_type = random.choice([POWERUP_TYPE["three_shot"], POWERUP_TYPE["piercing_shot"],POWERUP_TYPE["auto_shot"]])
        create_pickup(obj_pickups, create_type, random.randint(0, WINDOW_W), random.randint(0, WINDOW_H))   
    if g_previous_frame_score % SCORE_BONUS_1UP > g_score % SCORE_BONUS_1UP:
        g_player_life += 1
        make_message("1up!")
    g_previous_frame_score = g_score    

def is_exist(type, return_how_many=False):
    """
    敵が存在するか
    """
    counter = 0
    for i in range(MAX_ASTEROIDS):
        if obj_asteroids[i] is not None:
            if obj_asteroids[i]["type"] == type:
                if return_how_many:
                    counter += 1
                else:
                    return True
    if return_how_many:
        return counter
    else:
        return False 

def explode_missile(index):
    """
    敵ミサイルの爆発
    """
    if obj_bullets[index] is None: return
    create_effect(obj_bullets[index]["x"], obj_bullets[index]["y"], EFFECT_TYPE["missile_explosion"])
    ASSETS.play("explosion")
    obj_bullets[index] = None
def clear_message():
    """
    メッセージを消去
    """
    global g_message, g_message_timer
    global g_pickup_msg, g_pickup_msg_timer
    g_message_timer = 0
    g_pickup_msg_timer = 0
    g_message = ""
    g_pickup_msg = ""
def make_message(msg):
    """
    メッセージを作成
    """
    global g_message, g_message_timer
    g_message_timer = g_timer + 2*FPS
    g_message = msg
def make_pickup_message(msg):
    """
    メッセージを作成(ピックアップ)
    """
    global g_pickup_msg, g_pickup_msg_timer, g_pickup_pos
    g_pickup_msg = msg
    g_pickup_msg_timer = g_timer
    g_pickup_pos = {"x":g_player_pos["x"],"y":g_player_pos["y"]-20}

def player_pickup(type):
    """
    パワーアップ
    """
    if type == POWERUP_TYPE["three_shot"]:
        make_pickup_message("Spread Shot")
    elif type == POWERUP_TYPE["piercing_shot"]:
        make_pickup_message("Piercing Shot")
    elif type == POWERUP_TYPE["auto_shot"]:
        make_pickup_message("Full-Auto Shot")
    g_player_pickup_effects[type] += POWERUP_DURATION 

def player_upgrade_available(pickup_type):
    """
    パワーアップの影響化であるか
    """
    return 0 < g_player_pickup_effects[pickup_type]

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


def create_effect(x, y, type, size=1.0):
    """
    エフェクトを作成
    """
    for i in range(MAX_EFFECTS):
        if obj_effects[i] is None:
            obj_effects[i] = {"x":x, "y":y, "count":0, "type":type, "s":size}
            return

def create_enemy(pos=None, new_size=None, new_type=ASTEROID_TYPE["big"]):
    """
    隕石を作成(単体)
    x,y 座標
    rv  進行方向(deg)
    r   描画方向(deg)
    rot_speed   回転速度
    s   スケール
    type    種類
    timer   作成された時間
    """
    global obj_asteroids
    for i in range(MAX_ASTEROIDS):
        if obj_asteroids[i] is None:
            if pos is not None:
                x, y = pos[0], pos[1]
                rv = random.randint(0,359)
            else:
                if random.choice((False,True)):
                    x = random.randint(0, WINDOW_W)
                    if random.choice((False,True)):
                        # 上端
                        y = random.randint(-WINDOW_OUT, 0)
                        rv = random.randint(150,210)
                    else:
                        # 下端
                        y = random.randint(WINDOW_H, WINDOW_H+WINDOW_OUT)
                        rv = random.randint(-30,30)
                else:
                    y = random.randint(0, WINDOW_H)
                    if random.choice((False,True)):
                        # 左辺
                        x = random.randint(-WINDOW_OUT, 0)
                        rv = random.randint(-120,-60)
                    else:
                        # 右辺
                        x = random.randint(WINDOW_W, WINDOW_W+WINDOW_OUT)
                        rv = random.randint(60,120)
                    
            # 確立でプレイヤーに向かって飛ぶ
            if random.randint(0,FLY_TO_PLAYER) == 0:
                rv = get_target_degree(x,y)

            # サイズを決定
            # デブリを作成する場合は親から受け継ぐ
            if new_type == ASTEROID_TYPE["enemyship1"]:
                size = 0.6
            elif new_type == ASTEROID_TYPE["enemyship2"]:
                size = 0.8
            elif new_type == ASTEROID_TYPE["enemy_elite_fighter"]:
                size = 1.0
            elif new_type == ASTEROID_TYPE["enemy_bomber"]:
                size = 1.0
            else:
                if new_size is None:
                    size = ASTEROID_SIZE[random.choice(("big","mid","small"))]
                else:
                    size = new_size

            # 描画角度
            if new_type in (ASTEROID_TYPE["enemyship1"], ASTEROID_TYPE["enemyship2"], ASTEROID_TYPE["enemy_elite_fighter"], ASTEROID_TYPE["enemy_bomber"]):
                r = rv
            else:
                r = random.randint(0,359)

            # 回転速度
            rs = 0
            # if new_type == ASTEROID_TYPE["enemyship2"]:
            #     rs = 10

            # 速度
            velocity = 0
            if new_type == ASTEROID_TYPE["enemyship1"]:
                velocity = SPEED_ENEMY_INTERCEPTOR
            elif new_type == ASTEROID_TYPE["enemyship2"]:
                velocity = SPEED_ENEMY_FIGHTER
            elif new_type == ASTEROID_TYPE["enemy_elite_fighter"]:
                velocity = SPEED_ENEMY_ELITE_FIGHTER
            elif new_type == ASTEROID_TYPE["enemy_bomber"]:
                velocity = SPEED_ENEMY_BOMBER
            else:
                velocity = random.choice([0.25, 0.5, 1.0, 1.5])

            # シールド
            shield = 0
            if new_type == ASTEROID_TYPE["enemy_elite_fighter"]:
                shield = SHIELD_ENEMY_ELITE_FIGHTER
            elif new_type == ASTEROID_TYPE["enemy_bomber"]:
                shield = SHIELD_ENEMY_BOMBER

            obj_asteroids[i] = {
                "x": x, 
                "y": y, 
                "r": r, 
                "rv": rv, 
                "rot_speed": rs,
                "s": size,
                "velocity": velocity,
                "type": new_type,
                "spawn_timer": g_timer-random.randint(0,FPS),
                "shield": shield,
                "immu_timer": -ENEMY_IMMU_TIMER
                }
            break

def create_enemies():
    """
    隕石・敵を作成
    """
    global g_spawnrate, g_level
    sec = g_timer / 60
    if g_level == 0:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            # レベルアップ
            g_level += 1
            g_spawnrate = int(4*FPS)
            create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
        if g_timer%g_spawnrate == 0:
            create_enemy()
    elif g_level == 1:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            # レベルアップ
            g_level += 1
            g_spawnrate = int(4*FPS)
            create_enemy(new_type=ASTEROID_TYPE["enemyship2"])
        if g_timer%g_spawnrate == 0:
            rand = random.randint(0,3)
            if rand == 0:
                create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
            else:
                create_enemy()
    elif g_level == 2:
        if g_timer % (LVUP_RATE) == 0 and g_timer != 0:
            # レベルアップ
            g_level += 1
            g_spawnrate = int(3*FPS)
            create_enemy(new_type=ASTEROID_TYPE["enemy_elite_fighter"])
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
            g_spawnrate = int(g_spawnrate*0.95)
        if g_timer%g_spawnrate == 0:
            rand = random.randint(0,7)
            if rand in (0,1):
                create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
            elif rand == 2:
                if is_exist(ASTEROID_TYPE["enemy_elite_fighter"], True) >= 2:
                    create_enemy(new_type=ASTEROID_TYPE["enemyship2"])
                else:
                    create_enemy(new_type=ASTEROID_TYPE["enemy_elite_fighter"])
            elif rand == 3:
                if is_exist(ASTEROID_TYPE["enemy_bomber"], True) >= 2:
                    create_enemy(new_type=ASTEROID_TYPE["enemyship1"])
                else:
                    create_enemy(new_type=ASTEROID_TYPE["enemy_bomber"])
            else:
                create_enemy()
   
def is_enemy_immu(index):
    """
    敵が無敵時間か
    """
    return (g_timer - obj_asteroids[index]["immu_timer"]) < ENEMY_IMMU_TIMER

def destry_asteroid(index, playsound=True):
    """
    敵のダメージ・破壊処理
    """
    # エフェクトを作成
    create_effect(obj_asteroids[index]["x"], obj_asteroids[index]["y"], type=EFFECT_TYPE["explosion"], size=1.0)
    if playsound: ASSETS.play("rock")

    # 無敵時間
    if is_enemy_immu(index):
        return

    # シールド
    if obj_asteroids[index]["shield"] > 0:
        obj_asteroids[index]["shield"] -= 1
        obj_asteroids[index]["immu_timer"] = g_timer
        return
    
    # スコア
    type = obj_asteroids[index]["type"]
    add_score = 0
    if type == ASTEROID_TYPE["enemyship1"]:
        add_score = SCORE_ENEMY_INTERSEPTOR
    elif type == ASTEROID_TYPE["enemyship2"]:
        add_score = SCORE_ENEMY_FIGHTER
    elif type == ASTEROID_TYPE["enemy_elite_fighter"]:
        add_score = SCORE_ENEMY_ELITE_FIGHTER
    elif type == ASTEROID_TYPE["enemy_bomber"]:
        add_score = SCORE_ENEMY_BOMBER
    elif type == ASTEROID_TYPE["big"]:
        add_score = SCORE_ASTEROID_BIG
    elif type == ASTEROID_TYPE["small"]:
        add_score = SCORE_ASTEROID_SMALL
    global g_score
    g_score += add_score

    # ドロップ
    if type == ASTEROID_TYPE["big"]:
        if random.randint(0,DROP_RATE_BIG) == 0:
            if random.randint(0,DROP_RATE_BIG) == 0:
                # 低確率で2つドロップ
                create_pickup(obj_pickups, PICKUP_TYPE["diamond"], obj_asteroids[index]["x"], obj_asteroids[index]["y"])
                create_pickup(obj_pickups, PICKUP_TYPE["diamond"], obj_asteroids[index]["x"], obj_asteroids[index]["y"])
            else:
                create_pickup(obj_pickups, PICKUP_TYPE["diamond"], obj_asteroids[index]["x"], obj_asteroids[index]["y"])
    elif type == ASTEROID_TYPE["small"]:
        if random.randint(0,DROP_RATE_SMALL) == 0:    
            create_pickup(obj_pickups, PICKUP_TYPE["diamond"], obj_asteroids[index]["x"], obj_asteroids[index]["y"])    
    elif type == ASTEROID_TYPE["enemyship1"]:
        if random.randint(0,DROP_RATE_INTERSEPTOR) == 0:    
            create_type = random.choice([PICKUP_TYPE["diamond"], POWERUP_TYPE["three_shot"], POWERUP_TYPE["piercing_shot"],POWERUP_TYPE["auto_shot"]])
            create_pickup(obj_pickups, create_type, obj_asteroids[index]["x"], obj_asteroids[index]["y"])   
    elif type == ASTEROID_TYPE["enemyship2"]:
        if random.randint(0,DROP_RATE_FIGHTER) == 0:    
            create_type = random.choice([PICKUP_TYPE["diamond"], POWERUP_TYPE["three_shot"], POWERUP_TYPE["piercing_shot"],POWERUP_TYPE["auto_shot"]])
            create_pickup(obj_pickups, create_type, obj_asteroids[index]["x"], obj_asteroids[index]["y"])  
    elif type == ASTEROID_TYPE["enemy_elite_fighter"] or type == ASTEROID_TYPE["enemy_bomber"]:
        # Elite パワーアップを一つと、確率でもう一つダイヤかパワーアップを落とす
        create_type = random.choice([POWERUP_TYPE["three_shot"], POWERUP_TYPE["piercing_shot"],POWERUP_TYPE["auto_shot"]])
        create_pickup(obj_pickups, create_type, obj_asteroids[index]["x"], obj_asteroids[index]["y"])    
        if random.randint(0,DROP_RATE_ELITE) == 0:
            create_type = random.choice([PICKUP_TYPE["diamond"], POWERUP_TYPE["three_shot"], POWERUP_TYPE["piercing_shot"],POWERUP_TYPE["auto_shot"]])
            create_pickup(obj_pickups, create_type, obj_asteroids[index]["x"], obj_asteroids[index]["y"])    

    # 大アステロイドから小アステロイドへ
    if obj_asteroids[index]["type"] == ASTEROID_TYPE["big"]:
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
    obj_asteroids[index] = None

def shoot_bullet_player():
    """
    弾を発射(プレイヤー)
    """
    ASSETS.play("shot")
    if player_upgrade_available(POWERUP_TYPE["three_shot"]):
        shoot_bullet(BULLET_TYPE["player"], None, g_player_angle-10)
        shoot_bullet(BULLET_TYPE["player"], None, g_player_angle)
        shoot_bullet(BULLET_TYPE["player"], None, g_player_angle+10)
    else:
        shoot_bullet(BULLET_TYPE["player"], None, g_player_angle)

def shoot_bullet(type=BULLET_TYPE["player"], pos=None, angle=None, speed=0, sound=True):
    """
    弾を発射
    """
    global obj_bullets
    for i in range(MAX_BULLETS):
        if obj_bullets[i] is None:
            if type == BULLET_TYPE["player"]:
                bullet_x = g_player_pos["x"] - BULLET_OFFSET * math.sin(math.radians(angle))
                bullet_y = g_player_pos["y"] - BULLET_OFFSET * math.cos(math.radians(angle))
                if player_upgrade_available(POWERUP_TYPE["piercing_shot"]):
                    size = 1.0
                    type = BULLET_TYPE["player_piercing"]
                else:  
                    size = 0.4
            elif type == BULLET_TYPE["enemy_missile"]:
                bullet_x = pos[0] - BULLET_OFFSET * math.sin(math.radians(angle))
                bullet_y = pos[1] - BULLET_OFFSET * math.cos(math.radians(angle))
                if sound:
                    ASSETS.play("shot2")
                size = 1.5
            else:
                bullet_x = pos[0] - BULLET_OFFSET * math.sin(math.radians(angle))
                bullet_y = pos[1] - BULLET_OFFSET * math.cos(math.radians(angle))
                if sound:
                    ASSETS.play("shot2")
                size = 0.6
            obj_bullets[i] = {"x":bullet_x, "y":bullet_y, "r":angle, "s":size, "type":type, "timer":g_timer, "speed":speed}
            
            break

def create_pickup(obj_list, spawn_type, spawn_x, spawn_y):
    """
    ピックアップを作成
    """
    s = None
    if spawn_type == PICKUP_TYPE["diamond"]:
        s = 1.25
    else:
        s = 0.5
    for i in range(MAX_PICKUP):
        if obj_list[i] is None:
            obj_list[i] = {"x":spawn_x, "y":spawn_y, "s":s, "type":spawn_type, "rv":random.randint(0,359), "timer":g_timer}
            break

def update_objects(screen):
    """
    オブジェクトの更新処理
    """
    global g_score, g_money, obj_bullets
    # 敵の更新
    for i in range(MAX_ASTEROIDS):
        obj = obj_asteroids[i]
        if obj is not None:
            # 敵の移動
            if obj["type"] == ASTEROID_TYPE["enemyship2"]:
                obj["rot_speed"] = 50*math.sin(math.radians((g_timer-obj["spawn_timer"])/10))
            obj["r"] += obj["rot_speed"] / FPS
            obj["rv"] += obj["rot_speed"] / FPS
            obj["x"] -= obj["velocity"] * math.sin(math.radians(obj["rv"]))
            obj["y"] -= obj["velocity"] * math.cos(math.radians(obj["rv"]))
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
            # 矢印の描画
            if obj["type"] != ASTEROID_TYPE["small"]:
                arrow_blink = (g_timer % 4) < 2
                if arrow_blink:
                    sprite = ASSETS.img_arrow
                    if obj["y"] <= 0:
                        blit_rotate_center(screen, sprite, (obj["x"]-sprite.get_width()/2, 10), 0, 0.3)
                    elif obj["y"] >= WINDOW_H:
                        blit_rotate_center(screen, sprite, (obj["x"]-sprite.get_width()/2, WINDOW_H-90), 180, 0.3)
                    elif obj["x"] <= 0:
                        blit_rotate_center(screen, sprite, (10, obj["y"]-sprite.get_height()/2), 90, 0.3)
                    elif obj["x"] >= WINDOW_W:
                        blit_rotate_center(screen, sprite, (WINDOW_W-90, obj["y"]-sprite.get_height()/2), -90, 0.3)
                
            # 敵機
            if obj["type"] in (ASTEROID_TYPE["enemyship1"], ASTEROID_TYPE["enemyship2"], ASTEROID_TYPE["enemy_elite_fighter"], ASTEROID_TYPE["enemy_bomber"]):
                # 敵弾を発射
                if is_on_screen(obj["x"],obj["y"]):
                    speed = 1
                    if obj["type"] == ASTEROID_TYPE["enemyship2"]:
                        if(g_timer - obj["spawn_timer"]) % (FIRERATE_ENEMY_FIGHTER) == 0:
                            speed = BULLET_SPEED_ENEMY_FIGHTER
                            type = BULLET_TYPE["enemy2"]
                            r = get_target_degree(obj["x"], obj["y"])
                            shoot_bullet(type, (obj["x"], obj["y"]), r, speed)
                    elif obj["type"] == ASTEROID_TYPE["enemy_elite_fighter"]:
                        if(g_timer - obj["spawn_timer"]) % (TURNRATE_ENEMY_ELITE_FIGHTER) == 0:
                            obj["rot_speed"] = random.choice([0,0,0,-45,45])
                        if(g_timer - obj["spawn_timer"]) % (FIRERATE_ENEMY_ELITE_FIGHTER) == 0:
                            if 200 < get_dis(obj["x"],obj["y"],g_player_pos["x"],g_player_pos["y"]):
                                attack_type = random.randint(1,2)
                            else:
                                attack_type = random.randint(0,1)
                            speed = BULLET_SPEED_ELITE_FIGHTER
                            type = BULLET_TYPE["enemy2"]
                            if attack_type == 0:
                                distance = get_dis(g_player_pos["x"],g_player_pos["y"], obj["x"],obj["y"])
                                target_x = g_player_pos["x"] - g_player_velosity["x"] * distance / BULLET_SPEED_ENEMY_FIGHTER /2
                                target_y = g_player_pos["y"] - g_player_velosity["y"] * distance / BULLET_SPEED_ENEMY_FIGHTER /2
                                r = get_target_degree(obj["x"], obj["y"], target_x, target_y)
                                shoot_bullet(type, (obj["x"], obj["y"]), r+10, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), r, speed*1.1)
                                shoot_bullet(type, (obj["x"], obj["y"]), r-10, speed, False)
                            if attack_type == 1:
                                speed *= 1.5
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"], speed)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+45, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+90, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+135, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+180, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+225, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+270, speed, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), obj["r"]+315, speed, False)
                            if attack_type == 2:
                                distance = get_dis(g_player_pos["x"],g_player_pos["y"], obj["x"],obj["y"])
                                target_x = g_player_pos["x"] - g_player_velosity["x"] * distance / BULLET_SPEED_ENEMY_FIGHTER /2
                                target_y = g_player_pos["y"] - g_player_velosity["y"] * distance / BULLET_SPEED_ENEMY_FIGHTER /2
                                r = get_target_degree(obj["x"], obj["y"], target_x, target_y)
                                speed *= 2
                                shoot_bullet(type, (obj["x"], obj["y"]), r, speed)
                                shoot_bullet(type, (obj["x"], obj["y"]), r, speed*0.9, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), r, speed*0.8, False)
                                shoot_bullet(type, (obj["x"], obj["y"]), r, speed*0.7, False)
                    elif obj["type"] == ASTEROID_TYPE["enemy_bomber"]:
                        if(g_timer - obj["spawn_timer"]) % (TURNRATE_ENEMY_BOMBER) == 0:
                            obj["rot_speed"] = random.choice([0,0,-30,30])
                        if(g_timer - obj["spawn_timer"]) % (FIRERATE_ENEMY_BOMBER) == 0:
                            if random.randint(0,3) == 0:
                                r = get_target_degree(obj["x"], obj["y"])
                                shoot_bullet(BULLET_TYPE["enemy_missile"], (obj["x"], obj["y"]), obj["r"]+135, 4, False)
                                shoot_bullet(BULLET_TYPE["enemy_missile"], (obj["x"], obj["y"]), obj["r"]-135, 4)
                            else:
                                shoot_bullet(BULLET_TYPE["enemy_missile"], (obj["x"], obj["y"]), obj["r"], 4)
                    else:
                        if(obj["spawn_timer"] - g_timer) % (FIRERATE_ENEMY_INTERCEPTOR) == 0:
                            type = BULLET_TYPE["enemy1"]
                            speed = BULLET_SPEED_ENEMY_INTERCEPTOR
                            r = obj["r"]
                            shoot_bullet(type, (obj["x"], obj["y"]), r, speed)
            # 敵のバリア
            if obj["shield"] > 0:
                if is_enemy_immu(i) and blink_timer(3):
                    continue
                if (g_timer % 6) < 3:
                    index = 0
                else:
                    index = 1
                img_shield = pygame.transform.rotozoom(ASSETS.imgs_shield_enemy[index], 0, 1.0)
                screen.blit(img_shield, [obj["x"]-img_shield.get_width()/2, obj["y"]-img_shield.get_height()/2])

    # 弾
    for i in range(MAX_BULLETS):
        bullet = obj_bullets[i]
        if bullet is not None:
            draw = False
            type = bullet["type"]
            # ミサイルの方向調整・煙
            if type == BULLET_TYPE["enemy_missile"]:
                if g_timer - bullet["timer"] > 3 * FPS:
                    explode_missile(i)
                    continue
                end = get_target_degree(bullet["x"], bullet["y"])
                start = bullet["r"]
                shortest_angle = ((end-start) + 180) % 360 - 180
                shortest_angle = min(shortest_angle, MISSILE_ROTATE_SPEED)
                shortest_angle = max(-MISSILE_ROTATE_SPEED, shortest_angle)
                bullet["rv"] = bullet["r"] = start + shortest_angle
                if int(g_timer % 3) == 0:
                    smoke_x = bullet["x"] + MISSILE_SPEED * math.sin(math.radians(bullet["r"]))
                    smoke_y = bullet["y"] + MISSILE_SPEED * math.cos(math.radians(bullet["r"]))
                    create_effect(smoke_x, smoke_y, EFFECT_TYPE["fire"], 0.5)
            # 貫通弾
            if type in (BULLET_TYPE["player"], BULLET_TYPE["player_piercing"]):
                speed = BULLET_SPEED_PLAYER
            else:
                speed = bullet["speed"]
            # 移動
            bullet["x"] -= speed * math.sin(math.radians(bullet["r"]))
            bullet["y"] -= speed * math.cos(math.radians(bullet["r"]))
            # 画面外に行ったら消える
            if not -WINDOW_OUT <= bullet["x"] <= WINDOW_W + WINDOW_OUT or not -WINDOW_OUT <= bullet["y"] <= WINDOW_H + WINDOW_OUT:
                obj_bullets[i] = None
                continue
            if type in (BULLET_TYPE["player"], BULLET_TYPE["player_piercing"]):
                # プレイヤーの弾
                # ミサイルとの判定
                for j in range(MAX_BULLETS):
                    missile = obj_bullets[j]
                    if missile is not None:
                        if missile["type"] == BULLET_TYPE["enemy_missile"] and is_in_range(missile["x"], missile["y"], bullet["x"], bullet["y"], 20):
                            explode_missile(j)
                            break
                # 隕石との衝突判定
                for j in range(MAX_ASTEROIDS):
                    asteroid = obj_asteroids[j]
                    if asteroid is not None:
                        if asteroid["type"] == ASTEROID_TYPE["small"]:      
                            hit_radius = ASTEROID_HIT_RADIUS_SMALL     
                        else:      
                            hit_radius = ASTEROID_HIT_RADIUS
                        # 被弾
                        if is_in_range(asteroid["x"], asteroid["y"], bullet["x"], bullet["y"], hit_radius*obj_asteroids[j]["s"]) and not is_enemy_immu(j):
                            destry_asteroid(j)
                            if type == BULLET_TYPE["player_piercing"]:
                                pass
                            else:
                                obj_bullets[i] = None
                            break 
                else:
                    draw = True
            else:
                # 敵の弾 プレイヤーとの衝突を判定
                if is_in_range(bullet["x"], bullet["y"], g_player_pos["x"], g_player_pos["y"], 20.0):
                    player_damage()
                    if bullet["type"] == BULLET_TYPE["enemy_missile"]:
                        explode_missile(i)
                    else:
                        obj_bullets[i] = None
                    continue
                draw = True
            if draw:
                # 弾を描画
                if type == BULLET_TYPE["enemy_missile"]:
                    index = g_timer % 20
                    if index < 5:
                        index = 0
                    elif index < 10:
                        index = 1
                    elif index < 15:
                        index = 2
                    else:
                        index = 3
                    sprite = ASSETS.imgs_missile[index]
                else:
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
                img = ASSETS.imgs_explode
                length = len(img)
                size = 1.0
            elif effect["type"] == EFFECT_TYPE["fire"]:
                img = ASSETS.imgs_fire
                length = len(img)
                size = 0.7
            elif effect["type"] == EFFECT_TYPE["missile_explosion"]:    
                if g_timer % 10 == 0:
                    ASSETS.play("rock")
                    spawn_x = effect["x"]+random.randint(-40,40)
                    spawn_y = effect["y"]+random.randint(-40,40)
                    create_effect(spawn_x, spawn_y, EFFECT_TYPE["explosion"], 1.0)
                    if is_in_range(spawn_x, spawn_y, g_player_pos["x"], g_player_pos["y"], 30):
                        player_damage()
                if effect["count"] > 1*FPS:
                    obj_effects[i] = None
                continue
            elif effect["type"] == EFFECT_TYPE["pl_bomb"]:
                img = ASSETS.imgs_bomb
                length = len(img)
                size = 4.0
            elif effect["type"] == EFFECT_TYPE["flash"]:
                if effect["count"] <= 2:
                    screen.fill((255,255,255))
                    continue
                else:
                    obj_effects[i] = None
                    continue
            else:
                size = effect["s"]
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
            if is_in_range(pickup["x"], pickup["y"], g_player_pos["x"], g_player_pos["y"], PICKUP_RADIUS):
                # 拾う
                ASSETS.play("pickup")
                if pickup["type"] == PICKUP_TYPE["diamond"]:
                    g_score += SCORE_DIAMOND
                    g_money += MONEY_DIAMOND
                    charge_bomb(BOMB_CHARGE_DIAMOND)
                else:
                    g_score += SCORE_DIAMOND
                    player_pickup(pickup["type"])
                obj_pickups[i] = None
                continue
            # 描画
            passed_time = g_timer - pickup["timer"]
            # 自然消滅・点滅
            if passed_time > DIAMOND_LIFE + DIAMOND_BLINK:
                # 消滅
                pickup = None
                continue
            elif passed_time > DIAMOND_LIFE:
                # 点滅
                if  0 <= (g_timer % BLINK_SPEED) <= BLINK_SPEED / 2:
                    continue
            #描画
            sprite = None
            pickup_type = pickup["type"]
            if pickup_type == PICKUP_TYPE["diamond"]:
                sprite =  ASSETS.imgs_diamond[int(g_timer % (len(ASSETS.imgs_diamond)* ANIMATION_COUNT) / ANIMATION_COUNT)]
            else:
                sprite =  ASSETS.imgs_pickup[pickup_type]
            sprite = pygame.transform.rotozoom(sprite, 0, pickup["s"])
            screen.blit(sprite, [pickup["x"]-sprite.get_width()/2, pickup["y"]-sprite.get_height()/2])
            

def blit_rotate_center(surf, image, topleft, angle, scale=1.0):
    """
    画像中心を基準としたトランスフォームを適用して描画する
    """
    img = pygame.transform.rotozoom(image, angle, scale)
    new_rect = img.get_rect(center = image.get_rect(topleft = topleft).center)
    surf.blit(img, new_rect.topleft)

def player_burner(screen, angle_offset = 0):
    # スラスター
    burner_x = g_player_pos["x"] + BURNER_OFFSET * math.sin(math.radians(g_player_angle + angle_offset))
    burner_y = g_player_pos["y"] + BURNER_OFFSET * math.cos(math.radians(g_player_angle + angle_offset))
    sprite = ASSETS.img_burner
    blit_rotate_center(screen, sprite, (burner_x-sprite.get_width()/2, burner_y-sprite.get_height()/2), g_player_angle + angle_offset, 0.7)
    if int(g_timer % 3) == 0:
        smoke_x = g_player_pos["x"] + SMOKE_OFFSET * math.sin(math.radians(g_player_angle + angle_offset))
        smoke_y = g_player_pos["y"] + SMOKE_OFFSET * math.cos(math.radians(g_player_angle + angle_offset))
        create_effect(smoke_x, smoke_y, EFFECT_TYPE["fire"], 0.7)

def move_starship(screen, key):
    """
    プレイヤーの操作
    """
    global g_player_pos, g_player_angle, g_player_velosity, g_player_life, g_respawn_timer
    for i in range(3):
        if g_player_pickup_effects[i] > 0:
            g_player_pickup_effects[i] -= 1
    # オート射撃
    if player_upgrade_available(POWERUP_TYPE["auto_shot"]) and key[K_SPACE]:
        if g_timer % 5 == 0:
            shoot_bullet_player()
    """    if key[K_e]:
        # 加速
        g_player_velosity["x"] += CTRL_MOVE_SPEED * math.sin(math.radians(g_player_angle-90))
        g_player_velosity["y"] += CTRL_MOVE_SPEED * math.cos(math.radians(g_player_angle-90))
        player_burner(screen, -90)
    if key[K_q]:
        # 加速
        g_player_velosity["x"] += CTRL_MOVE_SPEED * math.sin(math.radians(g_player_angle+90))
        g_player_velosity["y"] += CTRL_MOVE_SPEED * math.cos(math.radians(g_player_angle+90))
        player_burner(screen, 90)
    if key[K_s]:
        # 加速
        g_player_velosity["x"] *= 0.95
        g_player_velosity["y"] *= 0.95"""

    if key[K_UP] or key[K_w]:
        # 加速
        g_player_velosity["x"] += CTRL_MOVE_SPEED * math.sin(math.radians(g_player_angle))
        g_player_velosity["y"] += CTRL_MOVE_SPEED * math.cos(math.radians(g_player_angle))
        # スラスター
        burner_x = g_player_pos["x"] + BURNER_OFFSET * math.sin(math.radians(g_player_angle))
        burner_y = g_player_pos["y"] + BURNER_OFFSET * math.cos(math.radians(g_player_angle))
        player_burner(screen)
    
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
    if g_player_pos["x"] < 0:
        g_player_pos["x"] = 0
    elif WINDOW_W < g_player_pos["x"]:
        g_player_pos["x"] = WINDOW_W
    if g_player_pos["y"] < 0:
        g_player_pos["y"] = 0
    elif WINDOW_H < g_player_pos["y"]:
        g_player_pos["y"] = WINDOW_H
    if abs(g_player_angle) > 360:
        g_player_angle %= 360
    
    # 船と敵との衝突判定
    for j in range(MAX_ASTEROIDS):
        if obj_asteroids[j] is not None and is_in_range(obj_asteroids[j]["x"], obj_asteroids[j]["y"], g_player_pos["x"], g_player_pos["y"], ASTEROID_HIT_RADIUS*obj_asteroids[j]["s"]):                    
            if player_damage():
                destry_asteroid(j)

def player_damage():
    """
    プレイヤーへのダメージ処理
    """
    global g_player_life, g_respawn_timer

    if g_gamestate != GAMESTATE["game"]:
        return False

    # 無敵時間をチェック
    if PLAYER_SESPAWN_TIME > g_timer - g_respawn_timer:
        return False

    # フラッシュして敵弾を削除
    create_effect(0, 0, type=EFFECT_TYPE["flash"])
    delete_bullets()

    ASSETS.play("rock")
    create_effect(g_player_pos["x"], g_player_pos["y"], EFFECT_TYPE["explosion"], 1.0)
    g_player_life -= 1
    g_respawn_timer = g_timer
    init_bomb()
    return True

def main():
    global g_timer, g_respawn_timer, g_level, g_player_velosity, g_score, g_previous_frame_score, g_money, g_bg_pos, ASSETS, g_gamestate, g_player_pos, g_player_angle, g_player_life
    global obj_bullets, obj_asteroids, obj_effects, obj_pickups
    global fnt_m, fnt_s, fnt_ss, fnt_l
    global g_bomb_energy
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
                # LSHIFT
                if event.key == K_LSHIFT and g_gamestate == GAMESTATE["game"]:
                    if is_bomb_ready(): fire_bomb()
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
                    if g_gamestate == GAMESTATE["game"] and not player_upgrade_available(POWERUP_TYPE["auto_shot"]):
                        shoot_bullet_player()
                    elif g_gamestate == GAMESTATE["pause"]:
                        g_gamestate = GAMESTATE["game"]
            if event.type == KEYUP:
                # Volume
                if event.key == K_f:
                    ASSETS.set_volume(max(0, ASSETS.get_volume() - 0.1))
                if event.key == K_r:
                    ASSETS.set_volume(min(1, ASSETS.get_volume() + 0.1))
                if event.key == K_SPACE:
                    if g_gamestate == GAMESTATE["title"]:
                        g_timer = 0
                        g_level = DEBUG_START_LEVEL
                        g_score = 0
                        g_previous_frame_score = 0
                        g_money = 0
                        timer_pause = 0
                        g_spawnrate = 2*FPS
                        g_player_pos = {"x":WINDOW_W/2, "y":WINDOW_H/2}
                        g_player_velosity = {"x":0, "y":0}
                        g_player_angle = 0
                        g_player_life = 3
                        g_respawn_timer = -PLAYER_SESPAWN_TIME
                        g_player_pickup_effects = [0]*POWERUP_NUM
                        obj_bullets = [None]*MAX_BULLETS
                        obj_asteroids = [None]*MAX_ASTEROIDS
                        obj_effects = [None]*MAX_EFFECTS
                        obj_pickups = [None]*MAX_PICKUP
                        g_gamestate = GAMESTATE["game"]
                        init_bomb()
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

        if not g_gamestate == GAMESTATE["game"]:
            clear_message()

        if g_gamestate == GAMESTATE["title"]:
            # タイトルの描画
            screen.blit(ASSETS.img_title, [WINDOW_W/2-ASSETS.img_title.get_width()/2, WINDOW_H/2-ASSETS.img_title.get_height()/2])
            draw_text(screen, "[R, F] Audio Vfolume", WINDOW_W-150, WINDOW_H-30, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[ESC] pause / quit", WINDOW_W-150, WINDOW_H-60, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[F1] Fullscreen", WINDOW_W-150, WINDOW_H-90, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[SPACE] Fire, [Shift] Bomb", WINDOW_W-150, WINDOW_H-120, (255,255,255), fnt_ss, anchor_center=False)
            draw_text(screen, "[WAD,Arrowkey] Ship ctrl", WINDOW_W-150, WINDOW_H-150, (255,255,255), fnt_ss, anchor_center=False)
            if blink_timer(5):
                draw_text(screen, "Press [SPACE] to start", WINDOW_W/2 + 20, WINDOW_H/2+200, (255,255,255), fnt_m)
        if g_gamestate == GAMESTATE["game"]:
            if g_player_life < 0:
                g_timer = 0
                g_gamestate = GAMESTATE["exploding"]
            else:
                # ボムのチャージ
                charge_bomb()
                # 自機の操作
                move_starship(screen, key)
                # スコアボーナスの作成
                score_bonus()
                # 隕石を作成
                create_enemies()
                # オブジェクトのアップデートと描画
                update_objects(screen)
                # プレイヤーの描画
                draw_player(screen)
                # UIの描画
                draw_ui(screen, fnt_s)
        if g_gamestate == GAMESTATE["exploding"]:
            # 爆発
            # オブジェクトのアップデートと描画
            update_objects(screen)
            if g_timer % 10 == 0:
                ASSETS.play("rock")
                create_effect(g_player_pos["x"]+random.randint(-40,40), g_player_pos["y"]+random.randint(-40,40), EFFECT_TYPE["explosion"], 1.0)
            # プレイヤーの描画
            draw_player(screen)
            # UIの描画
            draw_ui(screen, fnt_s)
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

def draw_player(screen):
    """
    プレイヤーを描画
    """
    
    # ボムが有効の時、シールドを描画
    if g_bomb_energy > BOMB_COST:
        if (g_timer % 6) < 3:
            img = ASSETS.imgs_bomb[3]
        else:
            img = ASSETS.imgs_bomb[4]
        img_shield = pygame.transform.rotozoom(img, 0, 0.75)
        screen.blit(img_shield, [g_player_pos["x"]-img_shield.get_width()/2, g_player_pos["y"]-img_shield.get_height()/2])


    # プレイヤー
    if g_timer - g_respawn_timer < PLAYER_SESPAWN_TIME and blink_timer():
        return
    else:
        sprite = ASSETS.imgs_player_ship[0]
        blit_rotate_center(screen, sprite, (g_player_pos["x"] - sprite.get_width()/2, g_player_pos["y"] - sprite.get_height()/2), g_player_angle, 0.5)

def draw_ui(screen, font):
    """
    UIを描画
    """
    global g_timer_ui
    if g_gamestate != GAMESTATE["exploding"]:
        g_timer_ui = g_timer
    draw_text(screen, "SCORE:{:09}".format(g_score), 150, 30, (255,255,255), font)
    # draw_text(screen, "MONEY:{:09}".format(g_money), 150, 60, (255,255,255), font)
    img_rotozoom = pygame.transform.rotozoom(ASSETS.imgs_player_ship[0], 0, 0.4)
    # 時間
    sec = int(g_timer_ui / FPS)
    min = int(sec / 60)
    sec = str(sec%60)
    min = str(min)
    if len(sec) == 1: sec = "0"+sec
    if len(min) == 1: min = "0"+min
    draw_text(screen, min+":"+sec, WINDOW_W/2, 30, (255,255,255), fnt_m)
    
    # ボム
    draw_text(screen, "BOMB: "+str(int(g_bomb_energy))+"%", WINDOW_W - 100, WINDOW_H-20, (255,255,255), fnt_s)
    # 残機
    if g_player_life > 0:
        for i in range(g_player_life):
            x = 30 + 50 * i
            y = 60
            screen.blit(img_rotozoom, [x, y])
    # ピックアップ
    for i in range(POWERUP_NUM):
        timer = g_player_pickup_effects[i]
        if timer > 0:
            if timer < (3 * FPS) and blink_timer(1, timer):
                continue
            img_rotozoom = pygame.transform.rotozoom(ASSETS.imgs_pickup[i], 0, 0.6)
            screen.blit(img_rotozoom, [30 + 30 * i, 120])
    #　メッセージ
    if g_message_timer > g_timer:
        draw_text(screen, g_message, WINDOW_W/2, WINDOW_H/2-20, (255,255,255), fnt_m)
    # メッセージ(ピックアップ)
    span = g_timer - g_pickup_msg_timer
    span_max = 2*FPS
    if span < span_max:
        draw_text(screen, g_pickup_msg, g_pickup_pos["x"], g_pickup_pos["y"]-math.sin(span/span_max*3.14)*10, (255,255,255), fnt_ss)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
■ UTILS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def blink_timer(frames = 1, timer=None):
    """
    一定フレームおきに真偽を入れ替える
    点滅に使う
    """
    if timer is None:
        timer = g_timer
    return 0 <= (timer % (BLINK_SPEED * frames)) <= (BLINK_SPEED*frames)/2

def get_dis(x1, y1, x2, y2):
    """
    二点間の距離を取得
    """
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 )

def is_in_range(x1, y1, x2, y2, range):
    """
    二点間が一定の距離以内か
    """
    return (x1-x2)**2 + (y1-y2)**2 < range**2

def get_target_degree(x1,y1,x2=None,y2=None):
    """
    座標xy1から座標xy2への角度を求める
    xy2を略した場合、プレイヤーへの角度を求める
    """
    if x2 is None: x2 = g_player_pos["x"]
    if y2 is None: y2 = g_player_pos["y"]
    return math.degrees(math.atan2(-(y2-y1), (x2-x1) ))-90

def is_on_screen(x,y):
    return (0<=x<=WINDOW_W) and (0<=y<=WINDOW_H)

my_out_file = open("./log.txt", "w")

if __name__ == "__main__":
    try:
        main()
    except:
        import traceback
        traceback.print_exc(file=my_out_file)
