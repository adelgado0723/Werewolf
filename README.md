# Werewolf!

## Contents

- [**About**](#about)
- [**Commands**](#commands)
- [**Server**](#server)
- [**Client**](#client)



## About

***Werewolf!*** takes place in a chat room where users play the role of villagers
investigating a series of crimes. They don’t know who the murderer is, but they
do know that he/she passes off as a villager during the day. This has led them
to adopt the practice of casting out one villager per day in hopes of casting
out the murderer.

***Three of the villagers play a special role:***

- **The werewolf:** 
	- chooses one villager to attack per day

- **The sheriff:** 
	- chooses one villager to investigate per day
		
- **The healer:**
	- protects one villager per day

These special characters get an opportunity to perform their secret tasks at
night while the villagers are sleeping. 

- The sheriff gets to learn the secret identity of the villager that they
  choose to investigate 
	- identity = {villager, healer, werewolf} 

- If the villager that the healer chooses is ***the same*** as the villager that the
  werewolf chooses, then the person survives that round. Otherwise, the person
  is killed by the wolf. 

The following morning, the nightly occurrences mentioned above are revealed to
the entire village and they are asked to deliberate and choose a villager to
cast out. Villagers are encouraged to chat and combine their knowledge about
who the werewolf could be before voting. However, they must be careful as the
wolf could be spreading misinformation to lead the villagers astray!

The werewolf wins the game if he/she manages to dwindle to flock of villagers
down to two (including the wolf). The villagers win if they cast out the wolf
successfully.


---

## Commands:

| **Command**               | **Description**                    |
|---------------------------|------------------------------------|
| **/help**                 | Display help message               |
| **/join [game_name]**     | Creates or switches into a game    |
| **/quit**                 | Exits the program                  |
| **/clear**                | Clears text on the screen          |
| **/choose [player_name]** | Used to make decisions in the game |
| **/list**                 | Lists all available games          |


## Server:
 
The server binds to the host address and port specified and starts to listen
for client connections. When a client connects, it spawns off a new thread that
listens for commands and runs games when they are created. A player can create
a game with the /join command. Each game has a “game thread” that manages that game.
To synchronize threads within a game, the “game thread” uses python threading
signals.  Games have the following stages:

1. **Lobby** 

	- Accepting players into game about to begin

2. **Assigning Roles** 

	- The game randomly assigns special roles (werewolf, healer, and sheriff)

3. **Playing Turns**
	
	- Night time - Special roles decide who to attack, protect, and investigate
	- Day time   - Results of night time activities are revealed
	- Check if game is over
	- Voting     - Players vote to cast out a villager
	- Check if game is over

The game moves forward with time as players have a restricted amount of time to
make decisions. If they do not make a decision in the allotted time, a choice
is made for them.

### Usage:

From Server Directory, execute:

		python WerewolfServer.py

### Files:

 | **File Name**         | **Description**                                  |
 |-------------------|----------------------------------------------|
 | [Server/WerewolfServer.py](https://github.com/adelgado0723/Werewolf/blob/master/Server/WerewolfServer.py) | - Hosts Werewolf! application                |
 | [Server/Game.py](https://github.com/adelgado0723/Werewolf/blob/master/Server/Game.py) | - Structures and routines for running a game |
 | [Server/Player.py](https://github.com/adelgado0723/Werewolf/blob/master/Server/Player.py) | - Holds variables for client connections     |
	
### Notes:
	
 - To shut off the server, issue a keyboard interrupt (CTL + C).

 - Minimum of 3 players per game. One healer, one sheriff, and one werewolf.
	
 - Maximum of 15 players per game.
	
 - Maximum of 100 connections.
	
 - Compile using *Python2*
	
	
---

## Client:

The client uses the graphical interface provided by the Tkinter library. It
shows a large text area where the player receives messages from the server. At
the bottom is a text input field where the player can chat or issue commands.
To the right, the GUI features an area for displaying the usernames of all
the players in the current game. 

The client connects to the server by clicking on File -> Connect, entering the
host address and port that the server is listening on, and clicking “OK”. Then,
the player is welcomed and asked to provide a unique user name. 

The client program uses multithreading by spawning a thread that continuously
listens for certain events and then handle them appropriately. 

### Usage:

From Client Directory, execute:

		python Main.py

### Files:

 | **File Name**         | **Description**                                           |
 |-------------------|-------------------------------------------------------|
 | [Client/WerewolfClient.py](https://github.com/adelgado0723/Werewolf/blob/master/Client/WerewolfClient.py) | - Client socket wrapper class                         |
 | [Client/Main.py](https://github.com/adelgado0723/Werewolf/blob/master/Client/Main.py) | - Multithreaded GUI client for Werewolf! appplication |
 | [Client/BaseDialog.py](https://github.com/adelgado0723/Werewolf/blob/master/Client/BaseDialog.py) |  -  For Tkinter basic dialog |
 | [Client/BaseEntry.py](https://github.com/adelgado0723/Werewolf/blob/master/Client/BaseEntry.py) |  -  For Tkinter basic dialog |


### Notes:
	
 - A game may only be joined while the game is in the "game lobby". Once the
   game is in progress, connection requests will be rejected.
	
	

