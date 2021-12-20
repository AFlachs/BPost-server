import websockets
import websockets.exceptions
import asyncio
from ClientMessages_Database import *


class Server:
    def __init__(self, sep):
        self.clients = set()
        self.database = ClientMessages_Database("database.db")
        self.sep = sep

        async def client_handler(websocket, path):
            """
            Manage a connection to the server from a client.
            """
            print("Youhou connecté")
            self.clients.add(websocket)
            try:
                async for message in websocket:  # Getting messages from the client
                    print("Message from client : \n", message)
                    self.manage_message(message)
            except websockets.exceptions.ConnectionClosed as e:
                print("Client", websocket, " has disconnected")
                print(e)
            finally:
                self.clients.remove(websocket)

        start_server = websockets.serve(client_handler, "localhost", 8000)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def manage_message(self, message):
        """Switch cases on the message that the server just received to know what to do with it."""
        split_message = message.split(self.sep)
        nb_instruction = split_message[0]
        if nb_instruction == 0:
            """A client wants to send a message to another client."""
            self.try_to_send_message(split_message)
        elif nb_instruction == 1:
            """A client wants to login."""
            self.try_to_login(split_message)
        elif nb_instruction == 2:
            """A client wants to create an account."""
            self.try_to_create_account(split_message)
        elif nb_instruction == 3:
            """A client wants to change his/her password."""
            self.try_to_change_password(split_message)
        elif nb_instruction == 4:
            """A client wants to add a new contact."""
            self.try_to_add_contact(split_message)
        else:
            """The format is not OK."""
            print("Erreur")
            # self.send_message("")

    def try_to_send_message(self, split_message):
        """Need to analyze the split_message to check if the second user is in the DB."""
        username1 = split_message[1]
        message = split_message[2]
        username2 = split_message[3]
        if self.database.client_in_database(username2) and self.database.client_in_database(username1):
            """We need to say to user1 that his/her was well sent."""
            print("Message well sent")
            # self.send_message("0"+self.sep+"WellSent"+self.sep+username2,username1)
            """We need to send the message to user2 and save it into the database."""
            print("Sending message to user2")
            # self.send_message("5"+self.sep+message+self.sep+username1, username2)
            self.database.insert_new_message(username1, message, username2)
        else:
            """One the clients is not in the database so failure."""
            print("Error in sending")
            # self.send_message("0"+self.sep+"Error"+self.sep+username2, username1)

    def try_to_login(self, split_message):
        """A client is trying to log in the database."""
        username = split_message[1]
        password = split_message[2]
        if self.database.check_password(username, password):
            """The client is logged in."""
            print("Client logged in.")
            # self.send_message("1"+self.sep+"AuthOK",username)
        else:
            """Something went wrong."""
            print("Log in failed.")
            # self.send_message("1"+self.sep+"Error", username)

    def try_to_create_account(self, split_message):
        """A new client is trying to create an account."""
        username = split_message[1]
        password = split_message[2]
        if self.database.insert_new_client(username, password):
            """The new client is in the database."""
            print("New client in the db.")
            # self.send_message("2"+self.sep+"AccOK", username)
        else :
            print("Creation of account failed")
            # Il faut envoyer un message d'erreur mais on n'a pas de username identifié dans la db...

    def try_to_change_password(self, split_message):
        """A client is trying to change his/her password."""
        username = split_message[1]
        current_password = split_message[2]
        new_password = split_message[3]
        if self.database.modify_password(username, current_password, new_password):
            print("The password has been changed.")
            # self.send_message("3"+self.sep+"PassOK", username)
        else :
            print("Changing password has failed.")
            # self.send_message("3"+self.sep+"Error", username)

    def try_to_add_contact(self, split_message):
        """A client is trying to add a new contact to his/her list."""
        username = split_message[1]
        contact = split_message[2]
        if self.database.add_contact(username, contact):
            """A new contact has been added."""
            print("New contact in list.")
            # self.send_message("4"+self.sep+"ContOK", username)
        else:
            print("New contact not added.")
            # self.send_message("4"+self.sep+"Error", username)