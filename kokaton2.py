import pygame
import sys
import random
import heapq
import time

# Pygameの初期化
pygame.init()

# 画面の設定
WIDTH, HEIGHT = 1024, 768  # 画面の大きさ
CELL_SIZE = 32  # セルサイズを設定
ROWS, COLS = HEIGHT // CELL_SIZE, WIDTH // CELL_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Game with Invincibility")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)  # ダメージ壁の色

# フレームレート
FPS = 60
clock = pygame.time.Clock()

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

    # 最短距離検索でゴールを位置決定
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

# 迷路の生成
maze = generate_maze(ROWS, COLS)

# 壁とゴールのリスト
walls = []
damage_walls = []
goal = None
for row_index, row in enumerate(maze):
    for col_index, cell in enumerate(row):
        if cell == 1:
            wall_rect = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            walls.append(wall_rect)
            # 一定確率でダメージ壁を追加
            if random.random() < 0.2:  # 20%の確率でダメージ壁にする
                damage_walls.append(wall_rect)
        elif cell == 2:  # ゴールの位置
            goal = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)

# プレイヤーの初期設定
player_size = CELL_SIZE // 2
player_x, player_y = CELL_SIZE + (CELL_SIZE // 4), CELL_SIZE + (CELL_SIZE // 4)
player_speed = 4
player_health = 100  # プレイヤーの体力

# 無敵状態の管理
invincible = False
invincible_start_time = 0

# 描画関数
def draw_player(x, y, invincible):
    # 無敵状態なら点滅させる
    if invincible and int(time.time() * 5) % 2 == 0:  # 点滅効果
        return
    pygame.draw.rect(SCREEN, BLUE, (x, y, player_size, player_size))

def draw_maze():
    for wall in walls:
        if wall in damage_walls:
            pygame.draw.rect(SCREEN, YELLOW, wall)  # ダメージ壁は黄色
        else:
            pygame.draw.rect(SCREEN, BLACK, wall)
    pygame.draw.rect(SCREEN, GREEN, goal)

def display_game_clear():
    font = pygame.font.Font(None, 74)
    text = font.render("Game Clear!", True, RED)
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
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        new_x += player_speed

    player_rect = pygame.Rect(new_x, new_y, player_size, player_size)

    # 無敵状態の時間確認
    if invincible and time.time() - invincible_start_time > 2:
        invincible = False

    # 壁との衝突判定
    if not any(player_rect.colliderect(wall) for wall in walls):
        player_x, player_y = new_x, new_y

    # ダメージ壁との衝突判定
    if not invincible and any(player_rect.colliderect(d_wall) for d_wall in damage_walls):
        player_health -= 10  # 衝突ごとに体力を減少
        invincible = True  # 無敵状態を有効化
        invincible_start_time = time.time()  # 無敵状態開始時間を記録
        if player_health <= 0:
            display_game_over()
            running = False

    # ゴール判定
    if player_rect.colliderect(goal):
        display_game_clear()
        running = False

    # 描画処理
    draw_maze()
    draw_player(player_x, player_y, invincible)
    # 体力表示
    font = pygame.font.Font(None, 36)
    health_text = font.render(f"Health: {player_health}", True, RED)
    SCREEN.blit(health_text, (10, 10))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
