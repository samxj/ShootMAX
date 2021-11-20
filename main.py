import pygame
from pygame import mixer
import os
import random
import csv

from pygame import fastevent
from pygame import draw
import button

pygame.init()
mixer.init()

clock = pygame.time.Clock()
fps = 60


SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 640

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ShootMAX")

moving_left = False
moving_right = False
shoot  = False
shop = False
grenade = False
grenade_thrown = False
level = 3
max_level = 3
level_complete = False
game_complete = False
start_game = False
start_intro = False
start_outro = False
respawn = (0, 0)
realspawn = (0, 0)
goback = True
done = False

GRAVITY = 0.75

ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 22

SCROLL_THRESH = 650
SCREEN_SCROLL = 0
BG_SCROLL = 0

img_list = []
button_list = []

for x in range(TILE_TYPES):
    img = pygame.image.load(f'asset/tiles/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

pygame.mixer.music.load("asset/audio/audio_music2.mp3")
pygame.mixer.music.set_volume(0.5)

jump_fx = pygame.mixer.Sound("asset/audio/audio_jump.wav")
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound("asset/audio/audio_shot.wav")
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound("asset/audio/audio_grenade.wav")
grenade_fx.set_volume(0.5)
win_fx = pygame.mixer.Sound("asset/audio/win.wav")

start_img = pygame.image.load("asset/icons/start_btn.png").convert_alpha()
exitbtn_img = pygame.image.load("asset/icons/exit_btn.png").convert_alpha()
restart_img = pygame.image.load("asset/icons/restart_btn.png").convert_alpha()

bullet_img = pygame.image.load("asset/icons/bullet.png").convert_alpha()
grenade_img = pygame.image.load("asset/icons/grenade.png").convert_alpha()
heal_box_img = pygame.image.load("asset/icons/health_box.png").convert_alpha()
ammo_box_img = pygame.image.load("asset/icons/ammo_box.png").convert_alpha()
grenade_box = pygame.image.load("asset/icons/grenade_box.png").convert_alpha()
coin_box = pygame.image.load("asset/icons/coin_box.png").convert_alpha()
coin_box_img = pygame.transform.scale(coin_box, (TILE_SIZE, TILE_SIZE))

pine1_img = pygame.image.load("asset/background/pine1.png").convert_alpha()
pine2_img = pygame.image.load("asset/background/pine2.png").convert_alpha()
mountain_img = pygame.image.load("asset/background/mountain.png").convert_alpha()
sky_cloud_img = pygame.image.load("asset/background/sky_cloud.png").convert_alpha()

decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

item_boxes = {
    "Health"    : heal_box_img,
    "Ammo"      : ammo_box_img,
    "Grenade"   : grenade_box,
    "Coin"      : coin_box_img,
}

BG = (144, 201, 120)
RED = (255, 0, 0)

font = pygame.font.SysFont("Futura", 30)
winfont = pygame.font.SysFont("Futura", 120)

def draw_text(text, font, colour, x, y):
    img = font.render(text, True, colour)
    SCREEN.blit(img, (x, y))


def draw_bg():
    SCREEN.fill(BG)
    width = sky_cloud_img.get_width()
    for x in range(5):
        SCREEN.blit(sky_cloud_img, ((x * width) - BG_SCROLL * 0.5, 0))
        SCREEN.blit(mountain_img, ((x * width) - BG_SCROLL * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        SCREEN.blit(pine1_img, ((x * width) - BG_SCROLL * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        SCREEN.blit(pine2_img, ((x * width) - BG_SCROLL * 0.8, SCREEN_HEIGHT - mountain_img.get_height() - 150))

def reset_level():
    enemey_group.empty()
    decoration_group.empty()
    water_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    exit_group.empty()

    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data
    

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #check what kind of box it was
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            elif self.item_type == 'Coin':
                player.ammo += 2
                player.health += 5
                player.coins += 1
                if player.health > player.max_health:
                    player.health = player.max_health
            #delete the item box
            self.kill()

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #update new health
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(SCREEN, (0, 0, 0), (self.x - 2, self.y - 2, 154, 24)) #border rect
        pygame.draw.rect(SCREEN, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(SCREEN, (0, 255, 0), (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #check collision with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemyk in enemey_group:
            if pygame.sprite.spritecollide(enemyk, bullet_group, False):
                if enemyk.alive:
                    enemyk.health -= 20
                    self.kill()

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        for tile in world.obstacle_list:
            #x
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #y
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0

                #check if thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                
                #check if thrown down
                elif self.vel_y:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        #update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 0.5)
            explosion_group.add(explosion)
            #damage anyone nearby
            
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 1 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 1:
                player.health -= 37
            elif abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 22
            elif abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 3 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 3:
                player.health -= 8
            elif abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 4 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 4:
                player.health -= 3

            for enemy in enemey_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 1 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 1:
                    enemy.health -= 50
                elif abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 35
                elif abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 3 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 3:
                    enemy.health -= 20
                elif abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 4 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 4:
                    enemy.health -= 10
    
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"asset/explosion/exp{num}.png").convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        EXPLOSION_SPEED = 4
        #explosion animation
        self.rect.x += screen_scroll
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

enemey_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()

class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):

        pygame.sprite.Sprite.__init__(self)

        self.alive = True
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades = grenades
        self.shoot_cooldown = 0
        self.health = 100
        self.max_health = self.health
        self.char_type = char_type
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        self.RewardCollected = False
        self.coins = 0
        self.kills = 0

        #ai specific vars
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        temp_list = []
        animation_types = ['idle', 'run', 'jump', 'death']
        for animation in animation_types:

            temp_list = []

            num_of_frames = len(os.listdir(f"asset/{self.char_type}_{animation}"))
            for ib in range(num_of_frames):
                self.img = pygame.image.load(f"asset/{self.char_type}_{animation}/{ib}.png").convert_alpha()
                self.img = pygame.transform.scale(self.img, (int(self.img.get_width() * scale), int(self.img.get_height() * scale)))
                temp_list.append(self.img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.healthbari = self.MovingHealthBar(self.rect.x, self.rect.y - 60, self.health, self.max_health)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
    
    class MovingHealthBar():
        def __init__(self, x, y, health, max_health):
            self.x = x
            self.y = y
            self.health = health
            self.max_health = max_health

        def draw(self, health, x, y):
            #update new health
            self.health = health
            ratio = self.health / self.max_health
            pygame.draw.rect(SCREEN, (0, 0, 0), (x - 12, y - 8, 62, 12)) #border rect
            pygame.draw.rect(SCREEN, RED, (x - 10, y - 10, 60, 10))
            pygame.draw.rect(SCREEN, (0, 255, 0), (x - 10, y - 10, 60 * ratio, 10))
    
    def update(self):
        self.update_animation()
        self.check_alive()
        if self.alive:
            self.healthbari.draw(self.health, self.rect.x + screen_scroll, self.rect.y)
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx = 0
        dy = 0
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        if self.jump == True and self.in_air == False:
            self.vel_y = -11 #that's moving up, cos in pygame, going up is decreasing y
            self.jump = False
            self.in_air = True
        
        self.vel_y += GRAVITY # + Is down because, you know
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        #floor collision
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                
                #check if falling
                elif self.vel_y:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
        
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True
        
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0
        
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        self.rect.x += dx
        self.rect.y += dy
    
        #update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and BG_SCROLL < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) or (self.rect.left < SCROLL_THRESH and BG_SCROLL > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        
        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + int(0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1
            shot_fx.play()
    
    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.idling = True
                self.update_action(0)#0: idle
                self.idling_counter = 50
            if self.vision.colliderect(player.rect):
                self.update_action(0)#0: idle
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1: run
                    self.move_counter += 1
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #pygame.draw.rect(SCREEN, RED, self.vision)
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter = 0
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False 
        #scroll
        self.rect.x += screen_scroll

    
    def update_animation(self):
        ANIMATION_COOLDOWN = 100

        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
                if self.RewardCollected == False:
                    itemni = ItemBox('Coin', self.rect.x, self.rect.y)
                    item_box_group.add(itemni)
                    self.RewardCollected = True
            else:
                self.frame_index = 0
            
    def update_action(self, new_action):
        #check if new action is different to old
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
    
    def check_alive(self):
        if self.health <= 0:
            self.speed = 0
            self.health = 0
            self.alive = False
            self.update_action(3)


    def draw(self):
        SCREEN.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        #pygame.draw.rect(SCREEN, (255, 0, 0), self.rect, 1)

class World():
    def __init__(self):
        self.obstacle_list = []
    
    def process_data(self, data, respawn):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:#create player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 30, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                        respawn = (x * TILE_SIZE, y * TILE_SIZE)
                    elif tile == 16:#create enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 40, 0)
                        enemey_group.add(enemy)
                    elif tile == 17:#create ammo box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:#create grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:#create health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:#create exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar
    
    def draw(self):

        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            SCREEN.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0
    
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:
            pygame.draw.rect(SCREEN, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(SCREEN, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(SCREEN, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(SCREEN, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:
            pygame.draw.rect(SCREEN, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete

#load level data
#create empty tile list

world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
with open(f'asset/level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exitbtn_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)
mainmenu_btn_img = pygame.transform.scale(exitbtn_img, (TILE_SIZE * 2, TILE_SIZE))
mainmenu_button = button.Button(SCREEN_WIDTH - 95, SCREEN_HEIGHT - (SCREEN_HEIGHT - 10), mainmenu_btn_img, 1)
shop_button = button.Button(SCREEN_WIDTH - 250, SCREEN_HEIGHT - (SCREEN_HEIGHT - 110), pygame.image.load("asset/icons/shop_btn.png").convert_alpha(), 1)
button_col = 0
button_row = 0
death_fade = ScreenFade(2, (235, 65, 54), 8)
intro_fade = ScreenFade(1, (0, 0, 0), 4)

world = World()
player, health_bar = world.process_data(world_data, respawn)

screen_scroll = 0
run = True
game_complete = False

while run:

    clock.tick(fps)
    if start_game == False and goback == True:#in main menu
        #draw menu

        SCREEN.fill(BG)

        if start_button.draw(SCREEN):
            start_game = True
            start_intro = True
        if exit_button.draw(SCREEN):
            run = False
        if shop_button.draw(SCREEN):
            shop = True
            goback = False

    elif shop == True and goback == False:
        SCREEN.fill(BG)
        for i in range(len(img_list)):
            pygame.draw.line(SCREEN, RED, (0, button_row * 10),  (SCREEN_WIDTH, button_row * 10), 1)
            button_row += 1
        shop = True
        
    elif start_game == True:
        if done == False:
            pygame.mixer.music.play(-1, 0.0, 4000)
            done = True
        draw_bg()
        world.draw()
        draw_text("AMMO: ", font, (255, 255, 255), 10, 5)
        for x in range(player.ammo):
            SCREEN.blit(bullet_img, (90 + (x * 10), 10))
        draw_text("GRENADES: ", font, (255, 255, 255), 10, 35)
        for x in range(player.grenades):
            SCREEN.blit(grenade_img, (135 + (x * 15), 40))

        for enemy in enemey_group:
            enemy.ai()
            enemy.draw()
            enemy.update()
        player.update()
        player.draw()

        bullet_group.update()
        bullet_group.draw(SCREEN)
        grenade_group.update()
        grenade_group.draw(SCREEN)
        explosion_group.update()
        explosion_group.draw(SCREEN)

        item_box_group.update()
        item_box_group.draw(SCREEN)

        decoration_group.update()
        decoration_group.draw(SCREEN)
        exit_group.update()
        exit_group.draw(SCREEN)
        water_group.update()
        water_group.draw(SCREEN)

        #for checkpoint in checkpoint_group:
        #    respawnx, respawn_scroll = checkpoint.update()
        #    checkpoint.draw(SCREEN)

        if mainmenu_button.draw(SCREEN):
            start_game = False
            start_intro = False
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0
        if player.alive:
            if shoot:
                player.shoot()
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                                    player.rect.top, player.direction)
                grenade_group.add(grenade)
                grenade_thrown = True
                player.grenades -= 1
            if player.in_air:
                player.update_action(2)#2: jump
            if moving_left or moving_right:
                player.update_action(1)#1: run
            else:
                player.update_action(0)#0: idle
        else:
            screen_scroll = 0
            if restart_button.draw(SCREEN):
                BG_SCROLL = 0
                world_data = reset_level()
                with open(f'asset/level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data, respawn)
                #player.rect.x = respawnx[0]
                #player.rect.y = respawnx[1]

        screen_scroll, level_complete = player.move(moving_left, moving_right)
        BG_SCROLL -= screen_scroll
        if level_complete:
            start_intro = True
            if level < max_level:
                level += 1
            else:
                win_fx.play()
                game_complete = True
                run = False
            if game_complete != True:
                BG_SCROLL = 0
                world_data = reset_level()
                with open(f'asset/level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                if intro_fade.fade():
                    start_intro = False
                    intro_fade.fade_counter = 0
                world = World()
                player, health_bar = world.process_data(world_data, respawn)
            else:
                outro = ScreenFade(1, BG, 8)
                if outro.fade():
                    draw_text("YOU WIN!", font, (0, 255, 0), SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 50)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                moving_left = True
                moving_right = False
            if event.key == pygame.K_RIGHT:
                moving_left = False
                moving_right = True
            if event.key == pygame.K_SPACE and player.alive:
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_s:
                shoot = True
            if event.key == pygame.K_a:
                grenade = True
            if event.key == pygame.K_ESCAPE:
                run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                moving_left = False
                moving_right = False
            if event.key == pygame.K_RIGHT:
                moving_left = False
                moving_right = False
            if event.key == pygame.K_s:
                shoot = False
            if event.key == pygame.K_a:
                grenade = False
                grenade_thrown = False
    pygame.display.update()

done = False

while game_complete:
    if done == False:
        win_fx.play()
        outro = ScreenFade(2, BG, 2)
        pygame.mixer.music.pause()
        start_outro = True
        done = True
    if start_outro:
        draw_bg()
        world.draw()
        item_box_group.update()
        item_box_group.draw(SCREEN)
        decoration_group.update()
        decoration_group.draw(SCREEN)
        exit_group.update()
        exit_group.draw(SCREEN)
        water_group.update()
        water_group.draw(SCREEN)
        if outro.fade():
            percentkilledraw = (player.coins / len(enemey_group)) * 100
            percentkilled = str(percentkilledraw).split(".")
            draw_text("YOU WIN!", winfont, (0, 0, 255), SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 50)
            draw_text(f"Kills: {player.coins}", font, (0, 0, 255), SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT // 2 + 50)
            if int(percentkilled[0]) < 100:
                draw_text(f"So that's {percentkilled[0]}% of all the enemies!", font, (0, 0, 255), SCREEN_WIDTH // 2 - 125, SCREEN_HEIGHT // 2 + 100)
            else:
                draw_text(f"You killed ALL the enemies! Well done!", font, (0, 0, 255), SCREEN_WIDTH // 2 - 165, SCREEN_HEIGHT // 2 + 100)
            start_outro = False
            outro.fade_counter = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_complete = False
    
    pygame.display.update()