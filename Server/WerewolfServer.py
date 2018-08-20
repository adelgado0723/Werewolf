import random
import socket
import sys
import threading
import Game
import Player
import time

class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 100}

    HELP_MESSAGE = """\n> The list of commands available are:
> 
> /help                   - Show the instructions
> /join [game_name]       - To create or switch to a game.
> /quit                   - Exits the program.
> /clear                  - Clears screen of text.
> /choose [player_name]   - Used to make decisions in a game.
> /list                   - Lists all available games.\n\n""".encode('utf8')


    WELCOME_MESSAGE_ONE = """> 
> Welcome to our village. 
> 
> Recently, the sheriff has been receiving reports of missing
> villagers as well as sightings of a strange beast in the 
> forest on the outskirts of the village. He is starting
> to think that the two might be connected.""".encode('utf8')

    RING = "\n> RING!\n> (The phone at the sheriff's desk goes off.)".encode('utf8') 

    WELCOME_MESSAGE_TWO = """\n>
> One of the missing villagers was just found dead in the forest. 
> The body is covered with deep lacerations and teeth marks. 
> 
>""".encode('utf8')
    
    WELCOME_MESSAGE_THREE = """\n> INSTRUCTIONS:
>
> The game takes place in a chat room where users play the role of villagers 
> investigating a series of crimes. They dont know who the murderer is, but 
> they do know that he/she passes off as a villager during the day. This has 
> led them to adopt the practice of casting out one villager per day in hopes 
> of casting out the murderer.
> 
> Three of the villagers play a special role:
> 		The werewolf chooses one villager to attack per day
> 		The sheriff chooses one villager to investigate per day
> 		The healer protects one villager per day
> 
> These special characters get an opportunity to perform their secret tasks at 
> night while the villagers are sleeping. The sheriff gets to learn about the 
> secret identity of the villager that they choose to investigate (identity = 
> {villager, healer, werewolf}). If the villager that the healer chooses is 
> the same as the villager that the werewolf chooses, then that person 
> survives the round. Otherwise, the person is killed by the wolf. 
> 
> The following morning, the nightly occurrences mentioned above are revealed 
> to the entire village and they are asked to deliberate and choose a villager 
> to cast out. Villagers are encouraged to chat and combine their knowledge 
> about who the werewolf could be before voting. However, they must be careful 
> as the wolf could be saying things to lead them astray!
> 
> The werewolf wins the game if he/she manages to dwindle to flock of villagers 
> down to two (including the wolf). The villagers win if they cast out the wolf 
> successfully.
>\n""".encode('utf8')

    DOTS = "\n> ..."
    TIME_TO_DELIBERATE = 300
    TIME_IN_LOBBY = 120
    TIME_TO_DELIBERATE_S = 300
    PLAYERS_PER_GAME = 15


    def __init__(self, host=socket.gethostbyname('0.0.0.0'), port=1301, allowReuseAddress=True, timeout=3):
        self.address = (host, port)
        self.games = {} # Game Name -> Game
        self.players_games_map = {} # User Name -> Game Name
        self.client_thread_list = [] # A list of all threads that are either running or have finished their task.
        self.players = [] # A list of all the players who are connected to the server.
        self.exit_signal = threading.Event()

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - {0}".format(errorMessage))
            raise

        self.serverSocket.settimeout(timeout)

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0], self.address[1], errorMessage))
            raise

    def start_listening(self, defaultGreeting="\n> Welcome to our game app!!! What is your full name?\n"):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])

        try:
            while not self.exit_signal.is_set():
                try:
                    print("Waiting for a client to establish a connection\n")
                    clientSocket, clientAddress = self.serverSocket.accept()
                    print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0], clientAddress[1]))
                    player = Player.Player(clientSocket)
                    self.players.append(player)
                    clientThread = threading.Thread(target=self.client_thread, args=(player,))
                    clientThread.start()
                    self.client_thread_list.append(clientThread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            self.exit_signal.set()

        for client in self.client_thread_list:
            if client.is_alive():
                client.join()
        for key, value in self.games:
                value.game_thread.join()
                

    def welcome_player(self, player):
        player.socket.sendall(Server.WELCOME_MESSAGE_ONE)
        time.sleep(6)
        
        for i in range(3):
            player.socket.sendall(Server.DOTS.encode('utf8'))
            time.sleep(1)

        player.socket.sendall(Server.RING)
        time.sleep(2)
        
        for i in range(3):
            player.socket.sendall(Server.DOTS.encode('utf8'))
            time.sleep(1)

        player.socket.sendall(Server.WELCOME_MESSAGE_TWO)
        time.sleep(6)

        for i in range(3):
            player.socket.sendall(Server.DOTS.encode('utf8'))
            time.sleep(1)

        player.socket.sendall(Server.WELCOME_MESSAGE_THREE)

    def client_thread(self, player, size=4096):

        self.welcome_player(player)
        player_name = ""
        unique = False
        while not player_name or  unique == False:
            player.socket.sendall("\n> Please enter a unique username.\n".encode('utf8'))
            player_name = player.socket.recv(size).decode('utf8')
            if not player_name in self.players:
                unique = True


        player.player_name = player_name

        player.socket.sendall("\n> Welcome, {0}. We hope you enjoy your stay in our village.\n".format(player.player_name).encode('utf8'))
        welcomeMessage = '\n> Type /help for a list of commands.\n\n'.format().encode('utf8')
        player.socket.sendall(welcomeMessage)

        while True:
            self.listen_for_commands(player, "")

        if self.exit_signal.is_set():
            player.socket.sendall('/squit'.encode('utf8'))

        player.socket.close()

    def quit(self, player):
        player.socket.sendall('/quit'.encode('utf8'))
        self.remove_player(player)

    def list_all_games(self, player):
        if len(self.games) == 0:
            inputString = "\n> No games available. Create your own by typing /join [game_name]\n".encode('utf8')
            player.socket.sendall(inputString)
        else:
            inputString = '\n\n> Current games available are: \n'
            for game in self.games:
                inputString += "    \n" + game + ": " + str(len(self.games[game].players)) + " player(s)"
            inputString += "\n"
            player.socket.sendall(inputString.encode('utf8'))

    def help(self, player):
        player.socket.sendall(Server.HELP_MESSAGE)

    def join(self, player, inputString):
        isInSameRoom = False

        if len(inputString.split(" ")) >= 2:
            gameName = inputString.split(" ")[1]
            gameExists = 0

            if player.player_name in self.players_games_map: 
                if self.players_games_map[player.player_name] == gameName:
                    player.socket.sendall("\n> You are already in game: {0}".format(gameName).encode('utf8'))
                    isInSameRoom = True
                else: # switch to a new game
                    oldGameName = self.players_games_map[player.player_name]
                    self.games[oldGameName].remove_player_from_game(player) # remove them from the previous game

            if not isInSameRoom:
                if not gameName in self.games:
                    newGame = Game.Game(gameName)
                    self.games[gameName] = newGame
                    print("Game Thread Being Created!\n")
                    self.games[gameName].game_thread = threading.Thread(target=self.play_game, args=(player, inputString, gameName))
                    self.games[gameName].game_thread.start()
                    # Game Lobby counter starts (could happen in Game initializer)

                if self.games[gameName].status == 'IN_WAITING_ROOM' and len(self.games[gameName].players) < Server.PLAYERS_PER_GAME:    
                    self.games[gameName].players.append(player)
                    self.games[gameName].player_game_state[self.games[gameName].players.index(player)] = "ALIVE"

                    self.games[gameName].welcome_player(player.player_name)
                    self.players_games_map[player.player_name] = gameName

                    self.play_turns(player, inputString, gameName)

                else:
                    player.socket.sendall("\n> Cannot join {0}.\n> {0} is a game in progress.".format(gameName).encode('utf8'))

        else:
            self.help(clientSocket)

    def play_turns(self, player, inputString, gameName):
        # Waiting in a non-blocking fashion
        while not self.games[gameName].game_over.isSet():
            is_set = self.games[gameName].game_over.wait(2)
            if is_set:
                self.games[gameName].remove_player_from_game(player) 
                break # game is over

            else:
                # play a game
                self.listen_for_commands(player, gameName)


    # To be used ONLY IF we already know that the player 
    # is in the gameName provided and roles have been assigned.
    def get_role(self, player_name, gameName):
        player = -1
        for p in self.games[gameName].players:
            if player_name == p.player_name:
                player = self.games[gameName].players.index(p)
        if player == self.games[gameName].werewolf:
            return "werewolf"
        elif player == self.games[gameName].healer:
            return "healer"
        elif player == self.games[gameName].sheriff:
            return "sheriff"
        else:
            return "villager"


    def play_game(self, player, inputString, gameName):

        # Lobby Area 
        # After One Minute or 10 players in channel
        # start game.

        self.games[gameName].broadcast_message("\n> Game {0} in Lobby area...".format(gameName))
        self.games[gameName].broadcast_message("\n> Game {0} will begin in {1} seconds...".format(gameName, Server.TIME_IN_LOBBY))

        self.games[gameName].create_timer(Server.TIME_IN_LOBBY)
        while not self.games[gameName].timer.isSet():
            is_set = self.games[gameName].timer.wait(2)
            if is_set:
                break # continue on to start the game 


        self.games[gameName].status == 'IN_PROGRESS'
        self.games[gameName].broadcast_message("\n> Game, {0}, Game is now starting!".format(gameName))
        # Create bots

        # Randomly assign roles:
        num_players = len(self.games[gameName].players)

        self.games[gameName].broadcast_message("\n> The fates are assigning players the role that they will play.")

        self.games[gameName].broadcast_message(Server.DOTS)
        time.sleep(1)

        self.games[gameName].broadcast_message(Server.DOTS)
        time.sleep(1)

        self.games[gameName].broadcast_message(Server.DOTS)
        time.sleep(1)

        random_index1 = random.randint(0, num_players-1)
        random_index2 = random_index1
        while random_index1 == random_index2:
            random_index2 = random.randint(0, num_players-1)

        random_index3 = random_index1
        while random_index3 == random_index2 or random_index3 == random_index1:
            random_index3 = random.randint(0, num_players-1)

        self.games[gameName].werewolf = random_index1
        self.games[gameName].healer = random_index2
        self.games[gameName].sheriff = random_index3

        for player in self.games[gameName].players:
            if  self.games[gameName].players.index(player) == self.games[gameName].werewolf:
                player.socket.sendall("\n>>> You are the werewolf in villager clothing!\n>\n>\n>".encode("utf8"))
            elif self.games[gameName].players.index(player) == self.games[gameName].healer:
                player.socket.sendall("\n>>> You are the healer. Your village needs your help!\n>\n>\n>".encode("utf8"))
            elif self.games[gameName].players.index(player) == self.games[gameName].sheriff:
                player.socket.sendall("\n>>> You are the sheriff. Solve the recent crimes!\n>\n>\n>".encode("utf8"))
            else:
                player.socket.sendall("\n>>> You are a villager. Survive these tough times!\n>\n>\n>".encode("utf8"))

        # Clearing timer for next section before releasing player threads
        self.games[gameName].timer.clear()
        self.games[gameName].roles_set.set()

        # Playing turns until there are 2 players left
        # or the werewolf has been killed.

        while not self.games[gameName].game_over.isSet():
            is_set = self.games[gameName].game_over.wait(2)
            if is_set:
                self.games[gameName].status == 'GAME_OVER'

                tmp = self.games
                del tmp[gameName]
                self.games = tmp
                break # game is over

            else:
                self.games[gameName].round_over.clear()

                # play a turn
                self.games[gameName].broadcast_message("\n> The sun sets on another day in the village with the creature still on the loose.\n>\n>\n>")
                self.games[gameName].broadcast_message("\n> {0} seconds until the sun rises.".format(Server.TIME_TO_DELIBERATE_S))

                self.games[gameName].broadcast_message("\n> The werewolf stalks its prey.")
                self.games[gameName].broadcast_message(Server.DOTS)
                self.games[gameName].broadcast_message("\n> The healer protects a villager in danger.")
                self.games[gameName].broadcast_message(Server.DOTS)
                self.games[gameName].broadcast_message("\n> The sheriff investigates a suspicious villager.\n>\n>")
                self.games[gameName].broadcast_message(Server.DOTS)


                self.games[gameName].players[self.games[gameName].werewolf].socket.sendall("\n>>> Choose a villager to attack from the list of player_names.\n>>> Use the /choose [player_name] command to make your selection.".encode("utf8"))
                self.games[gameName].players[self.games[gameName].healer].socket.sendall("\n>>> Choose a villager to protect from the list of player_names.\n>>> Use the /choose [player_name] command to make your selection.".encode("utf8"))
                self.games[gameName].players[self.games[gameName].sheriff].socket.sendall("\n>>> Choose a villager to investigate and discover who they really are.\n>>> Use the /choose [player_name] command to make your selection.".encode("utf8"))

                self.games[gameName].create_timer(Server.TIME_TO_DELIBERATE_S)
                self.games[gameName].accepting_special_choices.set()


                # Time for each special player to make their decision
                while not self.games[gameName].timer.isSet():
                    is_set = self.games[gameName].timer.wait(2)

                    self.games[gameName].special_choices_lock.acquire()
                    len_special_choices = len(self.games[gameName].special_choices)
                    print("Count of special choices made: ".format(len_special_choices))
                    self.games[gameName].special_choices_lock.release()

                    if is_set:
                        self.games[gameName].accepting_special_choices.clear()
                        break # continue on to revelation
                    else: 
                        self.games[gameName].special_choices_lock.acquire()
                        # Check if everyone has made a choice before time is up
                        if len_special_choices == 3:
                            self.games[gameName].timer.set()
                        self.games[gameName].special_choices_lock.release()

                # Done choosing
                self.games[gameName].broadcast_message("\n> Time is up for the werewolf, healer, and sheriff.\n> If they did not choose a target, \n> one will be chosen for them now.\n>")
                self.games[gameName].accepting_special_choices.clear()

                self.games[gameName].special_choices_lock.acquire()

                # If someone didn't choose, choose for them
                
                
                # Werewolf didn't choose.
                if not self.games[gameName].werewolf in self.games[gameName].special_choices:
                    if self.games[gameName].special_choices[self.games[gameName].healer]:
                        index = random.randint(0, len(self.games[gameName].players)-1)
                        target = self.games[gameName].players[index]
                        while self.games[gameName].werewolf == self.games[gameName].players.index(target) or self.games[gameName].player_game_state[self.games[gameName].players.index(target)] == "DEAD":
                            index = random.randint(0, len(self.games[gameName].players)-1)
                            target = self.games[gameName].players[index]
                        self.games[gameName].special_choices[self.games[gameName].werewolf] = self.games[gameName].players.index(target)
                        self.games[gameName].players[self.games[gameName].werewolf].socket.sendall("\n>>> You are attacking {0}\n>".format(target.player_name).encode("utf8"))

                # Healer didn't coose
                if not self.games[gameName].healer in self.games[gameName].special_choices:
                    if self.games[gameName].player_game_state[self.games[gameName].healer] == "ALIVE":
                        index = random.randint(0, len(self.games[gameName].players)-1)
                        target = self.games[gameName].players[index]
                        while self.games[gameName].player_game_state[self.games[gameName].players.index(target)] == "DEAD":
                            index = random.randint(0, len(self.games[gameName].players)-1)
                            target = self.games[gameName].players[index]
                        self.games[gameName].special_choices[self.games[gameName].healer] = self.games[gameName].players.index(target)
                        self.games[gameName].players[self.games[gameName].healer].socket.sendall("\n>>> You are protecting {0}\n>".format(target.player_name).encode("utf8"))
                # Sheriff didn't choose
                if not self.games[gameName].sheriff in self.games[gameName].special_choices:
                    if self.games[gameName].player_game_state[self.games[gameName].sheriff] == "ALIVE":
                        index = random.randint(0, len(self.games[gameName].players)-1)
                        target = self.games[gameName].players[index]
                        while self.games[gameName].sheriff ==  self.games[gameName].players.index(target) or self.games[gameName].player_game_state[self.games[gameName].players.index(target)] == "DEAD":
                            index = random.randint(0, len(self.games[gameName].players)-1)
                            target = self.games[gameName].players[index]
                        self.games[gameName].special_choices[self.games[gameName].sheriff] = self.games[gameName].players.index(target)
                        self.games[gameName].players[self.games[gameName].sheriff].socket.sendall("\n>>> You are investigating {0}\n>".format(target.player_name).encode("utf8"))
                        self.games[gameName].players[self.games[gameName].sheriff].socket.sendall("\n>>> You chose to investigate {0}.\n>>> You found out that they are really a: {1}!\n>".format(target.player_name, self.get_role( target.player_name, gameName )).encode("utf8"))



                # reveal to sheriff the role of the person they chose
                # send confirmation message

                self.games[gameName].special_choices_lock.release()

                self.games[gameName].broadcast_message("\n> The sun rises. What will it reveal today?")
                self.games[gameName].broadcast_message(Server.DOTS)

                # Events resolve and announcements are made
                # Wolf's victim gets killed if healer did not protect them
                if self.games[gameName].special_choices[self.games[gameName].werewolf] == self.games[gameName].special_choices[self.games[gameName].healer]:
                    self.games[gameName].broadcast_message("\n> The healer successfully protected the villager targeted by the wolf!.\n>\n>")
                else:
                    self.games[gameName].broadcast_message("\n> {0} was found dead this morning.\n>\n>".format(self.games[gameName].players[self.games[gameName].special_choices[self.games[gameName].werewolf]].player_name))
                    self.games[gameName].player_game_state[self.games[gameName].special_choices[self.games[gameName].werewolf]] = "DEAD"


                # Checking if game is over
                # Count number of players still alive
                players_alive = 0
                for p in self.games[gameName].player_game_state:
                    if self.games[gameName].player_game_state[p] == "ALIVE":
                        players_alive = players_alive + 1


                if self.games[gameName].player_game_state[self.games[gameName].werewolf] == "DEAD" or players_alive <= 2:
                    if self.games[gameName].player_game_state[self.games[gameName].werewolf] == "DEAD":
                        # if wolf was killed => Congratulate villagers
                        self.games[gameName].broadcast_message("\n> Congratulations, Villagers!\n> You vanquished the werewolf!\n>\n>")
                    else:  
                        # else => congratulate wolf
                        self.games[gameName].broadcast_message("\n> Congratulations, {0}!\n> As the werewolf, you made tasty treats out of another village!\n>\n>".format(self.games[gameName].players[self.games[gameName].werewolf].player_name))

                    self.games[gameName].broadcast_message("\n> This game has ended, but you are welcome to stay and chat.\n>\n>")
                    self.games[gameName].game_over.set()
                    self.games[gameName].round_over.set()
                    continue

                self.games[gameName].broadcast_message(Server.DOTS)
  
                # Counting the number of living villagers
                living = 0
                for p in self.games[gameName].players:
                    if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":
                        living = living + 1

                print("> {0} villagers left alive in game: {1}".format(living, gameName))
                self.games[gameName].broadcast_message("\n> {0} villagers left alive in game, {1}\n>\n>".format(living, gameName))

                tie = 1
                self.games[gameName].broadcast_message("\n>\n>\n> The sun is setting on today.\n> Villagers must agree on someone to cast out within {0} seconds.\n>\n>".format(Server.TIME_TO_DELIBERATE))
                self.games[gameName].broadcast_message("\n> Use the /choose [player_name] command to make your selection.")
                # time to discuss
                self.games[gameName].create_timer(Server.TIME_TO_DELIBERATE)
                self.games[gameName].accepting_choices.set()
                # Time for each special player to make their decision
                while not self.games[gameName].timer.isSet():
                    is_set = self.games[gameName].timer.wait(2)
                    self.games[gameName].choices_lock.acquire()
                    len_choices = len(self.games[gameName].choices)
                    self.games[gameName].choices_lock.release()
                    if is_set:
                        self.games[gameName].accepting_choices.clear()
                        break # continue 
                    else: 
                        self.games[gameName].choices_lock.acquire()
                        # Check if everyone has made a choice before time is up
                        if len_choices == living:
                            self.games[gameName].timer.set()
                        self.games[gameName].choices_lock.release()
                
                # Done choosing
                self.games[gameName].broadcast_message("\n> Time is up for the villagers to choose who is getting cast out.\n> If they did not choose a target, one will be chosen for them now.\n>")
                self.games[gameName].accepting_choices.clear()
                self.games[gameName].choices_lock.acquire()
                # If someone didn't choose, choose for them 
                for p in self.games[gameName].players:
                    if not self.games[gameName].players.index(p) in self.games[gameName].choices:
                        if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":
                            # Choose for villager (not themselves)
                            index = random.randint(0, len(self.games[gameName].players)-1)
                            target = self.games[gameName].players[index]
                            while self.games[gameName].players.index(p) == self.games[gameName].players.index(target) or self.games[gameName].player_game_state[self.games[gameName].players.index(target)] == "DEAD":
                                index = random.randint(0, len(self.games[gameName].players)-1)
                                target = self.games[gameName].players[index]
                            self.games[gameName].choices[self.games[gameName].players.index(p)] = self.games[gameName].players.index(target)
                            self.games[gameName].broadcast_message("\n> {0} votes to cast out {1}\n>".format(p.player_name, self.games[gameName].players[self.games[gameName].players.index(target)].player_name))
                # Sum up votes and cast out person
                voting_results = {}
                for p in self.games[gameName].player_game_state:
                    if self.games[gameName].player_game_state[p] == "ALIVE":
                        voting_results[p] = 0 
                for p in self.games[gameName].choices:
                    voting_results[self.games[gameName].choices[p]] = voting_results[self.games[gameName].choices[p]] + 1
                # Broadcasting result and finding maximum votes
                max_votes = 0
                for p in voting_results:
                    self.games[gameName].broadcast_message("\n> Villager {0}, received {1} vote(s) to be cast out.\n>".format( self.games[gameName].players[p].player_name, voting_results[p]))
                    if voting_results[max_votes] < voting_results[p]:
                        max_votes = p
                tie_counter = 0
                for p in voting_results:
                    if voting_results[p] == voting_results[max_votes]:
                        tie_counter = tie_counter + 1
                if tie_counter > 1:
                    self.games[gameName].broadcast_message("\n> There has been a tie, no one is cast out....")
                    
                else:
                    tie = 0;
                    # Casting out a villager
                    self.games[gameName].broadcast_message("\n> Villager {0}, is cast out!\n>".format(self.games[gameName].players[max_votes].player_name))
                    self.games[gameName].player_game_state[max_votes] = "DEAD"
                self.games[gameName].choices_lock.release()

                # Checking if game is over

                # Count number of players still alive
                players_alive = 0
                for p in self.games[gameName].player_game_state:
                    if self.games[gameName].player_game_state[p] == "ALIVE":
                        players_alive = players_alive + 1

                if self.games[gameName].player_game_state[self.games[gameName].werewolf] == "DEAD" or players_alive <= 2:
                    if self.games[gameName].player_game_state[self.games[gameName].werewolf] == "DEAD":
                        # if wolf was killed => Congratulate villagers
                        self.games[gameName].broadcast_message("\n> Congratulations, Villagers!\n> You vanquished the werewolf!\n>\n>")
                    else:  
                        # else => congratulate wolf
                        self.games[gameName].broadcast_message("\n> Congratulations, {0}!\n> As the werewolf, you made tasty treats out of another village!\n>\n>".format(self.games[gameName].players[self.games[gameName].werewolf].player_name))

                    self.games[gameName].broadcast_message("\n> This game has ended, but you are welcome to stay and chat.\n>\n>")
                    self.games[gameName].game_over.set()

                self.games[gameName].round_over.set()

                self.games[gameName].choices = {}
                self.games[gameName].special_choices = {}

        return

    def  listen_for_commands(self, player, gameName):

        inputString = player.socket.recv(4096).decode('utf8').lower()

        if self.exit_signal.is_set():
            return

        if not inputString:
            return

        if '/quit' in inputString:
            self.quit(player)
            return
        elif '/list' in inputString:
            self.list_all_games(player)
        elif '/help' in inputString:
            self.help(player)
        elif '/join' in inputString:
            self.join(player, inputString)
        elif '/choose' in inputString:
            self.choose(player, inputString.split(" ")[1], gameName)
        else:
            self.send_message(player, inputString + '\n')


    def choose(self, player, inputString, gameName):

        for p in self.games[gameName].players:
            if p.player_name == player.player_name:
                player = p

        if player in self.games[gameName].players:
            # Player is in game they are requesting to choose
            # Check if choosing is appropriate at this time
            choices_set = self.games[gameName].accepting_choices.isSet()
            special_choices_set = self.games[gameName].accepting_special_choices.isSet()
            is_alive = self.games[gameName].player_game_state[self.games[gameName].players.index(player)]

            if is_alive == "ALIVE":
                if choices_set:
                    self.games[gameName].choices_lock.acquire() 
                    for p in self.games[gameName].players:
                        if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":
                            if p.player_name == inputString:
                                self.games[gameName].choices[self.games[gameName].players.index(player)] = self.games[gameName].players.index(p)

                                self.games[gameName].broadcast_message("\n> {0} votes to cast out {1}\n>".format(player.player_name, p.player_name))
                        else:
                            inputString = """\n> The villager you chose is already dead!\n> Choose a different villager to attack!\n>""".encode('utf8')

                    self.games[gameName].choices_lock.release() 

                elif special_choices_set:
                    # confirm that they are a special player
                    if self.games[gameName].players.index(player) == self.games[gameName].werewolf:
                        self.games[gameName].special_choices_lock.acquire() 
                        for p in self.games[gameName].players:
                            if p.player_name == inputString:
                                if not self.games[gameName].players.index(p) == self.games[gameName].werewolf:
                                    if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":

                                        self.games[gameName].special_choices[self.games[gameName].werewolf] = self.games[gameName].players.index(p)
                                        self.games[gameName].players[self.games[gameName].werewolf].socket.sendall("\n> You are attacking {0}\n>".format(p.player_name).encode("utf8"))

                                    else:
                                        inputString = """\n> The villager you chose is already dead!\n> Choose a different villager to attack!\n>""".encode('utf8')
                                        break

                                else:
                                    inputString = """\n> You are the werewolf!\n> Choose a different villager to attack!\n>""".encode('utf8')
                                    break
                        self.games[gameName].special_choices_lock.release() 


                    elif self.games[gameName].players.index(player) == self.games[gameName].healer:
                        self.games[gameName].special_choices_lock.acquire() 
                        for p in self.games[gameName].players:
                            if p.player_name == inputString:
                                if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":

                                    self.games[gameName].special_choices[self.games[gameName].healer] = self.games[gameName].players.index(p)
                                    self.games[gameName].players[self.games[gameName].healer].socket.sendall("\n> You are protecting {0}\n>".format(p.player_name).encode("utf8"))

                                else:
                                    inputString = """\n> The villager you chose is already dead!\n> Choose a different villager to protect!\n>""".encode('utf8')
                        self.games[gameName].special_choices_lock.release() 

                    elif self.games[gameName].players.index(player) == self.games[gameName].sheriff:
                        self.games[gameName].special_choices_lock.acquire() 
                        for p in self.games[gameName].players:
                            if p.player_name == inputString:
                                if not self.games[gameName].players.index(p) == self.games[gameName].sheriff:
                                    if self.games[gameName].player_game_state[self.games[gameName].players.index(p)] == "ALIVE":
                                        self.games[gameName].special_choices[self.games[gameName].sheriff] = self.games[gameName].players.index(p)
                                        self.games[gameName].players[self.games[gameName].sheriff].socket.sendall("\n>>> You chose to investigate {0}.\n>>> You found out that they are really a: {1}!\n>".format(inputString, self.get_role( p.player_name, gameName )).encode("utf8"))
                                    else:
                                        inputString = """\n> The villager you chose is already dead!\n> Choose a different villager to investigate!\n>""".encode('utf8')
                                        break
                                else:
                                    inputString = """\n> You are the sheriff!\n> Choose a different villager to investigate.\n>""".encode('utf8')
                                    break
                        self.games[gameName].special_choices_lock.release() 

                    else:
                        inputString = """\n> Your are not the werewolf, the healer, or the sheriff.\n>\n>""".encode('utf8')

                else:
                    inputString = """\n> Your game is not receiving decisions at this time.\n>\n>""".encode('utf8')

            else:
                inputString = """\n> You have been killed by the werewolf or exiled from the village.
> You can no longer weigh-in on these decisions.\n>\n>""".encode('utf8')

        else:
            inputString = """\n> You are currently not in any games:
> Use /list to see a list of available games.
> Use /join [game name] to join a game.\n>\n>""".encode('utf8')

            player.socket.sendall(inputString)

    def event_based_timer(self, timeUpEvent, time):
        time.sleep(time)
        timeUpEvent.set()


    def send_message(self, player, inputString):
        if player.player_name in self.players_games_map:
            self.games[self.players_games_map[player.player_name]].broadcast_message(inputString, "{0}: ".format(player.player_name))
        else:
            inputString = """\n> You are currently not in any games:

Use /list to see a list of available games.
Use /join [game name] to join a game.\n\n""".encode('utf8')

            player.socket.sendall(inputString)

    def remove_player(self, player):
        if player.player_name in self.players_games_map:
            self.games[self.players_games_map[player.player_name]].remove_player_from_game(player)
            del self.players_games_map[player.player_name]

        self.players.remove(player)
        print("Client: {0} has left\n".format(player.player_name))

    def server_shutdown(self):
        print("Shutting down game server.\n")
        self.serverSocket.close()

def main():
    werewolfServer = Server()

    print("\nListening on port {0}".format(werewolfServer.address[1]))
    print("Waiting for connections...\n")

    werewolfServer.start_listening()
    werewolfServer.server_shutdown()

if __name__ == "__main__":
    main()
