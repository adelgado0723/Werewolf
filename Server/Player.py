class Player:
    def __init__(self, client_socket, player_name='', player_role='player'):
        self._client_socket = client_socket
        self._player_name = player_name
        self._player_role = player_role
        self._status = "Online"


    
    # Player socket for communicating with server
    @property
    def socket(self):
        return self._client_socket

    # Player information
    @property
    def player_name(self):
        return self._player_name

    @property
    def player_role(self):
        return self._player_role

    @property
    def status(self):
        return self._status

    # Setter functions

    @player_name.setter
    def player_name(self, new_player_name):
        self._player_name = new_player_name

    @player_role.setter
    def player_role(self, new_player_role):
        self._player_role = new_player_role

    @status.setter
    def status(self, new_status):
        self._status = new_status
