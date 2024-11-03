"""
Moksh S. GHP Project 2024
ChessMain.py
Main Driver for our Chess Engine
This will handle user input and updating the graphics
"""

# Import the necessary libraries
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as p
import ChessEngine, ChessAI
import sys
import os
from multiprocessing import Process, Queue
import tkinter as tk
from tkinter import filedialog

# Initialize global variables
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
END_GAME_BUTTON_X = BOARD_WIDTH + 20
END_GAME_BUTTON_Y = BOARD_HEIGHT - 60
END_GAME_BUTTON_WIDTH = 200
END_GAME_BUTTON_HEIGHT = 40
MAX_FPS = 10
IMAGES = {}

# Main Function
def main():

    # Initialize pygame and the GUI
    p.init()
    p.display.set_caption("The Engine")
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))

    # Display the start screen and get player's choice
    player_choice = showStartScreen(screen, clock)
    if (player_choice is None):
        p.quit()
        sys.exit()

    # If Human is playing as white, AI becomes black
    player_one = player_choice == "white"  
    player_two = not player_one 

    # Initialize the game state and other variables 
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # Variable for when a move is made
    animate = False  # Variable for when we should animate a move
    loadImages() 
    running = True
    square_selected = ()  # No square is selected initially, this will keep track of the last click of the user (tuple(row,col))
    player_clicks = []  # This will keep track of player clicks (two tuples)
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)

    while running:

        # Initialize pgn_string with a default value
        pgn_string = ""

        # Determine if it's the human's turn based on player choice
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if (e.type == p.QUIT):
                p.quit()
                sys.exit()

            # Mouse handler
            elif (e.type == p.MOUSEBUTTONDOWN):
                if (not game_over):
                    location = p.mouse.get_pos()  # Location of the mouse
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE

                    # If the board is flipped, adjust the row and column for the click
                    if (not player_one):  # Human is playing black, so board is flipped
                        row = DIMENSION - 1 - row
                        col = DIMENSION - 1 - col

                    # User clicked the same square twice
                    if (square_selected == (row, col) or col >= 8):
                        square_selected = ()  # Deselect
                        player_clicks = []  # Clear clicks
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # Append for both 1st and 2nd click
                    if (len(player_clicks) == 2 and human_turn):  # After 2nd click
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if (move == valid_moves[i]):
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  # Reset user clicks
                                player_clicks = []
                        if (not move_made):
                            player_clicks = [square_selected]

            # Key handler
            elif (e.type == p.KEYDOWN):

                # Undo when 'z' is pressed
                if (e.key == p.K_z):  
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if (ai_thinking):
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

                # Reset the game when 'r' is pressed
                if (e.key == p.K_r): 
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if (ai_thinking):
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

                elif e.type == p.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = p.mouse.get_pos()
                    
                    # Check if the end game button is clicked
                    if (END_GAME_BUTTON_X <= mouse_x <= END_GAME_BUTTON_X + END_GAME_BUTTON_WIDTH and
                        END_GAME_BUTTON_Y <= mouse_y <= END_GAME_BUTTON_Y + END_GAME_BUTTON_HEIGHT):
                        savePGNToFile(pgn_string)

        if (not game_over and not human_turn and not move_undone):
            if (not ai_thinking):
                ai_thinking = True
                return_queue = Queue()  # Used to pass data between threads
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if (move_finder_process and not move_finder_process.is_alive()):
                try:
                    ai_move = return_queue.get_nowait()
                except:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False
                move_finder_process = None  # Reset process after completion

        if (move_made):
            if (animate):
                animateMove(game_state.move_log[-1], screen, game_state.board, clock, not player_one)  # Pass flip_board
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected, player_one)  # Pass player_one to control board flip

        if (not game_over):
            drawMoveLog(screen, game_state, move_log_font)
        else:
            # Draw PGN save button when the game is over
            pgn_string = generatePGN(game_state.move_log)
            drawEndGameButton(screen, "Save PGN", BOARD_WIDTH + 20, BOARD_HEIGHT - 60, 200, 40, pgn_string)

        if (game_state.checkmate):
            game_over = True
            if (game_state.white_to_move):
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")
        elif (game_state.stalemate):
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()

# Display the start screen where the user can choose to play as white or black
def showStartScreen(screen, clock):

    # Set GUI font and button rectangles
    title_font = p.font.SysFont("Arial", 36, True)
    button_font = p.font.SysFont("Arial", 24)
    white_button_rect = p.Rect(275, 225, 200, 50)
    black_button_rect = p.Rect(275, 300, 200, 50)

    while True:
        screen.fill(p.Color("gray"))
        
        # Draw title text
        title_text = title_font.render("Welcome to The Engine!", True, p.Color("black"))
        screen.blit(title_text, (BOARD_WIDTH // 2 - title_text.get_width() // 2 + 125, 150))

        # Draw white button
        p.draw.rect(screen, (255, 255, 255), white_button_rect)
        white_text = button_font.render("Play as White", True, p.Color("black"))
        screen.blit(white_text, (white_button_rect.x + white_button_rect.width // 2 - white_text.get_width() // 2,
                                 white_button_rect.y + white_button_rect.height // 2 - white_text.get_height() // 2))

        # Draw black button
        p.draw.rect(screen, (0, 0, 0), black_button_rect)
        black_text = button_font.render("Play as Black", True, p.Color("white"))
        screen.blit(black_text, (black_button_rect.x + black_button_rect.width // 2 - black_text.get_width() // 2,
                                 black_button_rect.y + black_button_rect.height // 2 - black_text.get_height() // 2))

        # Event handling for button clicks
        for event in p.event.get():
            if (event.type == p.QUIT):
                return None  # Exit the program
            elif (event.type == p.MOUSEBUTTONDOWN):
                if white_button_rect.collidepoint(event.pos):
                    return "white"
                elif (black_button_rect.collidepoint(event.pos)):
                    return "black"

        p.display.flip()
        clock.tick(15)

# Load the images of the chess pieces
def loadImages():

    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    img_dir = os.path.join(os.path.dirname(__file__), "images")  # Use absolute path to the images directory
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(os.path.join(img_dir, piece + ".png")), (SQUARE_SIZE, SQUARE_SIZE))

# Responsible for all the graphics within the current game state
def drawGameState(screen, game_state, valid_moves, square_selected, player_one):

    flip_board = not player_one  # Flip the board if player is black
    drawBoard(screen, flip_board)  # Draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected, player_one)
    drawPieces(screen, game_state.board, flip_board)  # Draw pieces on top of those squares

# Draw the squares on the board
def drawBoard(screen, flip_board):

    global colors
    colors = [p.Color("white"), p.Color("gray")]

    for row in range(DIMENSION):
        for col in range(DIMENSION):

            # If flip_board is True, reverse the row and column indices to flip the board
            actual_row = row if not flip_board else DIMENSION - 1 - row
            actual_col = col if not flip_board else DIMENSION - 1 - col

            color = colors[((actual_row + actual_col) % 2)]
            p.draw.rect(screen, color, p.Rect(actual_col * SQUARE_SIZE, actual_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Highlight the selected square and all valid moves for the selected piece
def highlightSquares(screen, game_state, valid_moves, square_selected, player_one):

    flip_board = not player_one  # Flip the board if player is black

    if (len(game_state.move_log) > 0):
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))

        # Flip last move coordinates if needed
        end_row = last_move.end_row if not flip_board else DIMENSION - 1 - last_move.end_row
        end_col = last_move.end_col if not flip_board else DIMENSION - 1 - last_move.end_col
        screen.blit(s, (end_col * SQUARE_SIZE, end_row * SQUARE_SIZE))

    if (square_selected != ()):
        row, col = square_selected

        # Flip selected square coordinates if needed
        selected_row = row if not flip_board else DIMENSION - 1 - row
        selected_col = col if not flip_board else DIMENSION - 1 - col

        # Ensure the selected piece matches the current turn color
        if (game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b')):
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (selected_col * SQUARE_SIZE, selected_row * SQUARE_SIZE))

            # Highlight all possible moves for this piece
            s.fill(p.Color('yellow'))
            for move in valid_moves:

                # Check if move's start matches selected piece's position
                start_row = move.start_row
                start_col = move.start_col

                # Check for valid moves only for the piece selected
                if (start_row == row and start_col == col):

                    # Flip end position of the move if necessary
                    end_row = move.end_row if not flip_board else DIMENSION - 1 - move.end_row
                    end_col = move.end_col if not flip_board else DIMENSION - 1 - move.end_col
                    screen.blit(s, (end_col * SQUARE_SIZE, end_row * SQUARE_SIZE))

# Draw the pieces on the board
def drawPieces(screen, board, flip_board):

    for row in range(DIMENSION):
        for col in range(DIMENSION):

            # Flip coordinates if needed
            actual_row = row if not flip_board else DIMENSION - 1 - row
            actual_col = col if not flip_board else DIMENSION - 1 - col
            piece = board[row][col]
            if (piece != "--"):
                screen.blit(IMAGES[piece], p.Rect(actual_col * SQUARE_SIZE, actual_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Animate the move
def animateMove(move, screen, board, clock, flip_board):

    delta_r = move.end_row - move.start_row
    delta_c = move.end_col - move.start_col
    frames_per_square = 10 
    frame_count = (abs(delta_r) + abs(delta_c)) * frames_per_square

    piece_img = IMAGES[move.piece_moved]
    
    # Calculate start and end coordinates
    start_row = move.start_row if not flip_board else DIMENSION - 1 - move.start_row
    start_col = move.start_col if not flip_board else DIMENSION - 1 - move.start_col
    end_row = move.end_row if not flip_board else DIMENSION - 1 - move.end_row
    end_col = move.end_col if not flip_board else DIMENSION - 1 - move.end_col

    start_x, start_y = start_col * SQUARE_SIZE, start_row * SQUARE_SIZE
    end_x, end_y = end_col * SQUARE_SIZE, end_row * SQUARE_SIZE

    for frame in range(frame_count + 1):

        # Linear interpolation
        current_x = start_x + (end_x - start_x) * frame / frame_count
        current_y = start_y + (end_y - start_y) * frame / frame_count

        # Draw board and pieces except the moving piece
        drawBoard(screen, flip_board)
        drawPieces(screen, board, flip_board)

        # "Erase" the piece from the ending square (to handle captures)
        color = colors[(end_row + end_col) % 2]
        end_square = p.Rect(end_x, end_y, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        
        # Draw captured piece if there is one
        if (move.piece_captured != '--'):
            screen.blit(IMAGES[move.piece_captured], end_square)

        # Draw the moving piece at its current animated position
        screen.blit(piece_img, p.Rect(current_x, current_y, SQUARE_SIZE, SQUARE_SIZE))

        p.display.flip()
        clock.tick(60)  # Higher FPS for smoother animation

# Draw the move log
def drawMoveLog(screen, game_state, font):

    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + ". " + str(move_log[i]) + " "
        if (i + 1 < len(move_log)):  # Make sure black made a move
            move_string += str(move_log[i + 1])
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    text_y = padding
    line_spacing = 2
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if (i + j < len(move_texts)):
                text += move_texts[i + j] + "  "
        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing

# Draw the end game text
def drawEndGameText(screen, text):

    font = p.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, 0, p.Color('Gray'))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH // 2 - text_object.get_width() // 2,
                                                                 BOARD_HEIGHT // 2 - text_object.get_height() // 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color('Black'))
    screen.blit(text_object, text_location.move(2, 2))

# Generate a PGN string from the move log
def generatePGN(move_log):

    pgn = []
    for i in range(0, len(move_log), 2):
        move_number = f"{i // 2 + 1}. {move_log[i]}"
        if (i + 1 < len(move_log)):
            move_number += f" {move_log[i + 1]}"
        pgn.append(move_number)
    return " ".join(pgn)

# Create a button to save the PGN
def drawEndGameButton(screen, text, x, y, width, height, pgn_string):

    font = p.font.SysFont("Arial", 24)
    button_color = (180, 180, 180)
    p.draw.rect(screen, button_color, (x, y, width, height))
    text_surf = font.render(text, True, (0, 0, 0))
    screen.blit(text_surf, (x + width // 2 - text_surf.get_width() // 2, y + height // 2 - text_surf.get_height() // 2))

    # Check if button is clicked and save PGN
    if p.mouse.get_pressed()[0]:
        mouse_x, mouse_y = p.mouse.get_pos()
        if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
            savePGNToFile(pgn_string) 

# Save the PGN to a file
def savePGNToFile(pgn_string):

    # Initialize Tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a save file dialog
    file_path = filedialog.asksaveasfilename(defaultextension=".pgn", 
                                             filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
                                             title="Save PGN")
    
    # Only proceed if the user selects a file
    if (file_path):
        with open(file_path, "w") as file:
            file.write(pgn_string)

# Run the main function
if (__name__ == "__main__"):
    main()
