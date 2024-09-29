import pygame
import os

# Initialize Pygame
pygame.init()

# Set up the display
window_width, window_height = 900, 800
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption('Chess with Evaluation Bar')

# Define board properties
num_squares = 8
board_size = 650
square_size = board_size // num_squares

# Calculate the top-left corner position of the checkered board to center it
board_x = (window_width - board_size - 100) // 2
board_y = (window_height - board_size) // 2

# Define colors
color1 = (255, 255, 255)  # White color
color2 = (60, 60, 60)  # Black color
background_color = (128, 170, 100)  # Background color
highlight_color = (255, 255, 0)  # Yellow highlight
capture_highlight_color = (255, 0, 0)  # Red highlight for captures
check_highlight_color = (255, 165, 0)  # Orange highlight for check


def load_images():
    images = {}
    pieces = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
    colors = ['black', 'white']
    for color in colors:
        for piece in pieces:
            image_path = f'{color}-{piece}1.png'
            if os.path.isfile(image_path):
                try:
                    images[f'{color}-{piece}'] = pygame.transform.scale(
                        pygame.image.load(image_path),
                        (square_size, square_size)
                    )
                except pygame.error as e:
                    print(f"Could not load image {image_path}: {e}")
            else:
                print(f"Image file not found: {image_path}")
    return images


pieces_images = load_images()

# Define the standard starting positions for all pieces
initial_pieces = {
    'black-rook': [(0, 0), (0, 7)], 'black-knight': [(0, 1), (0, 6)], 'black-bishop': [(0, 2), (0, 5)],
    'black-queen': [(0, 3)], 'black-king': [(0, 4)],
    'black-pawn': [(1, i) for i in range(8)],
    'white-rook': [(7, 0), (7, 7)], 'white-knight': [(7, 1), (7, 6)], 'white-bishop': [(7, 2), (7, 5)],
    'white-queen': [(7, 3)], 'white-king': [(7, 4)],
    'white-pawn': [(6, i) for i in range(8)]
}

# Keep track of whether kings and rooks have moved (for castling)
piece_moved = {
    'white-king': False, 'black-king': False,
    'white-rook': [False, False], 'black-rook': [False, False]
}


def is_valid_move(piece, start, end, pieces, check_for_check=True):
    piece_type = piece.split('-')[1]
    color = piece.split('-')[0]
    start_row, start_col = start
    end_row, end_col = end

    if any(end in positions for p, positions in pieces.items() if p.startswith(color)):
        return False

    def is_path_clear(start, end):
        row_step = 1 if end_row > start_row else -1 if end_row < start_row else 0
        col_step = 1 if end_col > start_col else -1 if end_col < start_col else 0
        row, col = start_row + row_step, start_col + col_step
        while (row, col) != end:
            if any((row, col) in positions for positions in pieces.values()):
                return False
            row, col = row + row_step, col + col_step
        return True

    if piece_type == 'pawn':
        direction = -1 if color == 'white' else 1
        if start_col == end_col and (end_row, end_col) not in sum(pieces.values(), []):
            if start_row + direction == end_row:
                return True
            if (color == 'white' and start_row == 6) or (color == 'black' and start_row == 1):
                return start_row + 2 * direction == end_row
        return (end_row == start_row + direction and abs(end_col - start_col) == 1 and
                any((end_row, end_col) in positions for p, positions in pieces.items() if not p.startswith(color)))

    elif piece_type == 'rook':
        return (start_row == end_row or start_col == end_col) and is_path_clear(start, end)
    elif piece_type == 'knight':
        return (abs(start_row - end_row), abs(start_col - end_col)) in [(2, 1), (1, 2)]
    elif piece_type == 'bishop':
        return abs(start_row - end_row) == abs(start_col - end_col) and is_path_clear(start, end)
    elif piece_type == 'queen':
        return ((start_row == end_row or start_col == end_col or
                 abs(start_row - end_row) == abs(start_col - end_col)) and
                is_path_clear(start, end))
    elif piece_type == 'king':
        row_diff = abs(start_row - end_row)
        col_diff = abs(start_col - end_col)
        if row_diff <= 1 and col_diff <= 1:
            return True
        if not piece_moved[f'{color}-king'] and row_diff == 0 and col_diff == 2:
            rook_col = 7 if end_col == 6 else 0
            rook_index = 1 if end_col == 6 else 0
            if not piece_moved[f'{color}-rook'][rook_index]:
                return is_path_clear(start, (start_row, rook_col))
        return False

    return False


def is_in_check(color, pieces):
    king_pos = next(pos[0] for piece, pos in pieces.items() if piece == f'{color}-king')
    opponent_color = 'black' if color == 'white' else 'white'

    for piece, positions in pieces.items():
        if piece.startswith(opponent_color):
            for pos in positions:
                if is_valid_move(piece, pos, king_pos, pieces, check_for_check=False):
                    return True
    return False


def is_checkmate(color, pieces):
    if not is_in_check(color, pieces):
        return False

    for piece, positions in pieces.items():
        if piece.startswith(color):
            for start in positions:
                for end_row in range(8):
                    for end_col in range(8):
                        if is_valid_move(piece, start, (end_row, end_col), pieces):
                            new_pieces = {k: v.copy() for k, v in pieces.items()}
                            new_pieces[piece].remove(start)
                            new_pieces[piece].append((end_row, end_col))
                            for p, pos in new_pieces.items():
                                if p != piece and (end_row, end_col) in pos:
                                    new_pieces[p].remove((end_row, end_col))
                                    break
                            if not is_in_check(color, new_pieces):
                                return False
    return True


def evaluate_position(pieces):
    piece_values = {
        'pawn': 100, 'knight': 320, 'bishop': 330, 'rook': 500, 'queen': 900, 'king': 20000
    }

    # Center squares
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]

    # Piece-square tables 
    pst = {
        'pawn': [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ],
        'knight': [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 0, 0, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 20, 20, 15, 0, -30],
            [-30, 5, 10, 15, 15, 10, 5, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ],
        'bishop': [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 5, 10, 10, 5, 5, -10],
            [-10, 0, 10, 10, 10, 10, 0, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ],
        'rook': [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [0, 0, 0, 5, 5, 0, 0, 0]
        ],
        'queen': [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [0, 0, 5, 5, 5, 5, 0, -5],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20]
        ],
        'king_midgame': [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20]
        ],
        'king_endgame': [
            [-50, -40, -30, -20, -20, -30, -40, -50],
            [-30, -20, -10, 0, 0, -10, -20, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -30, 0, 0, 0, 0, -30, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]
    }

    white_score = 0
    black_score = 0
    white_material = 0
    black_material = 0

    for piece, positions in pieces.items():
        color, piece_type = piece.split('-')
        for position in positions:
            row, col = position
            value = piece_values[piece_type]

            if color == 'white':
                white_material += value
                white_score += value
                if piece_type != 'king':
                    white_score += pst[piece_type][row][col]
                else:
                    if white_material > 5000:  # Rough estimate for midgame
                        white_score += pst['king_midgame'][row][col]
                    else:
                        white_score += pst['king_endgame'][row][col]
                if position in center_squares:
                    white_score += 10
            else:
                black_material += value
                black_score += value
                if piece_type != 'king':
                    black_score += pst[piece_type][7 - row][col]
                else:
                    if black_material > 5000:  # Rough estimate for midgame
                        black_score += pst['king_midgame'][7 - row][col]
                    else:
                        black_score += pst['king_endgame'][7 - row][col]
                if position in center_squares:
                    black_score += 10

    # King safety (simplified)
    white_king_pos = next(pos[0] for piece, pos in pieces.items() if piece == 'white-king')
    black_king_pos = next(pos[0] for piece, pos in pieces.items() if piece == 'black-king')

    white_king_safety = 0
    black_king_safety = 0

    if white_material > 5000:  # Only consider king safety in midgame
        white_king_safety = 5 * (7 - white_king_pos[0])  # Encourage the king to stay back
    if black_material > 5000:
        black_king_safety = 5 * black_king_pos[0]  # Encourage the king to stay back

    white_score += white_king_safety
    black_score += black_king_safety

    return white_score - black_score


def draw_evaluation_bar(window, evaluation):
    bar_width = 20
    bar_height = 400
    bar_x = window_width - 30
    bar_y = (window_height - bar_height) // 2

    max_eval = 2000  # Maximum evaluation difference to show
    normalized_eval = max(min(evaluation / max_eval, 1), -1)

    white_height = int((0.5 + normalized_eval / 2) * bar_height)
    black_height = bar_height - white_height

    pygame.draw.rect(window, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(window, (255, 255, 255), (bar_x, bar_y + black_height, bar_width, white_height))
    pygame.draw.rect(window, (0, 0, 0), (bar_x, bar_y, bar_width, black_height))

    pygame.draw.line(window, (100, 100, 100), (bar_x, bar_y + bar_height // 2),
                     (bar_x + bar_width, bar_y + bar_height // 2))


# Main loop
running = True
dragging = False
dragged_piece = None
dragged_piece_index = None
drag_offset = (0, 0)
valid_moves = []
capture_moves = []
current_turn = 'white'
game_over = False
winner = None
evaluation = 0

font = pygame.font.Font(None, 36)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                clicked_row = (mouse_pos[1] - board_y) // square_size
                clicked_col = (mouse_pos[0] - board_x) // square_size

                if 0 <= clicked_row < 8 and 0 <= clicked_col < 8:
                    for piece, positions in initial_pieces.items():
                        if (clicked_row, clicked_col) in positions and piece.startswith(current_turn):
                            dragging = True
                            dragged_piece = piece
                            dragged_piece_index = positions.index((clicked_row, clicked_col))
                            drag_offset = (mouse_pos[0] - (board_x + clicked_col * square_size),
                                           mouse_pos[1] - (board_y + clicked_row * square_size))
                            start = (clicked_row, clicked_col)
                            valid_moves = [(r, c) for r in range(8) for c in range(8) if
                                           is_valid_move(piece, start, (r, c), initial_pieces)]
                            capture_moves = [(r, c) for r, c in valid_moves if
                                             any((r, c) in positions for p, positions in initial_pieces.items() if
                                                 not p.startswith(current_turn))]
                            break

        elif event.type == pygame.MOUSEBUTTONUP and not game_over:
            if event.button == 1 and dragging:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                dropped_row = (mouse_pos[1] - board_y) // square_size
                dropped_col = (mouse_pos[0] - board_x) // square_size

                if 0 <= dropped_row < 8 and 0 <= dropped_col < 8 and (dropped_row, dropped_col) in valid_moves:
                    start = initial_pieces[dragged_piece][dragged_piece_index]

                    if dragged_piece.endswith('king') and abs(dropped_col - start[1]) == 2:
                        rook_piece = f'{current_turn}-rook'
                        rook_index = 1 if dropped_col == 6 else 0
                        rook_new_col = 5 if dropped_col == 6 else 3
                        initial_pieces[rook_piece][rook_index] = (dropped_row, rook_new_col)
                        piece_moved[rook_piece][rook_index] = True

                    for p, positions in initial_pieces.items():
                        if (dropped_row, dropped_col) in positions and not p.startswith(current_turn):
                            positions.remove((dropped_row, dropped_col))
                            break

                    initial_pieces[dragged_piece][dragged_piece_index] = (dropped_row, dropped_col)
                    if dragged_piece.endswith(('king', 'rook')):
                        piece_moved[dragged_piece] = True if dragged_piece.endswith('king') else [True] * 2

                    current_turn = 'black' if current_turn == 'white' else 'white'

                    if is_checkmate(current_turn, initial_pieces):
                        game_over = True
                        winner = 'White' if current_turn == 'black' else 'Black'

                    evaluation = evaluate_position(initial_pieces)

                dragging = False
                dragged_piece = None
                dragged_piece_index = None
                valid_moves = []
                capture_moves = []

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_pos = pygame.mouse.get_pos()

    window.fill(background_color)

    for row in range(num_squares):
        for col in range(num_squares):
            color = color1 if (row + col) % 2 == 0 else color2
            pygame.draw.rect(window, color,
                             pygame.Rect(board_x + col * square_size, board_y + row * square_size, square_size,
                                         square_size))

    for move in valid_moves:
        color = capture_highlight_color if move in capture_moves else highlight_color
        pygame.draw.rect(window, color,
                         pygame.Rect(board_x + move[1] * square_size, board_y + move[0] * square_size, square_size,
                                     square_size), 4)

    for piece_name, positions in initial_pieces.items():
        for i, (row, col) in enumerate(positions):
            if piece_name in pieces_images and (piece_name != dragged_piece or i != dragged_piece_index):
                window.blit(pieces_images[piece_name],
                            pygame.Rect(board_x + col * square_size, board_y + row * square_size, square_size,
                                        square_size))

    if dragging and dragged_piece in pieces_images:
        mouse_pos = pygame.mouse.get_pos()
        window.blit(pieces_images[dragged_piece],
                    pygame.Rect(mouse_pos[0] - drag_offset[0], mouse_pos[1] - drag_offset[1], square_size, square_size))

    if is_in_check(current_turn, initial_pieces):
        king_pos = next(pos[0] for piece, pos in initial_pieces.items() if piece == f'{current_turn}-king')
        pygame.draw.rect(window, check_highlight_color,
                         pygame.Rect(board_x + king_pos[1] * square_size, board_y + king_pos[0] * square_size,
                                     square_size, square_size), 4)

    draw_evaluation_bar(window, evaluation)

    turn_text = font.render(f"Current turn: {current_turn.capitalize()}", True, (255, 255, 255))
    window.blit(turn_text, (10, 10))

    eval_text = font.render(f"Eval: {evaluation / 100:.2f}", True, (255, 255, 255))
    window.blit(eval_text, (window_width - 125, 10))

    if game_over:
        victory_text = font.render(f"{winner} wins!", True, (255, 255, 255))
        text_rect = victory_text.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(victory_text, text_rect)

    pygame.display.flip()

pygame.quit()
