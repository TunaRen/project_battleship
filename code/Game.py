import pygame
import csv
from engine import Player, Game, DQNAgent, suggest_next_move_combined



pygame.init()
pygame.font.init()
pygame.display.set_caption("BattleShip")
myfont = pygame.font.SysFont("fresansttf", 100)

# globals for screen size
SQ_SIZE = 45
H_MARGIN = SQ_SIZE * 4
V_MARGIN = SQ_SIZE
WIDTH = SQ_SIZE * 10 * 2 + H_MARGIN
HEIGHT = SQ_SIZE * 10 * 2 + V_MARGIN
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

INDENT = 10

# colors
GREEN = (0, 255, 0)
GREY = (200, 200, 200)
WHITE = (255, 250, 250)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
COLORS = {"U": GREY, "M": BLUE, "H": ORANGE, "S": RED}
HUMAN1 = True
HUMAN2 = False

# function to draw grid
def draw_grid(player, left=0, top=0, search=False, heatmap=False, suggestion=False):
    for i in range(100):
        x = left + i % 10 * SQ_SIZE
        y = top + i // 10 * SQ_SIZE
        square = pygame.Rect(x, y, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(SCREEN, WHITE, square, width=3)
        if search:
            x += SQ_SIZE // 2
            y += SQ_SIZE // 2
            pygame.draw.circle(SCREEN, COLORS[player.search[i]], (x, y), SQ_SIZE // 4)
        if heatmap:
            pygame.draw.rect(SCREEN, COLORS[player.search[i]], square)
        if suggestion:
            if player.search[i] == "U":
                pygame.draw.circle(SCREEN, (255, 192, 203), (x + SQ_SIZE // 2, y + SQ_SIZE // 2), 5)
        

# function to draw onto the position grids
def draw_ships(play, left=0, top=0):
    for ship in play.ships:
        x = left + ship.col * SQ_SIZE + INDENT
        y = top + ship.row * SQ_SIZE + INDENT
        if ship.orientation == "h":
            width = ship.size * SQ_SIZE - 2 * INDENT
            height = SQ_SIZE - 2 * INDENT
        else:
            width = SQ_SIZE - 2 * INDENT
            height = ship.size * SQ_SIZE - 2 * INDENT
        rectangle = pygame.Rect(x, y, width, height)
        pygame.draw.rect(SCREEN, GREEN, rectangle, border_radius=15)

def draw_heatmap(player, left=0, top=0):
    for i in range(100):
        x = left + i % 10 * SQ_SIZE
        y = top + i // 10 * SQ_SIZE
        square = pygame.Rect(x, y, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(SCREEN, COLORS[player.search[i]], square)

def draw_suggestion(screen, row, col):
    x = col * SQ_SIZE + SQ_SIZE // 2
    y = row * SQ_SIZE + SQ_SIZE // 2
    pygame.draw.circle(screen, PINK, (x, y), SQ_SIZE // 4)


# Initialize player and game
player1 = Player()
player2 = Player()
game = Game(HUMAN1, HUMAN2)

agent = DQNAgent(state_size=2, action_size=2)
hit_probabilities = [[0] * 10 for _ in range(10)]

# List to track player moves
player_moves = []

def save_moves_to_csv(filename, moves):
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['Player', 'Row', 'Column']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Kiểm tra xem liệu file có trống không
        csvfile.seek(0, 2)  # Đưa con trỏ tệp về cuối file
        empty = csvfile.tell() == 0
        if empty:  # Nếu file trống, viết header
            writer.writeheader()
        # Ghi các nước đi mới vào file
        start_index = max(0, len(moves) - game.n_shot)  # Chỉ ghi từ bước đi cuối cùng của lượt chơi trước đó
        for move in moves[start_index:]:
            writer.writerow(move)

# Function to record player moves
def record_player_move(game, row, col):
    global player_moves
    if game.play1_turn:  
        player_moves = [{'Player': 1, 'Row': row, 'Column': col}]
    else:  
        player_moves = [{'Player': 2, 'Row': row, 'Column': col}]
        save_moves_to_csv('playermoves.csv', player_moves)  # Lưu giá trị sau mỗi lượt bắn của cả người chơi và máy tính
        if not game.over:  # Nếu trò chơi chưa kết thúc
            if (game.human1 and not game.human2) or (not game.human1 and game.human2):  # Nếu lượt kế tiếp là của máy tính
                game.basic_ai()  # Máy tính thực hiện nước đi của mình
                player_moves = []

# Pygame main loop
animation = True
pausing = False
while animation:
    # Track user interaction
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            animation = False
        if event.type == pygame.MOUSEBUTTONDOWN and not game.over:
            x, y = pygame.mouse.get_pos()
            if game.play1_turn and x < SQ_SIZE * 10 and y < SQ_SIZE * 10:
                row = y // SQ_SIZE
                col = x // SQ_SIZE
                index = row * 10 + col
                game.make_move(index)
                record_player_move(game, row, col)
            elif not game.play1_turn and x > WIDTH - SQ_SIZE * 10 and y > SQ_SIZE * 10 + V_MARGIN:
                row = (y - SQ_SIZE * 10 - V_MARGIN) // SQ_SIZE
                col = (x - SQ_SIZE * 10 - H_MARGIN) // SQ_SIZE
                index = row * 10 + col
                game.make_move(index)
                record_player_move(game, row, col)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                animation = False
            if event.key == pygame.K_SPACE:
                pausing = not pausing
            if event.key == pygame.K_RETURN:
                game = Game(HUMAN1, HUMAN2)
                player_moves = []

    if not pausing:
        # Draw background
        SCREEN.fill(GREY)

        # Draw grid
        draw_grid(game.player1, search=True)
        draw_grid(game.player2, search=True, left=(WIDTH - H_MARGIN) // 2 + H_MARGIN, top=(HEIGHT - V_MARGIN) // 2 + V_MARGIN)

        # Draw heatmap
        draw_heatmap(game.player2, top=(HEIGHT - V_MARGIN) // 2 + V_MARGIN)
        draw_heatmap(game.player1, left=(WIDTH - H_MARGIN) // 2 + H_MARGIN)

        # Draw position grid
        draw_grid(game.player1, top=(HEIGHT - V_MARGIN) // 2 + V_MARGIN)
        draw_grid(game.player2, left=(WIDTH - H_MARGIN) // 2 + H_MARGIN)

        # Draw ships onto the position grid
        draw_ships(game.player1, top=(HEIGHT - V_MARGIN) // 2 + V_MARGIN)
        draw_ships(game.player2, left=(WIDTH - H_MARGIN) // 2 + H_MARGIN)
        
         # Gợi ý nước đánh tiếp theo
        row_suggestion, col_suggestion = suggest_next_move_combined(agent, game.player1, hit_probabilities)
        if row_suggestion is not None and col_suggestion is not None:
            draw_suggestion(SCREEN, row_suggestion, col_suggestion)

        # Computer moves
        if game.computer_turn and not game.over:
            if game.play1_turn:
                game.basic_ai()
            else:
                game.basic_ai()
        
        # Game over message
        if game.over:
            text = "Player " + str(game.result) + " wins!"
            textbox = myfont.render(text, False, GREY, WHITE)
            SCREEN.blit(textbox, (WIDTH // 4, HEIGHT // 2))
        
         # Ghi vào tệp khi trò chơi kết thúc
        save_moves_to_csv('playermoves.csv', player_moves)

        # Update screen
        pygame.time.wait(100)
        pygame.display.flip()
