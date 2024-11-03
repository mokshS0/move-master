"""
Moksh S. GHP Project 2024
ChessEngine.py
Stores all the information about the current state of chess game
Determines valid moves at current state and keeps a move log
"""

class GameState:

    # Initial board setup
    def __init__(self):

        # Board is an 8x8 list, each element in list has 2 characters that represent pieces
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        
        # Setting variables
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []
        self.enpassant_possible = ()
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    # Takes a move as a parameter and executes it
    def makeMove(self, move):

        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # Log the move
        self.white_to_move = not self.white_to_move  # Switch players

        # Update king's location if it moved
        if (move.piece_moved == "wK"):
            self.white_king_location = (move.end_row, move.end_col)
        elif (move.piece_moved == "bK"):
            self.black_king_location = (move.end_row, move.end_col)

        # Pawn promotion
        if (move.is_pawn_promotion):
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # Enpassant
        if (move.is_enpassant_move):
            self.board[move.start_row][move.end_col] = "--"  # Capturing the pawn

        # Update enpassant_possible variable
        if (move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2):  # Only on 2 square pawn advance
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # Castling
        if (move.is_castle_move):

            # King-side castle
            if (move.end_col - move.start_col == 2): 
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # Moves the rook to its new square
                self.board[move.end_row][move.end_col + 1] = '--'  # Erase old rook

            # Queen-side castle
            else:  
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # Moves the rook to its new square
                self.board[move.end_row][move.end_col - 2] = '--'  # Erase old rook

        self.enpassant_possible_log.append(self.enpassant_possible)

        # Update castling rights
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    # Undo the last move
    def undoMove(self):

        # Make sure that there is a move to undo
        if (len(self.move_log) != 0): 
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # Swap players

            # Update the king's position if needed
            if (move.piece_moved == "wK"):
                self.white_king_location = (move.start_row, move.start_col)
            elif (move.piece_moved == "bK"):
                self.black_king_location = (move.start_row, move.start_col)

            # Undo en passant move
            if (move.is_enpassant_move):
                self.board[move.end_row][move.end_col] = "--"  # Leave landing square blank
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # Undo castle rights
            self.castle_rights_log.pop()  # Get rid of the new castle rights from the move we are undoing
            self.current_castling_rights = self.castle_rights_log[-1]  # Set the current castle rights to the last one in the list

            # Undo the castle move
            if (move.is_castle_move):

                # King-side castle
                if (move.end_col - move.start_col == 2):
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'

                # Queen-side castle
                else: 
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    # Update the castle rights given the move
    def updateCastleRights(self, move):

        if (move.piece_captured == "wR"):
            if (move.end_col == 0):  # Left rook
                self.current_castling_rights.wqs = False
            elif (move.end_col == 7):  # Right rook
                self.current_castling_rights.wks = False
        elif (move.piece_captured == "bR"):
            if (move.end_col == 0):  # Left rook
                self.current_castling_rights.bqs = False
            elif (move.end_col == 7):  # Right rook
                self.current_castling_rights.bks = False

        if (move.piece_moved == 'wK'):
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif (move.piece_moved == 'bK'):
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif (move.piece_moved == 'wR'):
            if (move.start_row == 7):
                if (move.start_col == 0):  # Left rook
                    self.current_castling_rights.wqs = False
                elif (move.start_col == 7):  # Right rook
                    self.current_castling_rights.wks = False
        elif (move.piece_moved == 'bR'):
            if (move.start_row == 0):
                if (move.start_col == 0):  # Left rook
                    self.current_castling_rights.bqs = False
                elif (move.start_col == 7):  # Right rook
                    self.current_castling_rights.bks = False

    # Get all the valid moves 
    def getValidMoves(self):

        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # Advanced algorithm
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if (self.white_to_move):
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if (self.in_check):

            # Only 1 check, block the check or move the king
            if (len(self.checks) == 1): 
                moves = self.getAllPossibleMoves()

                # To block the check you must put a piece into one of the squares between the enemy piece and your king
                check = self.checks[0]  # Check information
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # Squares that pieces can move to

                # If knight, must capture the knight or move your king, other pieces can be blocked
                if (piece_checking[1] == "N"):
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  # check[2] and check[3] are the check directions
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col:  # Once you get to piece and check
                            break

                # Get rid of any moves that don't block check or move king
                for i in range(len(moves) - 1, -1, -1):  # Iterate through the list backwards when removing elements
                    if (moves[i].piece_moved[1] != "K"):  # Move doesn't move king so it must block or capture
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # Move doesn't block or capture piece
                            moves.remove(moves[i])

            # Double check - king has to move
            else: 
                self.getKingMoves(king_row, king_col, moves)

        # Not in check - all moves are fine
        else:  
            moves = self.getAllPossibleMoves()
            if (self.white_to_move):
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if (len(moves) == 0):
            if (self.inCheck()):
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    # Determine if the current player is in check
    def inCheck(self):

        if (self.white_to_move):
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    # Determine if the enemy can attack the square
    def squareUnderAttack(self, row, col):

        # Switch to opponent's point of view
        self.white_to_move = not self.white_to_move  
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if (move.end_row == row and move.end_col == col):  # Square is under attack
                return True
        return False

    # Get all moves without considering checks
    def getAllPossibleMoves(self):

        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if ((turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move)):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # Calls appropriate move function based on piece type
        return moves

    # Determine if the current player is in check and all pins and checks
    def checkForPinsAndChecks(self):
        pins = []  # Squares pinned and the direction its pinned from
        checks = []  # Squares where enemy is applying a check
        in_check = False
        if (self.white_to_move):
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]

        # Check outwards from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # Reset possible pins
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if (0 <= end_row <= 7 and 0 <= end_col <= 7):
                    end_piece = self.board[end_row][end_col]
                    if (end_piece[0] == ally_color and end_piece[1] != "K"):

                        # First allied piece could be pinned
                        if (possible_pin == ()):  
                            possible_pin = (end_row, end_col, direction[0], direction[1])

                        # 2nd allied piece - no check or pin from this direction    
                        else:  
                            break

                    elif (end_piece[0] == enemy_color):
                        enemy_type = end_piece[1]

                        # 5 possibilities in this complex conditional:
                        # 1.) orthogonally away from king and piece is a rook
                        # 2.) diagonally away from king and piece is a bishop
                        # 3.) 1 square away diagonally from king and piece is a pawn
                        # 4.) any direction and piece is a queen
                        # 5.) any direction 1 square away and piece is a king
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            
                            # No piece blocking, so check
                            if (possible_pin == ()):  
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break

                            # Piece blocking so pin
                            else:  
                                pins.append(possible_pin)
                                break
                        
                        # Enemy piece not applying checks
                        else:  
                            break

                # Off board
                else:
                    break  

        # Check for knight checks
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if (0 <= end_row <= 7 and 0 <= end_col <= 7):
                end_piece = self.board[end_row][end_col]

                # Enemy knight attacking a king
                if (end_piece[0] == enemy_color and end_piece[1] == "N"):  
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    # Get all the pawn's moves
    def getPawnMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()
        for i in range (len(self.pins) - 1, -1, -1):
            if (self.pins[i][0] == row and self.pins[i][1] == col):
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if (self.white_to_move):
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

         # 1 square pawn advance
        if (self.board[row + move_amount][col] == "--"): 
            if (not piece_pinned or pin_direction == (move_amount, 0)):
                moves.append(Move((row, col), (row + move_amount, col), self.board))

                # 2 square pawn advance
                if (row == start_row and self.board[row + 2 * move_amount][col] == "--"):  
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))

        # Capture to the left
        if (col - 1 >= 0):
            if (not piece_pinned or pin_direction == (move_amount, -1)):
                if (self.board[row + move_amount][col - 1][0] == enemy_color):
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if ((row + move_amount, col - 1) == self.enpassant_possible):
                    attacking_piece = blocking_piece = False
                    if (king_row == row):

                        # King is left of the pawn
                        if (king_col < col):  

                            # inside: between king and the pawn;
                            inside_range = range(king_col + 1, col - 1)

                            # outside: between pawn and border;
                            outside_range = range(col + 1, 8)

                        # King right of the pawn
                        else:  
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if (self.board[row][i] != "--"): 
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if (square[0] == enemy_color and (square[1] == "R" or square[1] == "Q")):
                                attacking_piece = True
                            elif (square != "--"):
                                blocking_piece = True
                    if (not attacking_piece or blocking_piece):
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))

        # Capture to the right
        if (col + 1 <= 7):  
            if (not piece_pinned or pin_direction == (move_amount, +1)):
                if (self.board[row + move_amount][col + 1][0] == enemy_color):
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if ((row + move_amount, col + 1) == self.enpassant_possible):
                    attacking_piece = blocking_piece = False
                    if (king_row == row):

                        # King is left of the pawn
                        if (king_col < col):

                            # inside: between king and the pawn;
                            inside_range = range(king_col + 1, col)

                            # outside: between pawn and border;
                            outside_range = range(col + 2, 8)

                        # King right of the pawn
                        else:  
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if (self.board[row][i] != "--"): 
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if (square[0] == enemy_color and (square[1] == "R" or square[1] == "Q")):
                                attacking_piece = True
                            elif (square != "--"):
                                blocking_piece = True
                    if (not attacking_piece or blocking_piece):
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    # Get all the rook's moves
    def getRookMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if (self.pins[i][0] == row and self.pins[i][1] == col):
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if (self.board[row][col][1] != "Q"):  # Can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # Up, down, left, right
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i

                # Check for possible moves only in boundaries of the board
                if (0 <= end_row <= 7 and 0 <= end_col <= 7): 
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]

                        # Empty space is valid
                        if (end_piece == "--"):  
                            moves.append(Move((row, col), (end_row, end_col), self.board))

                        # Capture enemy piece
                        elif (end_piece[0] == enemy_color): 
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break

                        # Same-sided piece
                        else: 
                            break

                # Off board
                else:  
                    break

    # Get all the knight's moves
    def getKnightMoves(self, row, col, moves):

        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if (self.pins[i][0] == row and self.pins[i][1] == col):
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        # Up/left up/right right/up right/down down/left down/right left/up left/down
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))  

        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if (0 <= end_row <= 7 and 0 <= end_col <= 7):
                if (not piece_pinned):
                    end_piece = self.board[end_row][end_col]
                    if (end_piece[0] != ally_color):  # Either enemy piece or empty square
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    # Get all the bishop's moves
    def getBishopMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if (self.pins[i][0] == row and self.pins[i][1] == col):
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        # Diagonals: up/left up/right down/right down/left
        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i

                # Check if the move is on board
                if (0 <= end_row <= 7 and 0 <= end_col <= 7):  
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]

                         # Empty space is valid
                        if (end_piece == "--"): 
                            moves.append(Move((row, col), (end_row, end_col), self.board))

                        # Capture enemy piece
                        elif (end_piece[0] == enemy_color): 
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break

                        # Same-sided piece
                        else:  
                            break

                # Off board
                else: 
                    break

    # Get all the queen's moves
    def getQueenMoves(self, row, col, moves):

        # Queen moves are a combination of rook and bishop moves
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    # Get all the king's moves
    def getKingMoves(self, row, col, moves):

        #All directions
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)

        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if (0 <= end_row <= 7 and 0 <= end_col <= 7):
                end_piece = self.board[end_row][end_col]

                # Not an ally piece - empty or enemy
                if (end_piece[0] != ally_color):  

                    # Place king on end square and check for checks
                    if (ally_color == "w"):
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if (not in_check):
                        moves.append(Move((row, col), (end_row, end_col), self.board))

                    # Place king back on original location
                    if (ally_color == "w"):
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    # Get all the castle moves
    def getCastleMoves(self, row, col, moves):

        if (self.squareUnderAttack(row, col)):
            return  # Can't castle while in check
        if ((self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks)):
            self.getKingsideCastleMoves(row, col, moves)
        if ((self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs)):
            self.getQueensideCastleMoves(row, col, moves)

    # Get all the king-side castle moves
    def getKingsideCastleMoves(self, row, col, moves):
        if (self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--'):
            if (not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2)):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    # Get all the queen-side castle moves
    def getQueensideCastleMoves(self, row, col, moves):
        if (self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--'):
            if (not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2)):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))

class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

#Finding the chess algebraic notation of the move based off of rows and columns
class Move:

    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # Pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        
        # En passant
        self.is_enpassant_move = is_enpassant_move
        if (self.is_enpassant_move):
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"

        # Castle
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    # Overriding the equals method
    def __eq__(self, other):

        if (isinstance(other, Move)):
            return self.moveID == other.moveID
        return False

    # Function to get the chess notation of the move
    def getChessNotation(self):
        if (self.is_pawn_promotion):
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if (self.is_castle_move):
            if (self.end_col == 1):
                return "0-0-0"
            else:
                return "0-0"
        if (self.is_enpassant_move):
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if (self.piece_captured != "--"):
            if (self.piece_moved[1] == "p"):
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if (self.piece_moved[1] == "p"):
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

    # Function to get the rank and file of the move
    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if (self.is_castle_move):
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if (self.piece_moved[1] == "p"):
            if (self.is_capture):
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if (self.is_capture):
            move_string += "x"
        return move_string + end_square
