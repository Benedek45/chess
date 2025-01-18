import re
import csv
import sys
import tkinter as tk

PIECE_UNICODE = {
    "R": "\u2656", "N": "\u2658", "B": "\u2657", "Q": "\u2655", "K": "\u2654", "P": "\u2659",  # White pieces
    "r": "\u265C", "n": "\u265E", "b": "\u265D", "q": "\u265B", "k": "\u265A", "p": "\u265F",  # Black pieces
    ".": " "  # Empty square
}
turn = 1
global re_turn
re_turn = False
global game_over
game_over = False  # Initialize the game over flag

# - 1
has_king_moved = {"white": False, "black": False}
has_rook_moved = {"A": False, "H": False}

def main():
    global game_over, turn  # Use the global game_over variable
    filename_main, start_new_game = chess_game_continue_or_start()
    if start_new_game:
        save_file = filename_main
        filename = "start.csv"
    else:
        filename = filename_main
        save_file = filename_main

    global re_turn
    board = load_board_from_csv(filename)
    root, canvas = display_chessboard_graphical(board)  # Initialize the GUI

    while not game_over:
        display_chessboard_graphical(board, root, canvas)
        figure, to_where = whose_turn(save_file, board)
        if figure is None or to_where is None:
            continue  # Retry on invalid input

        if not piece_type_rule(figure, to_where, board, figure):
            print("Invalid move. Try again.")
            re_turn = True
        else:
            step_csv(figure, to_where, board, figure, to_where, witch_figur(figure, board))
            save_csv(board, save_file)
            re_turn = False

        # Check for checkmate conditions
        if is_king_in_check(board, "white"):
            if is_checkmate(board, "white"):
                print("Checkmate! Black wins!")
                game_over = True
            else:
                print("White is in check!")

        if is_king_in_check(board, "black"):
            if is_checkmate(board, "black"):
                print("Checkmate! White wins!")
                game_over = True
            else:
                print("Black is in check!")
                turn -= turn

    root.destroy()  # Ensure GUI closes properly

# 0. step
def chess_game_continue_or_start():
    save_file_pattern = r'.+\.csv'
    while True:
        chess_start = input("Would you like to start a continue a game? (type: START or CONTINUE) ")
        if chess_start.upper().strip() == "START" or "CONTINUE":
            break
        else:
            print("Invalid input. Please type 'START' or 'CONTINUE'.")
    while True:
        if chess_start.upper().strip() == "START":
            save_file = input("What should be the new game name? ")
            if not re.fullmatch(save_file_pattern, save_file):
                print("wrong file format, try again")
            elif re.fullmatch(save_file_pattern, save_file):
                print("choosing save file location was successful ")
                start_game = True
                return save_file, start_game

        elif chess_start.upper().strip() == "CONTINUE":
            filename = input("What is your file name? ")
            if not re.fullmatch(save_file_pattern, filename):
                print("wrong file format, try again")
            elif re.fullmatch(save_file_pattern, filename):
                try:
                    with open(filename, "r") as _:
                        print(f"Successfully loaded the game from {filename}.")
                        start_game = False
                        return filename, start_game
                except FileNotFoundError:
                    sys.exit(f"Could not read {filename}")

        else:
            print("Invalid input. Please type 'START' or 'CONTINUE'.")
def load_board_from_csv(filename):
    global turn
    board = {}
    with open(filename, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            board[row["Coordinate"]] = {
                "Piece": row["Piece"],
                "Color": row["Color"],
                "AttackedByWhite": row["AttackedByWhite"] == "True",
                "AttackedByBlack": row["AttackedByBlack"] == "True",
            }
            turn = int(row["Turn"])
    return board
def display_chessboard_graphical(board, root=None, canvas=None):
    if root is None:
        root = tk.Tk()
        root.title("Chessboard")
        canvas = tk.Canvas(root, width=8 * 60 + 40, height=8 * 60 + 40)  # Extra space for labels
        canvas.pack()
    else:
        canvas.delete("all")  # Clear the canvas for updates

    # Define board size and colors
    square_size = 60
    light_color = "#F0D9B5"  # Light square color
    dark_color = "#B58863"   # Dark square color

    # Draw the chessboard squares
    for row in range(8):
        for col in range(8):
            # Determine the square color
            is_light_square = (row + col) % 2 == 0
            square_color = light_color if is_light_square else dark_color

            # Draw the square
            x1 = col * square_size + 40  # Offset for labels
            y1 = row * square_size + 40
            x2 = x1 + square_size
            y2 = y1 + square_size
            canvas.create_rectangle(x1, y1, x2, y2, fill=square_color, outline="")

            # Get the board coordinate
            board_row = str(8 - row)
            board_col = chr(ord('A') + col)
            coord = board_col + board_row

            # Draw the piece if it exists
            piece = board.get(coord, {"Piece": "."})["Piece"]
            if piece != ".":
                piece_unicode = PIECE_UNICODE.get(piece, " ")
                piece_color = "white" if piece.isupper() else "black"
                canvas.create_text(
                    x1 + square_size / 2,
                    y1 + square_size / 2,
                    text=piece_unicode,
                    fill=piece_color,
                    font=("Arial", int(square_size / 2))
                )

    # Draw row labels (1-8)
    for row in range(8):
        y = row * square_size + 40 + square_size / 2
        canvas.create_text(20, y, text=str(8 - row), font=("Arial", 16))

    # Draw column labels (A-H)
    for col in range(8):
        x = col * square_size + 40 + square_size / 2
        canvas.create_text(x, 20, text=chr(ord('A') + col), font=("Arial", 16))

    root.update()  # Refresh the GUI
    return root, canvas

# 1.step
def whose_turn(save_file, board):
    global turn, re_turn, game_over
    if game_over:
        return None, None

    if not re_turn:
        turn += 1
        re_turn = False
    if turn % 2 == 0:
        figure, to_where = get_white_input(save_file, board)
    else:
        figure, to_where = get_black_input(save_file, board)

    # Handle invalid moves
    if figure is None or to_where is None:
        print("Please enter a valid move.")
        re_turn = True  # Retry the same turn
        return None, None

    return figure, to_where





def get_white_input(save_file, board):
    return get_player_input("White", save_file, board)
def get_black_input(save_file, board):
    return get_player_input("Black", save_file, board)
def get_player_input(player_color, save_file, board):
    while True:
        move_input = input(f"Enter {player_color} move (format: A2 to A4): ").strip().upper()  # Convert to uppercase
        pattern = r'[A-H][1-8] TO [A-H][1-8]'  # Pattern for valid move format
        if re.fullmatch(pattern, move_input):
            user_input_save_file = save_file + ".txt"
            with open(user_input_save_file, "a") as file:
                file.write(f"{player_color}: {move_input}\n")
            return move_input.split(" TO ")

        print("Wrong format. Please try again.")



#2.step
def piece_type_rule(figure, to_where, board, start):
    piece = witch_figur(figure, board)
    if not piece:
        print("No piece at the source square.")
        return False
    '''
    if board[start]["Color"].lower() != ("white" if turn % 2 == 0 else "black"):
        print("Invalid move: You can only move your own pieces.")
        return False
    '''
    if piece.lower() == "p":  # Pawn
        return pawn_move_valid(figure, to_where, board)

    if piece.lower() == "n":  # Knight
        return knight_move_valid(figure, to_where, board)

    if piece.lower() == "b":  # Bishop
        return bishop_move_valid(figure, to_where, board)

    if piece.lower() == "q":  # Queen
        return queen_move_valid(figure, to_where, board)

    if piece.lower() == "k":  # King
        if abs(ord(start[0]) - ord(to_where[0])) == 2:  # Castling move
            if hiding_king(start, to_where, board, has_king_moved, has_rook_moved):
                print("Castling successful!")
                return True
        return king_move_valid(figure, to_where, board)

    if piece.lower() == "r":  # Rook
        if start == "A1" or start == "A8":
            has_rook_moved["A"] = True
        elif start == "H1" or start == "H8":
            has_rook_moved["H"] = True
        return rook_move_valid(figure, to_where, board)

    print(f"Move validation for {piece} is not implemented yet.")
    return False
def witch_figur(figure, board):
    if figure in board and board[figure]["Piece"] != ".":
        return board[figure]["Piece"]
    return None  # No piece at the source square
def king_move_valid(start, target, board):
    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    col_diff = abs(ord(start_col) - ord(target_col))
    row_diff = abs(start_row - target_row)

    # Check if the king moves one square in any direction
    if col_diff <= 1 and row_diff <= 1:
        target_piece = board[target]["Piece"]
        color = board[start]["Color"]

        # Ensure the target square is not attacked by the opponent
        if color == "white" and not board[target]["AttackedByBlack"]:
            return target_piece == "." or board[target]["Color"] != color
        elif color == "black" and not board[target]["AttackedByWhite"]:
            return target_piece == "." or board[target]["Color"] != color

    return False
def queen_move_valid(start, target, board):
    # The queen's move is valid if it is either a valid rook move or a valid bishop move
    return rook_move_valid(start, target, board) or bishop_move_valid(start, target, board)
def pawn_move_valid(start, target, board):

    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    piece = board[start]["Piece"]
    color = board[start]["Color"]

    direction = 1 if color == "white" else -1
    start_row_valid = 2 if color == "white" else 7

    # One-step forward move
    if start_col == target_col and target_row == start_row + direction:
        if board[target]["Piece"] == ".":
            return True

    # Two-step forward move from starting position
    if start_col == target_col and start_row == start_row_valid and target_row == start_row + 2 * direction:
        middle_row = start_row + direction
        middle_coord = start_col + str(middle_row)
        if board[target]["Piece"] == "." and board[middle_coord]["Piece"] == ".":
            return True

    # Diagonal capture
    if abs(ord(start_col) - ord(target_col)) == 1 and target_row == start_row + direction:
        if board[target]["Piece"] != "." and board[target]["Color"] != color:
            return True

    return False  # Invalid pawn move
def rook_move_valid(start, target, board):
    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    if start_col != target_col and start_row != target_row:
        return False  # A bástya csak egyenes vonalban mozoghat

    piece = board[start]["Piece"]
    color = board[start]["Color"]

    # Ellenőrizzük az út közben lévő mezőket
    if start_col == target_col:  # Függőleges mozgás
        step = 1 if target_row > start_row else -1
        for row in range(start_row + step, target_row, step):
            if board[f"{start_col}{row}"]["Piece"] != ".":
                return False

    elif start_row == target_row:  # Vízszintes mozgás
        step = 1 if ord(target_col) > ord(start_col) else -1
        for col in range(ord(start_col) + step, ord(target_col), step):
            if board[f"{chr(col)}{start_row}"]["Piece"] != ".":
                return False

    # A célmező ellenőrzése
    target_piece = board[target]["Piece"]
    if target_piece == "." or board[target]["Color"] != color:
        return True  # Üres mező vagy ellenséges bábu

    return False
def knight_move_valid(start, target, board):
    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    col_diff = abs(ord(start_col) - ord(target_col))
    row_diff = abs(start_row - target_row)

    # Check if the move matches an "L" shape
    if (col_diff == 2 and row_diff == 1) or (col_diff == 1 and row_diff == 2):
        target_piece = board[target]["Piece"]
        if target_piece == "." or board[target]["Color"] != board[start]["Color"]:
            return True

    return False
def bishop_move_valid(start, target, board):
    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    col_diff = abs(ord(start_col) - ord(target_col))
    row_diff = abs(start_row - target_row)

    # Check if the move is diagonal
    if col_diff == row_diff:
        col_step = 1 if target_col > start_col else -1
        row_step = 1 if target_row > start_row else -1

        col = ord(start_col) + col_step
        row = start_row + row_step
        while col != ord(target_col) and row != target_row:
            if board[f"{chr(col)}{row}"]["Piece"] != ".":
                return False  # Blocked
            col += col_step
            row += row_step

        # Check if the target square is empty or has an opponent's piece
        if board[target]["Piece"] == "." or board[target]["Color"] != board[start]["Color"]:
            return True

    return False
def update_attacks(board):
    # Reset all attack markers
    for coord in board:
        board[coord]["AttackedByWhite"] = False
        board[coord]["AttackedByBlack"] = False

    for coord, details in board.items():
        piece = details["Piece"]
        color = details["Color"]

        # Pawn attacks
        if piece.lower() == "p":
            row, col = int(coord[1]), coord[0]
            direction = 1 if color == "white" else -1
            attacked_rows = [row + direction]
            attacked_cols = [chr(ord(col) - 1), chr(ord(col) + 1)]  # Diagonal directions

            for r in attacked_rows:
                for c in attacked_cols:
                    target = f"{c}{r}"
                    if target in board:  # If the square exists
                        if color == "white":
                            board[target]["AttackedByWhite"] = True
                        else:
                            board[target]["AttackedByBlack"] = True

        # Rook attacks
        if piece.lower() == "r":
            directions = [  # Four possible directions for the rook
                (1, 0),  # Up
                (-1, 0),  # Down
                (0, 1),  # Right
                (0, -1)  # Left
            ]
            row, col = int(coord[1]), ord(coord[0])

            for dr, dc in directions:
                r, c = row, col
                while True:
                    r += dr
                    c += dc
                    target = f"{chr(c)}{r}"
                    if target not in board:  # Out of bounds
                        break
                    if color == "white":
                        board[target]["AttackedByWhite"] = True
                    else:
                        board[target]["AttackedByBlack"] = True

                    if board[target]["Piece"] != ".":  # Stop if there's a piece
                        break

        # Knight attacks
        if piece.lower() == "n":
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            row, col = int(coord[1]), ord(coord[0])

            for dr, dc in knight_moves:
                r, c = row + dr, col + dc
                target = f"{chr(c)}{r}"
                if target in board:  # If the square exists
                    if color == "white":
                        board[target]["AttackedByWhite"] = True
                    else:
                        board[target]["AttackedByBlack"] = True
        #bishop
        if piece.lower() == "b":
            directions = [  # Four possible diagonal directions
                (1, 1),  # Up-right
                (1, -1),  # Up-left
                (-1, 1),  # Down-right
                (-1, -1)  # Down-left
            ]
            row, col = int(coord[1]), ord(coord[0])

            for dr, dc in directions:
                r, c = row, col
                while True:
                    r += dr
                    c += dc
                    target = f"{chr(c)}{r}"
                    if target not in board:  # Out of bounds
                        break
                    if color == "white":
                        board[target]["AttackedByWhite"] = True
                    else:
                        board[target]["AttackedByBlack"] = True

                    if board[target]["Piece"] != ".":  # Stop if there's a piece
                        break
            #queen
        if piece.lower() == "q":
            directions = [  # Eight possible directions for the queen
                (1, 0), (-1, 0), (0, 1), (0, -1),  # Rook-like directions
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Bishop-like directions
            ]
            row, col = int(coord[1]), ord(coord[0])

            for dr, dc in directions:
                r, c = row, col
                while True:
                    r += dr
                    c += dc
                    target = f"{chr(c)}{r}"
                    if target not in board:  # Out of bounds
                        break
                    if color == "white":
                        board[target]["AttackedByWhite"] = True
                    else:
                        board[target]["AttackedByBlack"] = True

                    if board[target]["Piece"] != ".":  # Stop if there's a piece
                        break

        # King attacks
        if piece.lower() == "k":
            king_moves = [
                (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal directions
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal directions
            ]
            row, col = int(coord[1]), ord(coord[0])

            for dr, dc in king_moves:
                r, c = row + dr, col + dc
                target = f"{chr(c)}{r}"
                if target in board:  # If the square exists
                    if color == "white":
                        board[target]["AttackedByWhite"] = True
                    else:
                        board[target]["AttackedByBlack"] = True

def imposter_pawn(figure, board, target_row):
    piece = witch_figur(figure, board)
    if piece == "p":
        if target_row in [1, 8]:  # Pawn promotion happens only on the 1st or 8th rank
            while True:
                choose = input("What would you like to turn the pawn into (queen, rook, bishop, knight)? ").strip().lower()
                if choose == "king":
                    print("You can't have two kings. Choose again.")
                elif choose == "queen":
                    board[figure]["Piece"] = "q" if board[figure]["Color"] == "white" else "Q"
                    break
                elif choose == "rook":
                    board[figure]["Piece"] = "r" if board[figure]["Color"] == "white" else "R"
                    break
                elif choose == "bishop":
                    board[figure]["Piece"] = "b" if board[figure]["Color"] == "white" else "B"
                    break
                elif choose == "knight":
                    board[figure]["Piece"] = "n" if board[figure]["Color"] == "white" else "N"
                    break
                else:
                    print("Invalid choice. Please select one of: queen, rook, bishop, knight.")
def hiding_king(start, target, board, has_king_moved, has_rook_moved):
    start_col, start_row = start[0], int(start[1])
    target_col, target_row = target[0], int(target[1])

    # Sáncolás csak ugyanazon a soron történhet
    if start_row != target_row:
        return False

    # Király két mezőt lép jobbra (kis sáncolás)
    if target_col == chr(ord(start_col) + 2):
        rook_start = f"H{start_row}"
        rook_end = f"F{start_row}"
        if (
            not has_king_moved["white"] and  # Király nem mozdult
            not has_rook_moved["H"] and  # Bástya nem mozdult
            board[f"G{start_row}"]["Piece"] == "." and  # Út üres
            board[f"F{start_row}"]["Piece"] == "."
        ):
            # Végrehajtjuk a sáncolást
            board[f"G{start_row}"] = board[start]  # Király új helye
            board[start] = {"Piece": ".", "Color": "None"}  # Király régi helye
            board[rook_end] = board[rook_start]  # Bástya új helye
            board[rook_start] = {"Piece": ".", "Color": "None"}  # Bástya régi helye
            return True

    # Király két mezőt lép balra (nagy sáncolás)
    if target_col == chr(ord(start_col) - 2):
        rook_start = f"A{start_row}"
        rook_end = f"D{start_row}"
        if (
            not has_king_moved["white"] and  # Király nem mozdult
            not has_rook_moved["A"] and  # Bástya nem mozdult
            board[f"C{start_row}"]["Piece"] == "." and  # Út üres
            board[f"D{start_row}"]["Piece"] == "."
        ):
            # Végrehajtjuk a sáncolást
            board[f"C{start_row}"] = board[start]  # Király új helye
            board[start] = {"Piece": ".", "Color": "None"}  # Király régi helye
            board[rook_end] = board[rook_start]  # Bástya új helye
            board[rook_start] = {"Piece": ".", "Color": "None"}  # Bástya régi helye
            return True

    return False  # Érvénytelen sáncolás

def is_king_in_check(board, color):
    """
    Check if the king of the given color is in check.
    """
    for coord, details in board.items():
        if details["Piece"].lower() == "k" and details["Color"] == color:
            if (color == "white" and details["AttackedByBlack"]) or (color == "black" and details["AttackedByWhite"]):
                return True
    return False
def is_checkmate(board, color):
    """
    Check if the given color is in checkmate.
    """
    if not is_king_in_check(board, color):
        return False  # Not in check, so it can't be checkmate

    # Try all possible moves for the current player
    for coord, details in board.items():
        if details["Color"] == color:
            for target in get_possible_moves(coord, board):
                simulated_board = simulate_move(board, coord, target)
                if not is_king_in_check(simulated_board, color):
                    return False  # Found a move that escapes check

    return True  # No moves escape check, so it's checkmate
def simulate_move(board, start, target):
    """
    Simulate a move on the board and return the new board state.
    """
    simulated_board = {k: v.copy() for k, v in board.items()}  # Deep copy of the board
    simulated_board[target] = simulated_board[start]
    simulated_board[start] = {"Piece": ".", "Color": "None", "AttackedByWhite": False, "AttackedByBlack": False}
    update_attacks(simulated_board)  # Recalculate attacked squares
    return simulated_board
def get_possible_moves(coord, board):
    """
    Get all possible moves for a piece at the given coordinate.
    """
    possible_moves = []
    start_piece = board[coord]["Piece"]

    # If there's no piece at the given coordinate, return an empty list
    if start_piece == ".":
        return possible_moves

    # Iterate over all squares on the board to check for valid moves
    for row in range(1, 9):  # Board rows 1-8
        for col in "ABCDEFGH":  # Board columns A-H
            target_coord = f"{col}{row}"
            if piece_type_rule(coord, target_coord, board, coord):
                possible_moves.append(target_coord)

    return possible_moves
def step_csv(figure, to_where, board, start, target, piece):
    """
    Update the board after a valid move and handle special cases like promotion and castling.
    """
    global re_turn, turn
    if board[figure]["Color"].lower() != ("white" if turn % 2 == 0 else "black"):
        print("Invalid move: You can only move your own pieces.")
        turn -= 1
        return

    # Save the current state of the board for potential reversion
    original_state = {k: v.copy() for k, v in board.items()}

    # Execute the move
    board[to_where] = board[figure]
    board[figure] = {"Piece": ".", "Color": "None"}  # Clear the source square

    # Update attack data
    update_attacks(board)

    # Check if the move leaves the king in check
    king_color = board[to_where]["Color"]
    if is_king_in_check(board, king_color):
        print(f"Invalid move: {king_color} king is still in check!")
        board.clear()
        board.update(original_state)  # Revert to original state
        re_turn = True
        return

    # Handle pawn promotion
    target_row = int(to_where[1])
    if piece.lower() == "p" and (target_row == 1 or target_row == 8):
        imposter_pawn(to_where, board, target_row)

    # If everything is valid, finalize the move
    re_turn = False


#4.step
def save_csv(board, save_file):
    global turn
    with open(save_file, "w", newline="") as file:
        fieldnames = ["Coordinate", "Piece", "Color", "AttackedByWhite", "AttackedByBlack", "Turn"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for coord, details in board.items():
            writer.writerow({
                "Coordinate": coord,
                "Piece": details["Piece"],
                "Color": details["Color"],
                "AttackedByWhite": details.get("AttackedByWhite", False),
                "AttackedByBlack": details.get("AttackedByBlack", False),
                "Turn": turn  # Save the current turn
            })


if __name__ == "__main__":
    main()










#if anybode ask it it's more than 700 line long