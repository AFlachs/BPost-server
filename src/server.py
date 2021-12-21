import websockets
import websockets.exceptions
import asyncio
import ssl
import pathlib
from ClientMessages_Database import *


class Server:
    def __init__(self, sep):
        async def client_handler(websocket: websockets.WebSocketServerProtocol, path):
            """
            Manage a connection to the server from a client.
            """
            print("Youhou connecté")
            self.clients.add(websocket)
            try:
                async for message in websocket:  # Getting messages from the client
                    print("Message from client : \n", message)
                    self.manage_message(message, websocket)
                    await websocket.send("Message reçu")
            except websockets.exceptions.ConnectionClosed as e:
                print("Client", websocket, " has disconnected")
                print(e)
            finally:
                self.clients.remove(websocket)
                print("Connection closed")

        self.clients = set()
        self.messages_to_read = list()
        self.messages_to_send = dict()
        self.usernameWebsocket = dict()

        self.database = ClientMessages_Database("database.db")
        self.sep = sep

        # TLS configuration (called ssl but is TLS)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        localhost_priv = pathlib.Path(__file__).with_name("keys") / "key.pem"
        localhost_cert = pathlib.Path(__file__).with_name("keys") / "cert.pem"
        ssl_context.load_cert_chain(localhost_cert, localhost_priv)
        start_server = websockets.serve(client_handler, "localhost", 8000, ssl=ssl_context)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def manage_message(self, message, websocket):
        """Switch cases on the message that the server just received to know what to do with it."""
        split_message = message.split(self.sep)
        nb_instruction = split_message[0]
        if nb_instruction == 0:
            """A client wants to send a message to another client."""
            self.try_to_send_message(split_message)
        elif nb_instruction == 1:
            """A client wants to login."""
            self.try_to_login(split_message, websocket)
        elif nb_instruction == 2:
            """A client wants to create an account."""
            self.try_to_create_account(split_message, websocket)
        elif nb_instruction == 3:
            """A client wants to change his/her password."""
            self.try_to_change_password(split_message)
        elif nb_instruction == 4:
            """A client wants to add a new contact."""
            self.try_to_add_contact(split_message)
        elif nb_instruction == 6:
            """Set the public key after creation of account."""
            self.set_public_key(split_message)
        else:
            """The format is not OK."""
            print("Erreur")
            self.send_error_message("", websocket)

    def try_to_send_message(self, split_message):
        """Need to analyze the split_message to check if the second user is in the DB."""
        username1 = split_message[1]
        message = split_message[2]
        username2 = split_message[3]
        if self.database.client_in_database(username2) and self.database.client_in_database(username1):
            """We need to say to user1 that his/her was well sent."""
            print("Message well sent")
            self.send_message("0" + self.sep + "OK" + self.sep + username2, username1)
            """We need to send the message to user2 and save it into the database."""
            print("Sending message to user2")
            self.send_message("5" + self.sep + message + self.sep + username1, username2)
            self.database.insert_new_message(username1, message, username2)
        else:
            """One the clients is not in the database so failure."""
            print("Error in sending")
            self.send_message("0" + self.sep + "Error" + self.sep + username2, username1)

    def try_to_login(self, split_message, websocket):
        """A client is trying to log in the database."""
        username = split_message[1]
        password = split_message[2]
        if self.database.check_password(username, password):
            """The client is logged in, we can add him/her in the dict."""
            self.usernameWebsocket[username] = websocket
            self.checkUnreadMessages(username)
            print("Client logged in.")
            self.send_message("1" + self.sep + "OK", username)
        else:
            """Something went wrong."""
            print("Log in failed.")
            self.send_error_message("1" + self.sep + "Error", websocket)

    def try_to_create_account(self, split_message, websocket):
        """A new client is trying to create an account."""
        username = split_message[1]
        password = split_message[2]
        if self.database.insert_new_client(username, password):
            """The new client is in the database, we can add him/her in the dict."""
            self.usernameWebsocket[username] = websocket
            print("New client in the db.")
            self.send_message("2" + self.sep + "OK", username)
        else:
            print("Creation of account failed")
            self.send_error_message("2" + self.sep + "Error", websocket)

    def try_to_change_password(self, split_message):
        """A client is trying to change his/her password."""
        username = split_message[1]
        current_password = split_message[2]
        new_password = split_message[3]
        if self.database.modify_password(username, current_password, new_password):
            print("The password has been changed.")
            self.send_message("3" + self.sep + "OK", username)
        else:
            print("Changing password has failed.")
            self.send_message("3" + self.sep + "Error", username)

    def try_to_add_contact(self, split_message):
        """A client is trying to add a new contact to his/her list."""
        username = split_message[1]
        contact = split_message[2]
        if self.database.add_contact(username, contact):
            """A new contact has been added."""
            print("New contact in list.")
            public_key_new_contact = self.database.select_public_key(contact)
            self.send_message("4" + self.sep + "OK" + self.sep + public_key_new_contact, username)
        else:
            print("New contact not added.")
            self.send_message("4" + self.sep + "Error", username)

    def set_public_key(self, split_message):
        """A client is trying to set his/her public key."""
        username = split_message[1]
        public_key = split_message[2]
        self.database.set_public_key(username, public_key)
        print("Public key set up.")

    async def send_message(self, message, username):
        """Function that will send a message to a user."""
        # We have two possibilities : the user is connected or not. We can check the dict to see that.
        if username in self.usernameWebsocket:
            # The user is connected, we can take his/her websocket.
            ws = self.usernameWebsocket[username]
            await ws.send(message)
        else:
            # We need to add the message to the messages_to_send list.
            if username in self.messages_to_send:
                self.messages_to_send[username].append(message)
            else:
                self.messages_to_send[username] = [message]

    async def send_error_message(self, message, websocket):
        """Allows the server to send an error message to a client that's not logged in (username and websocket
        are not associated)."""
        await websocket.send(message)

    def checkUnreadMessages(self, username):
        """When a user logs in, we need to check if he/she has unread messages"""
        unreadMessages = self.messages_to_send[username]  # This is a list.
        for message in unreadMessages:
            self.send_message(message, username)
        self.messages_to_send[username] = []
