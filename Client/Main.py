import time
import tkinter as tk
from tkinter import messagebox
import WerewolfClient as client
import BaseDialog as dialog
import BaseEntry as entry
import threading

class SocketThreadedTask(threading.Thread):
    def __init__(self, socket, **callbacks):
        threading.Thread.__init__(self)
        self.socket = socket
        self.callbacks = callbacks

    def run(self):
        while True:
            try:
                message = self.socket.receive()

                if message == '/quit':
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> You have been disconnected from the server.\n')
                    self.socket.disconnect()
                    break
                elif message == '/clear':
                    self.callbacks['clear_chat_window']()
                    break

                elif message == '/squit':
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> The server was forcibly shutdown. No further messages are able to be sent\n')
                    self.socket.disconnect()
                    break
                elif 'joined' in message:
                    split_message = message.split('|')
                    if split_message[0].split(' ')[1] == 'You':
                        self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window'](split_message[0])
                    self.callbacks['update_user_list'](split_message[1])


                elif 'left game' in message:
                   self.callbacks['update_chat_window'](message)
                   self.callbacks['remove_user_from_list'](message.split(' ')[2])
                else:
                    self.callbacks['update_chat_window'](message)
            except OSError:
                break

class ChatDialog(dialog.BaseDialog):
    def body(self, master):
        tk.Label(master, text="Enter host:").grid(row=0, sticky="w")
        tk.Label(master, text="Enter port:").grid(row=1, sticky="w")

        self.hostEntryField = entry.BaseEntry(master, placeholder="Enter host")
        self.portEntryField = entry.BaseEntry(master, placeholder="Enter port")

        self.hostEntryField.grid(row=0, column=1)
        self.portEntryField.grid(row=1, column=1)
        return self.hostEntryField

    def validate(self):
        host = str(self.hostEntryField.get())

        try:
            port = int(self.portEntryField.get())

            if(port >= 0 and port < 65536):
                self.result = (host, port)
                return True
            else:
                tk.messagebox.showwarning("Error", "The port number has to be between 0 and 65535. Both values are inclusive.")
                return False
        except ValueError:
            tk.messagebox.showwarning("Error", "The port number has to be an integer.")
            return False


class SplashScreen(tk.Frame):
    def __init__(self, parent, controller):
        # tk.Frame.__init__(self, master)
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # self.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
       
        # controller.config(bg="#3366ff")

        m = tk.Label(self, text="This is a test of the splash screen\n\n")
        m.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # m.config(bg="#3366ff", justify=tk.CENTER, font=("calibri", 29))
    
        # tk.Button(self, text="Press this button to kill the program", bg='red', command=root.destroy).pack(side=tk.BOTTOM, fill=tk.X)
    

        label = tk.Label(self, text="Splash Screen", font=("Verdana", 12))
        label.grid(row=2, column=0, columnspan=2, sticky="nsew")

        button = tk.Button(self, text="Visit Page 1",
        command=lambda: controller.show_frame(ChatGUI))
        button.grid(row=4, column=0, columnspan=2, sticky="nsew")

class RunClient(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)


        container = tk.Frame(self)
        
        self.title("Werewolf!")
        # get screen width and height
        '''
        screenSizeX = self.winfo_screenwidth()
        screenSizeY = self.winfo_screenheight()

        frameSizeX = 800
        frameSizeY = 400

        framePosX = (screenSizeX - frameSizeX) / 2
        framePosY = (screenSizeY - frameSizeY) / 2

        self.geometry('%dx%d+%d+%d' % (frameSizeX, frameSizeY, framePosX, framePosY))
        self.resizable(True, True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        '''

        # container.pack(side="top", fill="both", expand=True)
        # container.grid_rowconfigure(0, weight=1)
        # container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        '''
        for F in (SplashScreen, ChatGUI):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")
        '''
        frame = SplashScreen(container, self)
        frame.grid(row=0, column=0, sticky="nsew")

        frame.tkraise()
       # self.show_frame(SplashScreen)

        #time.sleep(6)
        #self.show_frame(ChatGUI)


    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

class ChatGUI(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        '''
        # Added for loading screen
        parent.withdraw()
        splash = Splash(parent)
        # Simulating Loading Delay
        time.sleep(6)
    
        splash.destroy()
        parent.deiconify()
    
        # End of modification
        '''

        self.initUI(controller)
        self.clientSocket = client.Client()

        self.bind_widgets(self.clientSocket.send)
 
        controller.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initUI(self, parent):
        self.parent = parent

        self.mainMenu = tk.Menu(self.parent)
        self.parent.config(menu=self.mainMenu)

        self.subMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label='File', menu=self.subMenu)
        self.subMenu.add_command(label='Connect', command=self.connect_to_server)
        self.subMenu.add_command(label='Exit', command=self.on_closing)
        
        
        # Code moved here from Chat Window
        self.messageTextArea = tk.Text(parent, bg="white smoke", state=tk.DISABLED, wrap=tk.WORD)
        self.messageTextArea.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.messageScrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=self.messageTextArea.yview)
        self.messageScrollbar.grid(row=0, column=3, sticky="ns")

        self.messageTextArea['yscrollcommand'] = self.messageScrollbar.set

        self.usersListBox = tk.Listbox(parent, bg="gray80")
        self.usersListBox.grid(row=0, column=4, padx=5, sticky="nsew")

        self.entryField = entry.BaseEntry(parent, placeholder="Enter message.", width=80)
        self.entryField.grid(row=1, column=0, padx=5, pady=10, sticky="we")

        self.send_message_button = tk.Button(parent, text="Send", width=10, bg="#CACACA", activebackground="#CACACA")
        self.send_message_button.grid(row=1, column=1, padx=5, sticky="we")

    def connect_to_server(self):
        if self.clientSocket.isClientConnected:
            tk.messagebox.showwarning("Info", "Already connected to the server.")
            return

        dialogResult = ChatDialog(self.parent).result

        if dialogResult:
            self.clientSocket.connect(dialogResult[0], dialogResult[1])

            if self.clientSocket.isClientConnected:
                self.clear_chat_window()
                SocketThreadedTask(self.clientSocket, update_chat_window=self.update_chat_window,
                                                      update_user_list=self.update_user_list,
                                                      clear_chat_window=self.clear_chat_window,
                                                      remove_user_from_list=self.remove_user_from_list,).start()
            else:
                tk.messagebox.showwarning("Error", "Unable to connect to the server.")

    def on_closing(self):
        if self.clientSocket.isClientConnected:
            self.clientSocket.send('/quit')

        self.parent.quit()
        self.parent.destroy()

    # Code moved here from Chat Window         
    def update_chat_window(self, message):
        self.messageTextArea.configure(state='normal')
        self.messageTextArea.insert(tk.END, message)
        # Autoscroll
        self.messageTextArea.yview(tk.END)
        self.messageTextArea.configure(state='disabled')
       
    def update_user_list(self, user_message):
        users = user_message.split(' ')

        for user in users:
            if user not in self.usersListBox.get(0, tk.END):
                self.usersListBox.insert(tk.END, user)


        
    def remove_user_from_list(self, user):
        print(user)
        index = self.usersListBox.get(0, tk.END).index(user)
        self.usersListBox.delete(index)

    def clear_chat_window(self):
        if not self.messageTextArea.compare("end-1c", "==", "1.0"):
            self.messageTextArea.configure(state='normal')
            self.messageTextArea.delete('1.0', tk.END)
            self.messageTextArea.configure(state='disabled')

        if self.usersListBox.size() > 0:
            self.usersListBox.delete(0, tk.END)

    def send_message(self, **callbacks):
        message = self.entryField.get()
        self.set_message("")

        callbacks['send_message_to_server'](message)

    def set_message(self, message):
        self.entryField.delete(0, tk.END)
        self.entryField.insert(0, message)

    def bind_widgets(self, callback):
        self.send_message_button['command'] = lambda sendCallback = callback : self.send_message(send_message_to_server=sendCallback)
        self.entryField.bind("<Return>", lambda event, sendCallback = callback : self.send_message(send_message_to_server=sendCallback))
        self.messageTextArea.bind("<1>", lambda event: self.messageTextArea.focus_set())


   
if __name__ == "__main__":
    # root = tk.Tk()
    # sp = SplashScreen(root)
    # chatGUI = ChatGUI(root)
    app = RunClient() 
    app.mainloop()
