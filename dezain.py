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
pygame.display.set_caption("Maze Game")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)  # 敵MOBの色
YELLOW = (255, 255, 0)  # アイテムの色
PURPLE = (128, 0, 128)  # 新しい敵の色
MAGMA = (255, 69, 0)  # ダメージウォールの色

# フレームレート
FPS = 60
clock = pygame.time.Clock()

# スコアシステム
score = 0
invincible = False
invincible_timer = 0

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

# 敵MOBクラス
class Mob:
    def __init__(self, x, y, speed, mob_type="normal"):
        self.rect = pygame.Rect(x, y, CELL_SIZE // 2, CELL_SIZE // 2)
        self.speed = speed
        self.type = mob_type
        self.color = RED if mob_type == "normal" else PURPLE
        self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])

    def move(self, player_x, player_y, walls):
        if self.type == "tracker":
            dx = 1 if player_x > self.rect.x else -1 if player_x < self.rect.x else 0
            dy = 1 if player_y > self.rect.y else -1 if player_y < self.rect.y else 0
            new_rect = self.rect.move(dx * self.speed, dy * self.speed)
        else:
            dx, dy = self.direction
            new_rect = self.rect.move(dx * self.speed, dy * self.speed)

        if not any(new_rect.colliderect(wall) for wall in walls):
            self.rect = new_rect
        else:
            self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.rect.center, self.rect.width // 2)

# アイテムクラス
class Item:
    def __init__(self, x, y, item_type):
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        self.type = item_type

    def draw(self, screen):
        if self.type == "heal":
            pygame.draw.rect(screen, GREEN, self.rect)  # 緑の四角形（回復アイテム）
            pygame.draw.line(screen, WHITE, self.rect.topleft, self.rect.bottomright, 2)
            pygame.draw.line(screen, WHITE, self.rect.topright, self.rect.bottomleft, 2)
        elif self.type == "score":
            pygame.draw.circle(screen, YELLOW, self.rect.center, self.rect.width // 3)  # 黄色のコイン（スコアアイテム）

# ダメージウォールクラス
class DamageWall:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    def draw(self, screen):
        pygame.draw.rect(screen, MAGMA, self.rect)
        pygame.draw.rect(screen, (255, 140, 0), self.rect.inflate(-4, -4))

# 壁のデザイン
def draw_maze():
    for wall in walls:
        pygame.draw.rect(SCREEN, (139, 69, 19), wall)
        pygame.draw.rect(SCREEN, (160, 82, 45), wall.inflate(-2, -2))
    pygame.draw.rect(SCREEN, (0, 255, 0), goal)

# プレイヤーのデザイン
def draw_player(x, y, invincible):
    if invincible and pygame.time.get_ticks() % 300 < 150:
        return  # 点滅状態で描画をスキップ
    pygame.draw.circle(SCREEN, BLUE, (x + player_size // 2, y + player_size // 2), player_size // 2)
    hat_top = (x + player_size // 2, y + player_size // 4)
    hat_left = (x + player_size // 4, y + player_size // 2)
    hat_right = (x + player_size * 3 // 4, y + player_size // 2)
    pygame.draw.polygon(SCREEN, (0, 0, 255), [hat_top, hat_left, hat_right])

# 迷路の生成
maze = generate_maze(ROWS, COLS)

# 壁とゴールのリスト
walls = []
goal = None
damage_walls = []
for row_index, row in enumerate(maze):
    for col_index, cell in enumerate(row):
        if cell == 1:
            wall_rect = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            walls.append(wall_rect)
            # 通路に隣接している壁をダメージウォールにする
            if any(maze[row_index + dy][col_index + dx] == 0 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)] if 0 <= row_index + dy < ROWS and 0 <= col_index + dx < COLS):
                damage_walls.append(DamageWall(col_index * CELL_SIZE, row_index * CELL_SIZE))
        elif cell == 2:
            goal = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)

# 敵MOBの配置
mobs = []
while len(mobs) < 5:
    mob_x = random.randint(1, COLS - 2) * CELL_SIZE
    mob_y = random.randint(1, ROWS - 2) * CELL_SIZE
    mob_rect = pygame.Rect(mob_x, mob_y, CELL_SIZE // 2, CELL_SIZE // 2)
    if not any(mob_rect.colliderect(wall) for wall in walls):
        mob_type = "tracker" if random.random() > 0.7 else "normal"
        mobs.append(Mob(mob_x, mob_y, 2, mob_type))

# アイテムの配置
items = []
for _ in range(5):
    item_x = random.randint(1, COLS - 2) * CELL_SIZE
    item_y = random.randint(1, ROWS - 2) * CELL_SIZE
    temp_rect = pygame.Rect(item_x, item_y, CELL_SIZE, CELL_SIZE)
    if not any(temp_rect.colliderect(wall) for wall in walls) and not any(temp_rect.colliderect(existing_item.rect) for existing_item in items):
        items.append(Item(item_x, item_y, random.choice(["heal", "score"])))

# プレイヤーの初期位置
player_size = CELL_SIZE // 2
player_x, player_y = CELL_SIZE + (CELL_SIZE // 4), CELL_SIZE + (CELL_SIZE // 4)
player_speed = 4
player_hp = 3

# 描画関数
def display_game_clear():
    font = pygame.font.Font(None, 74)
    text = font.render(f"Game Clear! Score: {score}", True, RED)
    SCREEN.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

def display_game_over():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Over!", True, RED)
    SCREEN.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.flip()
    pygame.time.wait(3000)

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
