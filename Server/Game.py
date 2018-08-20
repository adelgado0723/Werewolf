import time
import threading
import Player
class Game:
    def __init__(self, name):
        self.players = [] # A list of the players in this game.
        self.game_name = name
        self.status = 'IN_WAITING_ROOM'
        self.timer = threading.Event()
        self.roles_set = threading.Event()
        self.accepting_choices = threading.Event()
        self.accepting_special_choices = threading.Event()
        self.game_over = threading.Event()
        self.player_game_state = {} # Relates a player and their state in the game {player1 : state} where state is "DEAD" or "ALIVE"
        self.choices = {} # Relates two players {player1 : player2} where player1 chooses player2
        self.special_choices = {} # Relates two players {player1 : player2} where player1 chooses player2
        self.game_thread = None
        self.werewolf = None
        self.healer = None
        self.sheriff = None
        self.choices_lock = threading.Lock()
        self.special_choices_lock = threading.Lock()
        self.round_over = threading.Event()

    def welcome_player(self, player_name):
        all_players = self.get_all_players_in_game()

        for player in self.players:
            if player.player_name is player_name:
                chatMessage = '\n> {0} have joined the game, {1}!\n|{2}'.format("You", self.game_name, all_players).encode('utf8')
                player.socket.sendall(chatMessage)
            else:
                chatMessage = '\n> {0} has joined the game, {1}!\n|{2}'.format(player_name, self.game_name, all_players).encode('utf8')
                player.socket.sendall(chatMessage)

    def broadcast_message(self, chatMessage, player_name=''):
        for player in self.players:
            if player.player_name is player_name:
                player.socket.sendall("You: {0}".format(chatMessage).encode('utf8'))
            else:
                player.socket.sendall("{0} {1}".format(player_name, chatMessage).encode('utf8'))

    def get_all_players_in_game(self):
        return ' '.join([player.player_name for player in self.players])

    def remove_player_from_game(self, player):
        self.players.remove(player)
        leave_message = "\n> {0} has left the game {1}\n".format(player.player_name, self.game_name)
        self.broadcast_message(leave_message)


    def create_timer(self, time):
        self.timer.clear()
        timer_thread = threading.Thread(target=self.set_game_timer, args=(time,))
        timer_thread.start()
        
    def set_game_timer(self, sleep_time):
        time.sleep(sleep_time)
        is_set = self.timer.wait(2)
        if not is_set:
            self.timer.set()

