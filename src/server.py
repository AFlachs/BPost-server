import websockets
import websockets.exceptions
import asyncio
import ssl
import pathlib
from ClientMessages_Database import *


class Server:
    def __init__(self, sep):
        async def client_handler(websocket: websockets.WebSocketServerProtocol):
            """
            Manage a connection to the server from a client.
            """
            self.clients.add(websocket)
            try:
                async for message in websocket:  # Getting messages from the client
                    print("Message from client : \n", message)
                    await self.manage_message(message, websocket)
            except websockets.exceptions.ConnectionClosed as e:
                print("Client", websocket, " has disconnected")
                for connected in self.usernameWebsocket:
                    print(connected)
            finally:
                self.clients.remove(websocket)
                self.usernameWebsocket = {key: val for key, val in self.usernameWebsocket.items() if val != websocket}
                print("Connection closed")


        """Sets and dictionaries of the server.
        Clients : set of the clients that are connected to the server at the moment.
        Messages_to_read : list of messages that the server has to read.
        Messages_to_send : dictionary with key=username and value=list of messages to send to username 
        when he/she connects to the server.
        UsernameWebsocket : dictionary with key=username and value=websocket of the username. It 
        gathers the users that are logged in at the moment."""
        self.clients = set()
        self.messages_to_read = list()
        self.messages_to_send = dict()
        self.usernameWebsocket = dict()

        self.database = ClientMessages_Database(pathlib.Path(__file__).with_name("database.db"))
        self.sep = sep
        """Boolean that checks if the database is used in another coroutine or not."""
        self.database_lock = False

        # TLS configuration (called ssl but is TLS)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        localhost_priv = pathlib.Path(__file__).with_name("keys") / "key.pem"
        localhost_cert = pathlib.Path(__file__).with_name("keys") / "cert.pem"
        ssl_context.load_cert_chain(localhost_cert, localhost_priv)
        start_server = websockets.serve(client_handler, "localhost", 8000, ssl=ssl_context)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def manage_message(self, message, websocket):
        """Switch cases on the message that the server just received to know what to do with it."""
        split_message = message.split(self.sep)
        nb_instruction = int(split_message[0])
        if nb_instruction == 0:
            """A client wants to send a message to another client."""
            await self.try_to_send_message(split_message)
        elif nb_instruction == 1:
            """A client wants to login."""
            await self.try_to_login(split_message, websocket)
        elif nb_instruction == 2:
            """A client wants to create an account."""
            await self.try_to_create_account(split_message, websocket)
        elif nb_instruction == 3:
            """A client wants to change his/her password."""
            await self.try_to_change_password(split_message)
        elif nb_instruction == 4:
            """A client wants to add a new contact."""
            await self.try_to_add_contact(split_message)
        elif nb_instruction == 6:
            """Set the public key after creation of account."""
            await self.set_public_key(split_message)
        else:
            """The format is not OK."""
            print("Erreur")
            await self.send_error_message("", websocket)

    async def try_to_send_message(self, split_message):
        """Need to analyze the split_message to check if the second user is in the DB."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username1 = split_message[1]
        message = split_message[2]
        username2 = split_message[3]
        self.database_lock = True
        if self.database.client_in_database(username2) and self.database.client_in_database(username1):
            self.database_lock = False
            """We need to say to user1 that his/her was well sent."""
            await self.send_message("0" + self.sep + "OK" + self.sep + username2, username1)
            """We need to send the message to user2 and save it into the database."""
            print("Sending message to", username2)
            await self.send_message("5" + self.sep + message + self.sep + username1, username2)
            self.database_lock = True
            self.database.insert_new_message(username1, message, username2)
            self.database_lock = False
        else:
            self.database_lock = False
            """One the clients is not in the database so failure."""
            print("Error in sending")
            await self.send_message("0" + self.sep + "Error" + self.sep + username2, username1)

    async def try_to_login(self, split_message, websocket):
        """A client is trying to log in the database."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username = split_message[1]
        password = split_message[2]
        self.database_lock = True
        if self.database.check_password(username, password):
            self.database_lock = False
            """The client is logged in, we can add him/her in the dict."""
            self.usernameWebsocket[username] = websocket
            await self.checkUnreadMessages(username)
            print("Client logged in.")
            await self.send_message("1" + self.sep + "OK", username)
        else:
            self.database_lock = False
            """Something went wrong."""
            print("Log in failed.")
            await self.send_error_message("1" + self.sep + "Error", websocket)

    async def try_to_create_account(self, split_message, websocket):
        """A new client is trying to create an account."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username = split_message[1]
        password = split_message[2]
        self.database_lock = True
        if self.database.insert_new_client(username, password):
            self.database_lock = False
            """The new client is in the database, we can add him/her in the dict."""
            self.usernameWebsocket[username] = websocket
            print("New client in the db.")
            await self.send_message("2" + self.sep + "OK", username)
        else:
            self.database_lock = False
            print("Creation of account failed")
            await self.send_error_message("2" + self.sep + "Error", websocket)

    async def try_to_change_password(self, split_message):
        """A client is trying to change his/her password."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username = split_message[1]
        current_password = split_message[2]
        new_password = split_message[3]
        self.database_lock = True
        if self.database.modify_password(username, current_password, new_password):
            self.database_lock = False
            print("The password has been changed.")
            await self.send_message("3" + self.sep + "OK", username)
        else:
            self.database_lock = False
            print("Changing password has failed.")
            await self.send_message("3" + self.sep + "Error", username)

    async def try_to_add_contact(self, split_message):
        """A client is trying to add a new contact to his/her list."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username = split_message[1]
        contact = split_message[2]
        self.database_lock = True
        if self.database.add_contact(username, contact):
            self.database_lock = False
            """A new contact has been added."""
            print("New contact in list.")
            self.database_lock = True
            public_key_new_contact = self.database.select_public_key(contact)
            self.database_lock = False
            await self.send_message("4" + self.sep + "OK" + self.sep + public_key_new_contact, username)
        else:
            self.database_lock = False
            print("New contact not added.")
            await self.send_message("4" + self.sep + "Error", username)

    async def set_public_key(self, split_message):
        """A client is trying to set his/her public key."""
        while self.database_lock:
            await asyncio.sleep(0.3)
        username = split_message[1]
        public_key = split_message[2]
        self.database_lock = True
        self.database.set_public_key(username, public_key)
        self.database_lock = False
        print("Public key set up.")

    async def send_message(self, message, username):
        """Function that will send a message to a user."""
        # We have two possibilities : the user is connected or not. We can check the dict to see that.
        if username in self.usernameWebsocket:
            # The user is connected, we can take his/her websocket.
            print("Message sent to user", username)
            ws = self.usernameWebsocket[username]
            await ws.send(message)
        else:
            # We need to add the message to the messages_to_send list.
            print("Message added to 'to send'", username)
            if username in self.messages_to_send:
                self.messages_to_send[username].append(message)
            else:
                self.messages_to_send[username] = [message]

    async def send_error_message(self, message, websocket):
        """Allows the server to send an error message to a client that's not logged in (username and websocket
        are not associated)."""
        print("Sending error message")
        await websocket.send(message)

    async def checkUnreadMessages(self, username):
        """When a user logs in, we need to check if he/she has unread messages"""
        if username in self.messages_to_send:
            unreadMessages = self.messages_to_send[username]  # This is a list.
            for message in unreadMessages:
                await self.send_message(message, username)
            self.messages_to_send[username] = []
