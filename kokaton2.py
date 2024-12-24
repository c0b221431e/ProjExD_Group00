import pygame
import sys
import random
import heapq

# Pygameの初期化
pygame.init()

# 画面の設定
WIDTH, HEIGHT = 1024, 768  # 画面の大きさ
CELL_SIZE = 32  # セルサイズを設定
ROWS, COLS = HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Game with Items")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# フレームレート
FPS = 60
clock = pygame.time.Clock()

# アイテム画像の読み込み
ITEM_IMAGES = {
    "hp": pygame.image.load("ex5/fig/hp.png"),
    "weapon": pygame.image.load("ex5/fig/sword1.png"),
    "invincible": pygame.image.load("ex5/fig/star.png"),
}

# アイテム画像をセルサイズにリサイズ
for key in ITEM_IMAGES:
    ITEM_IMAGES[key] = pygame.transform.scale(ITEM_IMAGES[key], (CELL_SIZE, CELL_SIZE))

# 迷路生成関数（ゴールを最も遠い点に置く）
def generate_maze(rows, cols):
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def carve_passages(cx, cy):
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # 上下左右
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx * 2, cy + dy * 2
            if 0 < nx < cols - 1 and 0 < ny < rows - 1 and maze[ny][nx] == 1:
                maze[cy + dy][cx + dx] = 0
                maze[ny][nx] = 0
                carve_passages(nx, ny)

    def find_furthest_point(start_x, start_y):
        distances = [[-1 for _ in range(cols)] for _ in range(rows)]
        pq = [(0, start_x, start_y)]  # ヒープの初期化
        distances[start_y][start_x] = 0
        furthest = (start_x, start_y, 0)

        while pq:
            dist, x, y = heapq.heappop(pq)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 0 and distances[ny][nx] == -1:
                    new_dist = dist + 1
                    distances[ny][nx] = new_dist
                    heapq.heappush(pq, (new_dist, nx, ny))
                    if new_dist > furthest[2]:
                        furthest = (nx, ny, new_dist)
        return furthest

    maze[1][1] = 0  # プレイヤー初期位置
    carve_passages(1, 1)
    furthest_x, furthest_y, _ = find_furthest_point(1, 1)
    maze[furthest_y][furthest_x] = 2  # ゴール位置
    return maze

# アイテムのクラス
class Item:
    def __init__(self, x, y, item_type):
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        self.type = item_type  # "hp", "weapon", "invincible"

    def draw(self):
        SCREEN.blit(ITEM_IMAGES[self.type], self.rect.topleft)

# アイテム生成関数
def generate_items(maze, num_items):
    items = []
    for _ in range(num_items):
        while True:
            x = random.randint(1, COLS - 2) * CELL_SIZE
            y = random.randint(1, ROWS - 2) * CELL_SIZE
            if maze[y // CELL_SIZE][x // CELL_SIZE] == 0:
                item_type = random.choice(["hp", "weapon", "invincible"])
                items.append(Item(x, y, item_type))
                break
    return items

# 迷路生成
maze = generate_maze(ROWS, COLS)

# 壁とゴールのリスト
walls = []
goal = None
for row_index, row in enumerate(maze):
    for col_index, cell in enumerate(row):
        if cell == 1:
            walls.append(pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        elif cell == 2:
            goal = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)

# プレイヤーの初期位置
player_size = CELL_SIZE // 2
player_x, player_y = CELL_SIZE + (CELL_SIZE // 4), CELL_SIZE + (CELL_SIZE // 4)
player_speed = 4

# ステータス
player_hp = 3
weapon_active = False
invincible = False
weapon_timer = 0
invincible_timer = 0
invincible_flash = False  # 無敵中の点滅状態

# アイテム生成
items = generate_items(maze, 5)

# 描画関数
# def draw_player(x, y):
#     if invincible:
#         global invincible_flash
#         invincible_flash = (invincible_flash + 1) % 30  # 点滅スピード調整（30フレームで切り替え）
#         color = YELLOW if invincible_flash < 15 else BLUE

#     else:
#         color = BLUE
#     pygame.draw.polygon(SCREEN, color, [
#         (x + player_size // 2, y),  # 上
#         (x + player_size, y + player_size // 2),  # 右
#         (x + player_size // 2, y + player_size),  # 下
#         (x, y + player_size // 2)  # 左
#     ])
PLAYER_IMAGE = pygame.image.load("ex5/fig/0.png")
PLAYER_IMAGE = pygame.transform.scale(PLAYER_IMAGE, (player_size, player_size))

def draw_player(x, y):
    global invincible_flash
    player_image = PLAYER_IMAGE.copy()
    
    if invincible:
        invincible_flash = (invincible_flash + 1) % 30  # 点滅スピード調整（30フレームで切り替え）
        if invincible_flash < 15:
            # 黄色く点滅
            yellow_tint = pygame.Surface(player_image.get_size())
            yellow_tint.fill(YELLOW)
            player_image.blit(yellow_tint, (0, 0), special_flags=pygame.BLEND_MULT)
    
    SCREEN.blit(player_image, (x, y))

def draw_maze():
    for wall in walls:
        pygame.draw.rect(SCREEN, BLACK, wall)
    pygame.draw.rect(SCREEN, GREEN, goal)

def display_game_clear():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Clear!", True, RED)
    SCREEN.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

# アイテム取得判定
def check_item_collision(player_rect, items):
    global player_hp, weapon_active, invincible, weapon_timer, invincible_timer
    for item in items[:]:
        if player_rect.colliderect(item.rect):
            if item.type == "hp":
                player_hp = min(player_hp + 1, 5)
            elif item.type == "weapon":
                weapon_active = True
                weapon_timer = 300
            elif item.type == "invincible":
                invincible = True
                invincible_timer = 300
            items.remove(item)

# ゲームループ
running = True
while running:
    SCREEN.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    new_x, new_y = player_x, player_y
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        new_y -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        new_y += player_speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        new_x -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        new_x += player_speed

    player_rect = pygame.Rect(new_x, new_y, player_size, player_size)
    if not any(player_rect.colliderect(wall) for wall in walls):
        player_x, player_y = new_x, new_y

    if player_rect.colliderect(goal):
        display_game_clear()
        running = False

    check_item_collision(player_rect, items)

    if weapon_active:
        weapon_timer -= 1
        if weapon_timer <= 0:
            weapon_active = False
    if invincible:
        invincible_timer -= 1
        if invincible_timer <= 0:
            invincible = False

    draw_maze()
    for item in items:
        item.draw()
    draw_player(player_x, player_y)

    # UI表示
    font = pygame.font.Font(None, 36)
    hp_text = font.render(f"HP: {player_hp}", True, RED)
    SCREEN.blit(hp_text, (10, 10))

    if weapon_active:
        SCREEN.blit(font.render("Weapon Active", True, (255, 165, 0)), (10, 50))
    if invincible:
        SCREEN.blit(font.render("Invincible", True, (0, 255, 255)), (10, 90))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()