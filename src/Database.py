import sqlite3
from sqlite3 import Error


class Database:
    location = None
    connection = None
    cursor = None

    def __init__(self, location):
        self.location = location
        self.create_table()

    def open_connection(self):
        """Creates the connection with the database if the database does not already exist."""
        try:
            self.connection = sqlite3.connect(self.location)
            self.cursor = self.connection.cursor()
        except Error as e:
            print(e)


    def close_connection(self):
        self.cursor.close()
        self.connection.close()


    def create_table(self):
        """Creates the table containing usernames, passwords (and contacts?)."""
        self.open_connection()
        sql_request = """CREATE TABLE IF NOT EXISTS clients(
                                username text PRIMARY KEY,
                                password text NOT NULL,
                                contacts text NOT NULL);"""
        try:
            self.cursor.execute(sql_request)
        except Error as e:
            print(e)
        self.connection.commit()

    def insert_new_client(self, username, password):
        """Insert a new client in the database if he/she is not already in it."""
        if self.client_in_database(username):
            print("The client already exists.")
            return False
        else:
            print("Client doesn't exist so we're gonna add it.")
            sql_insert_client = """INSERT INTO clients VALUES('"""+username+"""','"""+password+"""','');"""
            # The connection is established in the client_in_database function.
            self.cursor.execute(sql_insert_client)
            self.connection.commit()
            return True

    def client_in_database(self, username):
        """Check if a client is already in the database."""
        sql_select = """SELECT * FROM clients WHERE username = '"""+username+"""';"""
        self.cursor.execute(sql_select)
        data = self.cursor.fetchall()
        if len(data) == 0:
            print('There is no client named %s.' % username)
            return False
        else:
            print('Client %s found.' % username)
            return True

    def add_contact(self, username, contact_to_add):
        """Add a new contact to the client with username."""
        current_contacts = self.select_contacts(username)
        if current_contacts == "":
            new_contacts = contact_to_add
        else:
            new_contacts = current_contacts + "," + contact_to_add
        sql_insert_contact = """UPDATE clients 
                            SET contacts = ?
                            WHERE username = ?;"""
        self.cursor.execute(sql_insert_contact, (new_contacts, username))
        self.connection.commit()

    def select_contacts(self, username):
        """Returns the current contacts of client with username."""
        data = ""
        if self.client_in_database(username):
            self.cursor.execute("SELECT contacts FROM clients WHERE username =?;", (username,))
            data = self.cursor.fetchall()
        return data[0][0]
