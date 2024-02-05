import pygame, random
from pathlib import Path

class Assets:
    def __init__(self, pygame):
        self.pygame = pygame
        self.img_arrow = pygame.image.load(Assets.make_absolute_path("/assets/arrow.png")).convert_alpha()
        self.img_title = pygame.image.load(Assets.make_absolute_path("/assets/logo.png")).convert_alpha()
        self.img_gameover = pygame.image.load(Assets.make_absolute_path("/assets/gameover.png")).convert_alpha()
        self.img_bg = pygame.image.load(Assets.make_absolute_path("/assets/galaxy.png")).convert_alpha()
        self.img_bullet = [
            pygame.image.load(Assets.make_absolute_path("/assets/bullet.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/bullet_enemy1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/bullet_enemy2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/bullet.png")).convert_alpha()
        ]
        self.imgs_player_ship = [
            pygame.image.load(Assets.make_absolute_path("/assets/starship.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/starship_l.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/starship_r.png")).convert_alpha()
        ]
        self.img_burner = pygame.image.load(Assets.make_absolute_path("/assets/starship_burner.png")).convert_alpha()
        self.imgs_explode = [
            pygame.image.load(Assets.make_absolute_path("/assets/explosion1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion3.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion4.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion5.png")).convert_alpha()
        ]
        self.imgs_bomb = [
            pygame.image.load(Assets.make_absolute_path("/assets/explosion_p_1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion_p_2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion_p_3.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion_p_4.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/explosion_p_5.png")).convert_alpha()
        ]
        self.imgs_shield_enemy = [
            self.imgs_explode[3], self.imgs_explode[4]
        ]
        self.imgs_missile = [
            pygame.image.load(Assets.make_absolute_path("/assets/missile0.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/missile1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/missile2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/missile3.png")).convert_alpha()
        ]
        self.imgs_asteroid = [
            pygame.image.load(Assets.make_absolute_path("/assets/asteroid_big.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/asteroid_small.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/enemy1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/enemy2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/enemy3.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/enemy8.png")).convert_alpha()
        ]
        self.imgs_diamond = [
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_0.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_3.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_4.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_5.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_6.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/diamond_7.png")).convert_alpha()
        ]
        self.imgs_fire = [
            pygame.image.load(Assets.make_absolute_path("/assets/fire_0.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/fire_1.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/fire_2.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/fire_3.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/fire_4.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/fire_5.png")).convert_alpha()
        ]
        self.imgs_pickup = [
            pygame.image.load(Assets.make_absolute_path("/assets/item_spread.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/item_piercing.png")).convert_alpha(),
            pygame.image.load(Assets.make_absolute_path("/assets/item_auto.png")).convert_alpha()
        ]
        self.sounds_rock = [
            pygame.mixer.Sound(Assets.make_absolute_path("/assets/rock2.ogg")),
            pygame.mixer.Sound(Assets.make_absolute_path("/assets/rock3.ogg"))
        ]
        self.volume = 0.5
        self.sound_pickup = pygame.mixer.Sound(Assets.make_absolute_path("/assets/pickup.ogg"))
        self.sound_shot = pygame.mixer.Sound(Assets.make_absolute_path("/assets/shot.ogg"))
        self.sound_shot2 = pygame.mixer.Sound(Assets.make_absolute_path("/assets/shot2.ogg"))
        self.sound_explosion = pygame.mixer.Sound(Assets.make_absolute_path("/assets/explosion.ogg"))
        self.sound_damage = pygame.mixer.Sound(Assets.make_absolute_path("/assets/damage.ogg"))
        self.set_volume(self.volume)

    def set_volume(self, volume):
        self.volume = volume
        self.sounds_rock[0].set_volume(volume)
        self.sounds_rock[1].set_volume(volume)
        self.sound_pickup.set_volume(volume)
        self.sound_shot.set_volume(volume)
        self.sound_shot2.set_volume(volume)
        self.sound_explosion.set_volume(volume)
        self.sound_damage.set_volume(volume)
        self.pygame.mixer.music.set_volume(volume)
    
    def get_volume(self):
        return self.volume

    def play_main_bgm(self):
            self.pygame.mixer.music.load(Assets.make_absolute_path("/assets/bensound-deepblue.mp3"))
            self.pygame.mixer.music.play(-1)

    def play(self, str):
        if str == "shot":
            self.sound_shot.play()  
        elif str == "shot2":
            self.sound_shot2.play()   
        elif str == "explosion":
            self.sound_explosion.play()     
        elif str == "damage":
            self.sound_damage.play()   
        elif str == "pickup":
            self.sound_pickup.play()  
        elif str == "rock":
            index = random.randint(0,1)
            self.sounds_rock[index].play() 
    
    @classmethod
    def make_absolute_path(self, relative_path):
        """
        相対パスを絶対パスへ変換
        """
        return (str(Path(__file__).parent) + relative_path).replace("\\", "/")