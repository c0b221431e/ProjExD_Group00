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
    def __init__(self, x, y, speed):
        self.rect = pygame.Rect(x, y, CELL_SIZE // 2, CELL_SIZE // 2)
        self.speed = speed
        self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        self.color = random.choice([RED, (128, 0, 128), (255, 255, 0)])

    def move(self, walls):
        dx, dy = self.direction
        new_rect = self.rect.move(dx * self.speed, dy * self.speed)
        if not any(new_rect.colliderect(wall) for wall in walls):
            self.rect = new_rect
        else:
            self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.direction = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])

    def draw(self, screen):
        center = (self.rect.centerx, self.rect.centery)
        pygame.draw.circle(screen, self.color, center, self.rect.width // 2)
        eye_offset = self.rect.width // 4
        eye_radius = self.rect.width // 8
        pygame.draw.circle(screen, WHITE, (center[0] - eye_offset, center[1] - eye_offset), eye_radius)
        pygame.draw.circle(screen, WHITE, (center[0] + eye_offset, center[1] - eye_offset), eye_radius)
        pygame.draw.circle(screen, BLACK, (center[0] - eye_offset, center[1] - eye_offset), eye_radius // 2)
        pygame.draw.circle(screen, BLACK, (center[0] + eye_offset, center[1] - eye_offset), eye_radius // 2)

# 壁のデザイン
def draw_maze():
    for wall in walls:
        pygame.draw.rect(SCREEN, (139, 69, 19), wall)
        pygame.draw.rect(SCREEN, (160, 82, 45), wall.inflate(-2, -2))
    pygame.draw.rect(SCREEN, (0, 255, 0), goal)

# プレイヤーのデザイン
def draw_player(x, y):
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
for row_index, row in enumerate(maze):
    for col_index, cell in enumerate(row):
        if cell == 1:
            walls.append(pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        elif cell == 2:
            goal = pygame.Rect(col_index * CELL_SIZE, row_index * CELL_SIZE, CELL_SIZE, CELL_SIZE)

# 敵MOBの配置
mobs = []
while len(mobs) < 10:
    mob_x = random.randint(1, COLS - 2) * CELL_SIZE
    mob_y = random.randint(1, ROWS - 2) * CELL_SIZE
    mob_rect = pygame.Rect(mob_x, mob_y, CELL_SIZE // 2, CELL_SIZE // 2)
    if not any(mob_rect.colliderect(wall) for wall in walls):
        mobs.append(Mob(mob_x, mob_y, 2))

# プレイヤーの初期位置
player_size = CELL_SIZE // 2
player_x, player_y = CELL_SIZE + (CELL_SIZE // 4), CELL_SIZE + (CELL_SIZE // 4)
player_speed = 4

# 描画関数
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
    if not any(player_rect.colliderect(wall) for wall in walls):
        player_x, player_y = new_x, new_y

    if player_rect.colliderect(goal):
        display_game_clear()
        running = False

    for mob in mobs:
        mob.move(walls)
        mob.draw(SCREEN)
        if player_rect.colliderect(mob.rect):
            display_game_over()
            running = False

    draw_maze()
    draw_player(player_x, player_y)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
