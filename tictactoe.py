from random import *

chars = ['❌', '⭕️']

class TicTacToe:
    def __init__(self, user_id_1, user_id_2):
        self.players = {user_id_1: ' ', user_id_2: ' '}
        self.field = [[' ' for i in range(3)] for j in range(3)]
        self.player_messages = {
            user_id_1: {'chat_id': None, 'message_id': None},
            user_id_2: {'chat_id': None, 'message_id': None}
        }
        self.state = 'ongoing'
        self.move_count = 0
        self.winner = None
        self.random_move(user_id_1, user_id_2)

    def random_move(self, user_1, user_2):
        shuffle(chars)
        self.players[user_1] = chars[0]
        self.players[user_2] = chars[1]
    
    def move(self, user_id, field_cord):
        row, col = field_cord
        player = self.players[user_id]
        if self.field[row][col] == ' ':
            self.field[row][col] = player
        else:
            raise ValueError('Клетка занята')
        self.move_count += 1
        if self.check_win(row, col, player):
            self.state = 'win'
            self.winner = user_id
            return self.state
        elif self.move_count == 9:
            self.state = 'draw'
            return self.state
        else:
            return self.state

    def check_win(self, row, col, player):
        # Проверка строки
        if all(self.field[row][i] == player for i in range(3)):
            return True
        # Проверка столбца
        if all(self.field[i][col] == player for i in range(3)):
            return True
        # Проверка главной диагонали
        if row == col and all(self.field[i][i] == player for i in range(3)):
            return True
        # Проверка побочной диагонали
        if row + col == 2 and all(self.field[i][2 - i] == player for i in range(3)):
            return True
        return False
    
    def return_str_field(self):
        str_field = ''
        for i in range(3):
            for j in range(3):
                str_field += self.field[i][j].replace(' ', '⬜️')
            str_field += '\n'
        return str_field
    



        

