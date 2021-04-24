import sys
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QLineEdit, QPushButton, QWidget
import sqlite3
import random


WHITE = 1
BLACK = 2
FIRST_PLAYER = ''
SECOND_PLAYER = ''
 
 
def opponent(color):#  Вернуть обратный данному цвет
    if color == WHITE:
        return BLACK
    else:
        return WHITE
  

def correct_coords(row, col):#  Проверка на принадлежность координат доске
    return 0 <= row < 8 and 0 <= col < 8


def is_not_under_attack(board, row1, col1, color):#  Проверить, под атакой ли клетка
    if color == WHITE:
        for i in BLACK_FIGURES:
            piece = board.get_piece(i[0], i[1])
            if piece.char() == 'P':
                if piece.can_attack(board, i[0], i[1], row1, col1, king_check=True):
                    return False
            else:
                if piece.can_attack(board, i[0], i[1], row1, col1):
                    return False
        return True
    if color == BLACK:
        for i in WHITE_FIGURES:
            piece = board.get_piece(i[0], i[1])
            if piece.char() == 'P':
                if piece.can_attack(board, i[0], i[1], row1, col1, king_check=True):
                    return False
            else:
                if piece.can_attack(board, i[0], i[1], row1, col1):
                    return False
        return True
 
 
class Board:#  Класс шаматной доски
    def __init__(self):
        self.color = WHITE#  Устанавливаем белый цвет игрока
        self.field = []
        self.alert = False#  Король не под шахом
        for row in range(8):
            self.field.append([None] * 8)#  Создаем пустой список для будущих шаматных фигур
            
    def current_player_color(self):#  Вернуть цвет игрока
        return self.color

    def king_alert(self, coords_1=[]):#  Проверка на шах короля
        if self.color == WHITE:
            if coords_1 == []:
                for i in WHITE_FIGURES:
                    if self.get_piece(i[0], i[1]) is not None:
                        if self.get_piece(i[0], i[1]).char() == 'K':
                            coords_1 = [i[0], i[1]]
            if not is_not_under_attack(board, coords_1[0], coords_1[1], self.color):
                self.alert = True
                self.get_piece(coords_1[0], coords_1[1]).castling = False
                return True
        if self.color == BLACK:
            if coords_1 == []:
                for i in BLACK_FIGURES:
                    if self.get_piece(i[0], i[1]) is not None:
                        if self.get_piece(i[0], i[1]).char() == 'K':
                            coords_1 = [i[0], i[1]]
            if not is_not_under_attack(board, coords_1[0], coords_1[1], self.color):
                self.alert = True
                self.get_piece(coords_1[0], coords_1[1]).castling = False
                return True
        return False
 
    def cell(self, row, col):#  Вернуть информацию о фигуре
        piece = self.field[row][col]
        if piece is None:
            return '  '
        color = piece.get_color()
        c = 'w' if color == WHITE else 'b'
        return c + piece.char()
 
    def get_piece(self, row, col):#  Получить фигуру по координатам
        if correct_coords(row, col):
            return self.field[row][col]
        else:
            return None
 
    def move_piece(self, row, col, row1, col1):#  Передвинуть фигуру
        if not correct_coords(row, col) or not correct_coords(row1, col1):
            return False
        if row == row1 and col == col1:
            return False 
        piece = self.field[row][col]
        if piece is None:
            return False
        if piece.color != self.color:
            return False
        if self.field[row1][col1] is None:
            if not piece.can_move(self, row, col, row1, col1):
                return False
        elif self.field[row1][col1].color == opponent(piece.color):
            if not piece.can_attack(self, row, col, row1, col1):
                return False
        else:
            return False
        if piece.char() in ('K', 'R'):
            piece.can_castle = False
        if self.alert:
            piece_2 = self.field[row1][col1]
            self.field[row][col] = None  
            self.field[row1][col1] = piece
            if piece.char() == 'K':
                if self.king_alert([row1, col1]):
                    self.field[row][col] = piece
                    self.field[row1][col1] = piece_2
                    return False
            else:
                if self.king_alert():
                    self.field[row][col] = piece
                    self.field[row1][col1] = piece_2
                    return False
        self.field[row][col] = None  
        self.field[row1][col1] = piece
        self.color = opponent(self.color)
        return True

    def castling_0(self, row, col, row1, col1):#  Длинная рокировка
        king = board.get_piece(row, col)
        rook = board.get_piece(row1, col1)
        if king is None or rook is None:
            return False
        if king.char() != 'K' or rook.char() != 'R':
            return False
        if not king.can_castle:
            return False
        if not rook.can_castle:
            return False
        if king.color != rook.color:
            return False
        for i in (1, 2, 3):
            if self.field[row][col - i] is not None:
                return False
        if not is_not_under_attack(board, row1, col1, rook.color):
            return False
        if not is_not_under_attack(board, row, col - 1, king.color):
            return False
        if not is_not_under_attack(board, row, col - 2, king.color):
            return False
        if not is_not_under_attack(board, row, col - 3, king.color):
            return False
        piece = self.field[row][col]
        self.field[row][col] = None  
        self.field[row][col - 2] = piece
        piece = self.field[row1][col1]
        self.field[row1][col1] = None  
        self.field[row1][col1 + 3] = piece
        self.color = opponent(self.color)
        return True

    def castling_7(self, row, col, row1, col1):#  Короткая рокировка
        king = self.field[row][col]
        rook = self.field[row1][col1]
        if king is None or rook is None:
            return False
        if king.char() != 'K' or rook.char() != 'R':
            return False
        if not king.can_castle:
            return False
        if not rook.can_castle:
            return False
        for i in (1, 2):
            if self.field[row][col + i] is not None:
                return False
        if not is_not_under_attack(board, row1, col1, rook.color):
            return False
        if not is_not_under_attack(board, row, col + 1, king.color):
            return False
        if not is_not_under_attack(board, row, col + 2, king.color):
            return False
        piece = self.field[row][col]
        self.field[row][col] = None  
        self.field[row][col + 2] = piece
        piece = self.field[row1][col1]
        self.field[row1][col1] = None  
        self.field[row1][col1 - 2] = piece
        self.color = opponent(self.color)
        return True

    def promote_pawn(self, char, pawn_coords):#  Превращение пешки
        color = self.field[pawn_coords[0]][pawn_coords[1]].get_color()
        if char == 'Q':
            self.field[pawn_coords[0]][pawn_coords[1]] = Queen(color)
        elif char == 'R':
            self.field[pawn_coords[0]][pawn_coords[1]] = Rook(color)
        elif char == 'B':
            self.field[pawn_coords[0]][pawn_coords[1]] = Bishop(color)
        elif char == 'N':
            self.field[pawn_coords[0]][pawn_coords[1]] = Knight(color)
        return True
 
 
class Rook:#  Класс ладьи
    def __init__(self, color):
        self.color = color
        self.castling = True#  Поначалу может рокироваться

    def can_castle(self):
        return self.castling
        
    def get_color(self):
        return self.color
    
    def char(self):
        return 'R'
    
    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if row == row1 or col == col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                if not (board.get_piece(i, col) is None):
                    return False
            step = 1 if (col1 >= col) else -1
            for i in range(col + step, col1, step):
                if not (board.get_piece(row, i) is None):
                    return False
            return True
        return False
 
    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)
 
 
class Pawn:#  Класс пешки
    def __init__(self, color):
        self.color = color
 
    def get_color(self):
        return self.color
 
    def char(self):
        return 'P'
 
    def can_move(self, board, row, col, row1, col1, king_check=False):
        if not correct_coords(row1, col1):
            return False
        if self.color == WHITE:
            start_row = 1
        else:
            start_row = 6
        if (row1 - row == 2 and self.color == WHITE) or (row1 - row == -2 and self.color == BLACK):
            if row != start_row:
                return False
            if col != col1:
                return False
            if board.get_piece(row1, col1) is not None:
                return False
            return True
        if (row1 - row == 1 and self.color == WHITE) or (row1 - row == -1 and self.color == BLACK):
            if col1 != col:
                if abs(col1 - col) != 1:
                    return False
                if board.get_piece(row1, col1) is None:
                    if king_check:
                        return True
                    else:
                        return False
                if board.get_piece(row1, col1).get_color() == self.color:
                    return False
                else:
                    return True
            else:
                if board.get_piece(row1, col1) is not None:
                    return False 
                return True
        return False
        
    def can_attack(self, board, row, col, row1, col1, king_check=False):
        if not correct_coords(row1, col1):
            return False
        if self.color == WHITE:
            start_row = 1
        else:
            start_row = 6
        if (row1 - row == 2 and self.color == WHITE) or (row1 - row == -2 and self.color == BLACK):
            return False
        if (row1 - row == 1 and self.color == WHITE) or (row1 - row == -1 and self.color == BLACK):
            if col1 != col:
                if abs(col1 - col) != 1:
                    return False
                if board.get_piece(row1, col1) is None:
                    if king_check:
                        return True
                    else:
                        return False
                if board.get_piece(row1, col1).get_color() == self.color:
                    return False
                else:
                    return True
            else:
                return False 
        return False
 
class Knight:#  Класс коня
    def __init__(self, color):
        self.color = color
 
    def get_color(self):
        return self.color
 
    def char(self):
        return 'N'  
 
    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if str(abs(row1 - row)) + str(abs(col1 - col)) in ('12', '21'):
            return True
        return False
 
    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)

 
class Queen:#  Класс ферзя
    def __init__(self, color):
        self.color = color
 
    def get_color(self):
        return self.color
 
    def char(self):
        return 'Q'
 
    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if row == row1 or col == col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                if not (board.get_piece(i, col) is None):
                    return False
            step = 1 if (col1 >= col) else -1
            for i in range(col + step, col1, step):
                if not (board.get_piece(row, i) is None):
                    return False
            return True
        if row - col == row1 - col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                c = col - row + i
                if not (board.get_piece(i, c) is None):
                    return False
            return True
        if row + col == row1 + col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                c = row + col - i
                if not (board.get_piece(i, c) is None):
                    return False
            return True
        return False
 
    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)
 
 
class Bishop:#  Класс слона
    def __init__(self, color):
        self.color = color
 
    def get_color(self):
        return self.color
 
    def char(self):
        return 'B'
 
    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if row - col == row1 - col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                c = col - row + i
                if not (board.get_piece(i, c) is None):
                    return False
            return True
        if row + col == row1 + col1:
            step = 1 if (row1 >= row) else -1
            for i in range(row + step, row1, step):
                c = row + col - i
                if not (board.get_piece(i, c) is None):
                    return False
            return True
        return False
 
    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)
    
    
class King:#  Класс короля
    def __init__(self, color):
        self.color = color
        self.castling = True#  Поначалу может рокироваться

    def can_castle(self):
        return self.castling
 
    def get_color(self):
        return self.color
 
    def char(self):
        return 'K'

    def can_move(self, board, row, col, row1, col1):
        if not correct_coords(row1, col1):
            return False
        piece1 = board.get_piece(row1, col1)
        if not (piece1 is None) and piece1.get_color() == self.color:
            return False
        if str(abs(row1 - row)) + str(abs(col1 - col)) not in ('01', '10', '11'):
            return False
        if not is_not_under_attack(board, row1, col1, self.color):
            return False
        return True
 
    def can_attack(self, board, row, col, row1, col1):
        return self.can_move(board, row, col, row1, col1)


class Starter(QMainWindow):#  Оконо с регистрацией и входом
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(60, 60, 1800, 1000)
        self.setWindowTitle('Вход')
        self.input_name = QLineEdit(self)
        self.input_password = QLineEdit(self)
        self.input_name.move(800, 300)
        self.input_password.move(800, 325)
        self.input_name.resize(self.input_name.sizeHint())
        self.input_password.resize(self.input_password.sizeHint())
        self.btn_1 = QPushButton('ВОЙТИ', self)
        self.btn_1.resize(self.btn_1.sizeHint())
        self.btn_1.move(815, 375)
        self.lab_1 = QLabel('Введите логин и пароль, если вы зарегистрированы', self)
        self.lab_1.resize(self.lab_1.sizeHint())
        self.lab_1.move(750, 275)
        self.btn_2 = QPushButton('Если вы не зарегистрированы, нажмите сюда', self)
        self.btn_2.resize(self.btn_2.sizeHint())
        self.btn_2.move(750, 410)
        self.btn_1.clicked.connect(self.run_1)
        self.btn_2.clicked.connect(self.run_2)
        self.error = QLabel('', self)
        self.error.move(810, 440)

    def run_1(self):
        global FIRST_PLAYER
        global SECOND_PLAYER
        name = self.input_name.text()
        password = self.input_password.text()
        con = sqlite3.connect("players_list.db")
        cur = con.cursor()
        if self.lab_1.text() == 'Введите логин и пароль, если вы зарегистрированы':#  Вход игрока в систему
            result = cur.execute("""SELECT password FROM enter WHERE nickname = ?""", (name,)).fetchall()
            if len(result) == 0:
                self.error.setText('Неправильные данные')
            elif password != result[0][0]:
                self.error.setText('Неправильные данные')
            elif len(FIRST_PLAYER) == 0:
                FIRST_PLAYER = name
                self.error.setText('')
                self.input_name.setText('')
                self.input_password.setText('')
                self.error.setText('Первый игрок вошел')
            else:
                if name == FIRST_PLAYER:
                    self.error.setText('Неправильные данные')
                else:
                    SECOND_PLAYER = name
                    self.second_app()
        else:#  Регистрация игрока
            if name == '' or str(password) == '':
                self.error.setText('Неправильные данные')
            elif len(name) > 13:
                self.error.setText('Неправильные данные')
            else:
                result = cur.execute("""SELECT nickname FROM enter""").fetchall()
                if any(name == i for i in list(i[0] for i in result)):
                    self.error.setText('Неправильные данные')
                else:
                    cur.execute("""INSERT INTO enter VALUES(?, ?)""", (name, password))
                    cur.execute("""INSERT INTO player_statistics VALUES(?, ?, ?, ?)""", (name, 0, 0, 0))
                    con.commit()
                    self.lab_1.setText('Введите логин и пароль, если вы зарегистрированы')
                    self.btn_2.show()
                    self.btn_1.setText('ВОЙТИ')
                    self.btn_1.resize(self.btn_1.sizeHint())
                    self.input_name.setText('')
                    self.input_password.setText('')
        self.error.resize(self.error.sizeHint())

    def run_2(self):#  Перенаправить на регистрацию
        self.lab_1.setText('Введите логин и пароль (не более 13 символов), чтобы зарегистрироваться')
        self.lab_1.resize(self.lab_1.sizeHint())
        self.btn_1.setText('ЗАРЕГИСТРИРОВАТЬСЯ')
        self.btn_1.resize(self.btn_1.sizeHint())
        self.error.setText('')
        self.btn_2.hide()

    def second_app(self):#  Запуск второго окна
        self.ex_1 = Counter()
        self.ex_1.show()
        self.hide()


class Counter(QWidget):#  Окно, говорящее, кто будет ходит первым, показывающее статистику соперников
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global FIRST_PLAYER
        global SECOND_PLAYER
        self.setGeometry(600, 300, 350, 400)
        self.setWindowTitle('Начало игры')
        self.win_label = QLabel('Победы:', self)
        self.lose_label = QLabel('Поражения:', self)
        self.win_lose_label = QLabel('Статистика:', self)
        self.win_label.move(10, 70)
        self.lose_label.move(10, 80)
        self.win_lose_label.move(10, 90)
        self.white_label = QLabel('Белый:', self)
        self.black_label = QLabel('Черный:', self)
        self.white_label.move(80, 50)
        self.black_label.move(220, 50)
        self.names = [FIRST_PLAYER, SECOND_PLAYER]
        random.shuffle(self.names)
        self.name_1 = QLabel(self.names[0], self)
        self.name_1.resize(self.name_1.sizeHint())
        self.name_1.move(80, 60)
        self.name_2 = QLabel(self.names[1], self)
        self.name_2.resize(self.name_2.sizeHint())
        self.name_2.move(220, 60)
        con = sqlite3.connect("players_list.db")
        cur = con.cursor()
        self.win_1 = QLabel(str(cur.execute("""SELECT win FROM player_statistics WHERE player_nickname = ?""", (self.names[0],)).fetchone()[0]), self)
        self.win_1.move(80, 70)
        self.win_2 = QLabel(str(cur.execute("""SELECT win FROM player_statistics WHERE player_nickname = ?""", (self.names[1],)).fetchone()[0]), self)
        self.win_2.move(220, 70)
        self.win_1 = QLabel(str(cur.execute("""SELECT lose FROM player_statistics WHERE player_nickname = ?""", (self.names[0],)).fetchone()[0]), self)
        self.win_1.move(80, 80)
        self.win_2 = QLabel(str(cur.execute("""SELECT lose FROM player_statistics WHERE player_nickname = ?""", (self.names[1],)).fetchone()[0]), self)
        self.win_2.move(220, 80)
        self.win_1 = QLabel(str(cur.execute("""SELECT win_lose FROM player_statistics WHERE player_nickname = ?""", (self.names[0],)).fetchone()[0]), self)
        self.win_1.move(80, 90)
        self.win_2 = QLabel(str(cur.execute("""SELECT win_lose FROM player_statistics WHERE player_nickname = ?""", (self.names[1],)).fetchone()[0]), self)
        self.win_2.move(220, 90)
        self.btn_3 = QPushButton('СТАРТ', self)
        self.btn_3.clicked.connect(self.open_game)
        self.btn_3.move(110, 110)
        FIRST_PLAYER = [self.names[0], WHITE]
        SECOND_PLAYER = [self.names[1], BLACK]

    def open_game(self):#  Начать игру
        self.ex_2 = Chess_game()
        self.ex_2.show()
        self.hide()


class Chess_game(QWidget):#  Окно с шахматами
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(60, 60, 1800, 1000)
        self.setWindowTitle('Шахматы')
        self.pixmap = QPixmap('b1.png')
        self.image = QLabel(self)
        self.image.move(0, 60)
        self.image.setPixmap(self.pixmap)#  Отрисовываем картинку доски
        self.label_00 = QLabel(self)
        self.label_00.move(350, 645)
        self.label_01 = QLabel(self)
        self.label_01.move(410, 645)
        self.label_02 = QLabel(self)
        self.label_02.move(470, 645)
        self.label_03 = QLabel(self)
        self.label_03.move(530, 645)
        self.label_04 = QLabel(self)
        self.label_04.move(590, 645)
        self.label_05 = QLabel(self)
        self.label_05.move(650, 645)
        self.label_06 = QLabel(self)
        self.label_06.move(710, 645)
        self.label_07 = QLabel(self)
        self.label_07.move(770, 645)
        self.label_10 = QLabel(self)
        self.label_10.move(350, 585)
        self.label_11 = QLabel(self)
        self.label_11.move(410, 585)
        self.label_12 = QLabel(self)
        self.label_12.move(470, 585)
        self.label_13 = QLabel(self)
        self.label_13.move(530, 585)
        self.label_14 = QLabel(self)
        self.label_14.move(590, 585)
        self.label_15 = QLabel(self)
        self.label_15.move(650, 585)
        self.label_16 = QLabel(self)
        self.label_16.move(710, 585)
        self.label_17 = QLabel(self)
        self.label_17.move(770, 585)
        self.label_20 = QLabel(self)
        self.label_20.move(350, 525)
        self.label_21 = QLabel(self)
        self.label_21.move(410, 525)
        self.label_22 = QLabel(self)
        self.label_22.move(470, 525)
        self.label_23 = QLabel(self)
        self.label_23.move(530, 525)
        self.label_24 = QLabel(self)
        self.label_24.move(590, 525)
        self.label_25 = QLabel(self)
        self.label_25.move(650, 525)
        self.label_26 = QLabel(self)
        self.label_26.move(710, 525)
        self.label_27 = QLabel(self)
        self.label_27.move(770, 525)
        self.label_30 = QLabel(self)
        self.label_30.move(350, 465)
        self.label_31 = QLabel(self)
        self.label_31.move(410, 465)
        self.label_32 = QLabel(self)
        self.label_32.move(470, 465)
        self.label_33 = QLabel(self)
        self.label_33.move(530, 465)
        self.label_34 = QLabel(self)
        self.label_34.move(590, 465)
        self.label_35 = QLabel(self)
        self.label_35.move(650, 465)
        self.label_36 = QLabel(self)
        self.label_36.move(710, 465)
        self.label_37 = QLabel(self)
        self.label_37.move(770, 465)
        self.label_40 = QLabel(self)
        self.label_40.move(350, 405)
        self.label_41 = QLabel(self)
        self.label_41.move(410, 405)
        self.label_42 = QLabel(self)
        self.label_42.move(470, 405)
        self.label_43 = QLabel(self)
        self.label_43.move(530, 405)
        self.label_44 = QLabel(self)
        self.label_44.move(590, 405)
        self.label_45 = QLabel(self)
        self.label_45.move(650, 405)
        self.label_46 = QLabel(self)
        self.label_46.move(710, 405)
        self.label_47 = QLabel(self)
        self.label_47.move(770, 405)
        self.label_50 = QLabel(self)
        self.label_50.move(350, 350)
        self.label_51 = QLabel(self)
        self.label_51.move(410, 350)
        self.label_52 = QLabel(self)
        self.label_52.move(470, 350)
        self.label_53 = QLabel(self)
        self.label_53.move(530, 350)
        self.label_54 = QLabel(self)
        self.label_54.move(590, 350)
        self.label_55 = QLabel(self)
        self.label_55.move(650, 350)
        self.label_56 = QLabel(self)
        self.label_56.move(710, 350)
        self.label_57 = QLabel(self)
        self.label_57.move(770, 350)
        self.label_60 = QLabel(self)
        self.label_60.move(350, 295)
        self.label_61 = QLabel(self)
        self.label_61.move(410, 295)
        self.label_62 = QLabel(self)
        self.label_62.move(470, 295)
        self.label_63 = QLabel(self)
        self.label_63.move(530, 295)
        self.label_64 = QLabel(self)
        self.label_64.move(590, 295)
        self.label_65 = QLabel(self)
        self.label_65.move(650, 295)
        self.label_66 = QLabel(self)
        self.label_66.move(710, 295)
        self.label_67 = QLabel(self)
        self.label_67.move(770, 295)
        self.label_70 = QLabel(self)
        self.label_70.move(350, 240)
        self.label_71 = QLabel(self)
        self.label_71.move(410, 240)
        self.label_72 = QLabel(self)
        self.label_72.move(470, 240)
        self.label_73 = QLabel(self)
        self.label_73.move(530, 240)
        self.label_74 = QLabel(self)
        self.label_74.move(590, 240)
        self.label_75 = QLabel(self)
        self.label_75.move(650, 240)
        self.label_76 = QLabel(self)
        self.label_76.move(710, 240)
        self.label_77 = QLabel(self)
        self.label_77.move(770, 240)#  Создаем QLabel для каждой клетки доски
        self.vis = [[self.label_00, self.label_01, self.label_02, self.label_03, self.label_04, self.label_05, self.label_06, self.label_07], 
                    [self.label_10, self.label_11, self.label_12, self.label_13, self.label_14, self.label_15, self.label_16, self.label_17], 
                    [self.label_20, self.label_21, self.label_22, self.label_23, self.label_24, self.label_25, self.label_26, self.label_27], 
                    [self.label_30, self.label_31, self.label_32, self.label_33, self.label_34, self.label_35, self.label_36, self.label_37],
                    [self.label_40, self.label_41, self.label_42, self.label_43, self.label_44, self.label_45, self.label_46, self.label_47], 
                    [self.label_50, self.label_51, self.label_52, self.label_53, self.label_54, self.label_55, self.label_56, self.label_57], 
                    [self.label_60, self.label_61, self.label_62, self.label_63, self.label_64, self.label_65, self.label_66, self.label_67], 
                    [self.label_70, self.label_71, self.label_72, self.label_73, self.label_74, self.label_75, self.label_76, self.label_77]]
        #  Создали список из QLabel для ориентации по доске
        self.promote_label = QLabel('Пешка достигла конца поля соперника. Введите имя фигуры для превращения:\n(Q - ферзь, R - ладья, B - слон, N - конь)', self)
        self.promote_label.resize(self.promote_label.sizeHint())
        self.promote_label.move(1500, 150)
        self.promote = QLineEdit(self)
        self.promote.move(1500, 200)
        self.promote_btn = QPushButton('ПРЕВРАТИТЬ', self)
        self.promote_btn.move(1500, 250)
        self.promote_label.hide()
        self.promote_btn.hide()
        self.promote.hide()#  Поначалу скрытые виджеты, отвечающие за превращение пешки
        self.turn = QLabel(self)
        self.turn.move(1000, 140)#  Кто ходит
        self.shah = QLabel('Шах: НЕТ', self)
        self.shah.move(1000, 160)# Есть ли шах
        self.sur_btn = QPushButton('СДАТЬСЯ', self)
        self.sur_btn.move(1400, 250)#  Сдаться
        self.input_figure = QLineEdit(self)
        self.input_figure.move(1000, 200)
        self.input_target = QLineEdit(self)
        self.input_target.move(1000, 250)#  Ввод координат фигуры, места, куда она идет
        self.text_1 = QLabel('Введите координаты фигуры', self)
        self.text_1.move(1000, 180)
        self.text_2 = QLabel('Введите координаты цели', self)
        self.text_2.move(1000, 230)
        self.do_it = QPushButton('ВЫПОЛНИТЬ', self)#  Переместить фигуру
        self.do_it.move(1000, 280)
        self.error = QLabel(self)
        self.error.move(1000, 305)#  Будет выводить ошибки
        self.castling_1 = QPushButton('Длинная рокировка', self)
        self.castling_1.move(1200, 200)#  Длинная рокировка
        self.castling_2 = QPushButton('Короткая рокировка', self)
        self.castling_2.move(1200, 250)#  Короткая рокировка
        board.field[0][0] = Rook(WHITE)
        board.field[0][1] = Knight(WHITE)
        board.field[0][2] = Bishop(WHITE)
        board.field[0][3] = Queen(WHITE)
        board.field[0][4] = King(WHITE)
        board.field[0][5] = Bishop(WHITE)
        board.field[0][6] = Knight(WHITE)
        board.field[0][7] = Rook(WHITE)
        for i in range(0, 8):
            board.field[1][i] = Pawn(WHITE)
        board.field[7][0] = Rook(BLACK)
        board.field[7][1] = Knight(BLACK)
        board.field[7][2] = Bishop(BLACK)
        board.field[7][3] = Queen(BLACK)
        board.field[7][4] = King(BLACK)
        board.field[7][5] = Bishop(BLACK)
        board.field[7][6] = Knight(BLACK)
        board.field[7][7] = Rook(BLACK)
        for i in range(0, 8):
            board.field[6][i] = Pawn(BLACK)
        #  Создали фигуры на доске
        self.visualisate()
        self.do_it.clicked.connect(self.compilate)
        self.castling_1.clicked.connect(self.long_castling)
        self.castling_2.clicked.connect(self.short_castling)
        self.sur_btn.clicked.connect(self.surrender)
        self.promote_btn.clicked.connect(self.pawn_promotion_2)
        self.pawn_coords = [0, 0]

    def compilate(self):#  Переместить фигуру или вывести ошибку
        try:
            figure_1 = self.input_figure.text()
            figure_2 = self.input_target.text()
            figure_1 = [int(figure_1[1]) - 1, COORDS[figure_1[0].upper()]]
            figure_2 = [int(figure_2[1]) - 1, COORDS[figure_2[0].upper()]]
            if board.move_piece(figure_1[0], figure_1[1], figure_2[0], figure_2[1]):
                self.error.setText('')
                if board.color == WHITE:
                    BLACK_FIGURES[BLACK_FIGURES.index(figure_1)] = figure_2
                    if figure_2 in WHITE_FIGURES:
                        del WHITE_FIGURES[WHITE_FIGURES.index(figure_2)]
                if board.color == BLACK:
                    WHITE_FIGURES[WHITE_FIGURES.index(figure_1)] = figure_2
                    if figure_2 in BLACK_FIGURES:
                        del BLACK_FIGURES[BLACK_FIGURES.index(figure_2)]
                piece = board.get_piece(figure_2[0], figure_2[1])
                if piece.char() == 'P':
                    self.pawn_coords = [figure_2[0], figure_2[1]]
                    if piece.color == WHITE and figure_2[0] == 7:
                        self.pawn_promotion_1()
                    elif piece.color == BLACK and figure_2[0] == 0:
                        self.pawn_promotion_1()
            else:
                self.error.setText('Ошибка')
                self.error.resize(self.error.sizeHint())
        except Exception:
            self.error.setText('Ошибка')
            self.error.resize(self.error.sizeHint())
        if board.king_alert():
            self.shah.setText('Шах: ЕСТЬ')
        else:
            self.shah.setText('Шах: НЕТ')
        self.shah.resize(self.shah.sizeHint())
        self.visualisate()
        self.input_figure.setText('')
        self.input_target.setText('')

    def long_castling(self):#  Длинная рокировка
        if board.color == WHITE:
            if board.castling_0(0, 4, 0, 0):
                WHITE_FIGURES[WHITE_FIGURES.index([0, 4])] = [0, 2]
                WHITE_FIGURES[WHITE_FIGURES.index([0, 0])] = [0, 3]
        if board.color == BLACK:
            if board.castling_0(7, 4, 7, 0):
                BLACK_FIGURES[BLACK_FIGURES.index([7, 4])] = [7, 2]
                BLACK_FIGURES[BLACK_FIGURES.index([7, 0])] = [7, 3]
        self.visualisate()
                
    def short_castling(self):#  Короткая рокировка
        if board.color == WHITE:
            if board.castling_7(0, 4, 0, 7):
                WHITE_FIGURES[WHITE_FIGURES.index([0, 4])] = [0, 6]
                WHITE_FIGURES[WHITE_FIGURES.index([0, 7])] = [0, 5]
        if board.color == BLACK:
            if board.castling_7(7, 4, 7, 7):
                BLACK_FIGURES[BLACK_FIGURES.index([7, 4])] = [7, 6]
                BLACK_FIGURES[BLACK_FIGURES.index([7, 7])] = [7, 5]
        self.visualisate()

    def visualisate(self):#  Отобразить фигуры на доске
        if board.color == WHITE:
            self.turn.setText('Ходит: {0}, {1}'.format(FIRST_PLAYER[0], 'БЕЛЫЙ'))
        elif board.color == BLACK:
            self.turn.setText('Ходит: {0}, {1}'.format(SECOND_PLAYER[0], 'ЧЕРНЫЙ'))
        self.turn.resize(self.turn.sizeHint())
        for row in range(7, -1, -1):
            for col in range(8):
                piece_1 = board.get_piece(row, col)
                if piece_1 is not None:
                    if piece_1.color == WHITE:
                        self.vis[row][col].setText('<p style="color: rgb(255, 255, 255);">{0}</p>'.format(piece_1.char()))
                        self.vis[row][col].setFont(QFont("Times", 24, QFont.Bold))
                        self.vis[row][col].adjustSize()
                    else:
                        self.vis[row][col].setText('<p style="color: rgb(0, 0, 0);">{0}</p>'.format(piece_1.char()))
                        self.vis[row][col].setFont(QFont("Times", 24, QFont.Bold))
                        self.vis[row][col].adjustSize()
                else:
                    self.vis[row][col].setText('')
        
    def pawn_promotion_1(self):#  Можно превратить пешку
        self.promote_btn.show()
        self.promote_label.show()
        self.promote.show()
        self.input_figure.hide()
        self.input_target.hide()
        self.text_1.hide()
        self.text_2.hide()
        self.castling_1.hide()
        self.castling_2.hide()
        self.do_it.hide()

    def pawn_promotion_2(self):#  Превратить пешку
        char = self.promote.text()
        char = char.upper()
        if char in 'QNKB':
            board.promote_pawn(char, self.pawn_coords)
        self.visualisate()
        self.promote.setText('')
        self.promote_btn.hide()
        self.promote_label.hide()
        self.promote.hide()
        self.input_figure.show()
        self.input_target.show()
        self.text_1.show()
        self.text_2.show()
        self.castling_1.show()
        self.castling_2.show()
        self.do_it.show()
                    
    def surrender(self):#  Сдаться, закончить игру
        global FIRST_PLAYER
        global SECOND_PLAYER
        if board.color == WHITE:
            lose = FIRST_PLAYER[0]
            win = SECOND_PLAYER[0]
        elif board.color == BLACK:
            lose = SECOND_PLAYER[0]
            win = FIRST_PLAYER[0]
        con = sqlite3.connect("players_list.db")
        cur = con.cursor()
        info_1 = cur.execute("""SELECT win FROM player_statistics WHERE player_nickname = ?""", (lose,)).fetchone()[0]
        info_2 = cur.execute("""SELECT lose FROM player_statistics WHERE player_nickname = ?""", (lose,)).fetchone()[0]
        info_2 += 1
        cur.execute("""UPDATE player_statistics
                    SET win = ?, lose = ?, win_lose = ?
                    WHERE player_nickname = ?""", (info_1, info_2, round(info_1 / info_2, 2), lose))
        info_1 = cur.execute("""SELECT win FROM player_statistics WHERE player_nickname = ?""", (win,)).fetchone()[0]
        info_2 = cur.execute("""SELECT lose FROM player_statistics WHERE player_nickname = ?""", (win,)).fetchone()[0]
        info_1 += 1
        if info_2 == 0:
            info_2 = 1
        cur.execute("""UPDATE player_statistics
                    SET win = ?, lose = ?, win_lose = ?
                    WHERE player_nickname = ?""", (info_1, info_2 - 1, round(info_1 / info_2, 2), win))
        con.commit()
        FIRST_PLAYER = FIRST_PLAYER[0]
        SECOND_PLAYER = SECOND_PLAYER[0]
        self.ex_1 = Counter()
        self.ex_1.show()
        self.hide()


board = Board()#  Создаем доску
WHITE_FIGURES = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [1, 0], [1, 1], [1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7]]
BLACK_FIGURES = [[7, 0], [7, 1], [7, 2], [7, 3], [7, 4], [7, 5], [7, 6], [7, 7], [6, 0], [6, 1], [6, 2], [6, 3], [6, 4], [6, 5], [6, 6], [6, 7]]
#  Создали реестры фигур для ориентации по доске
COORDS = {
            'A': 0,
            'B': 1,
            'C': 2,
            'D': 3,
            'E': 4,
            'F': 5,
            'G': 6,
            'H': 7
        }#  Словарь для замены букв в координатах клетки на цифры, понятные коду


if __name__ == '__main__':#  Запуск
    app = QApplication(sys.argv)
    ex = Starter()
    ex.show()
    sys.exit(app.exec())