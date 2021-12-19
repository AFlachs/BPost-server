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
        """Closes all the connections."""
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
        self.close_connection()

    def insert_new_client(self, username, password):
        """Insert a new client in the database if he/she is not already in it."""
        self.open_connection()
        if self.client_in_database(username):
            print("The client already exists.")
            self.close_connection()
            return False
        else:
            print("Client doesn't exist so we're gonna add it.")
            sql_insert_client = """INSERT INTO clients VALUES('""" + username + """','""" + password + """','');"""
            # The connection is established in the client_in_database function.
            self.cursor.execute(sql_insert_client)
            self.connection.commit()
            self.close_connection()
            return True

    def client_in_database(self, username):
        # ATTENTION : Don't use this function outside of the database class.
        """Check if a client is already in the database."""
        self.open_connection()
        sql_select = """SELECT * FROM clients WHERE username = '""" + username + """';"""
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
        list_of_contacts = self.split_contacts(current_contacts)
        if self.contact_already_registered(contact_to_add, list_of_contacts):
            print("The new contact already is in the list.")
            return
        self.open_connection()
        if list_of_contacts[0] == "":
            new_contacts = contact_to_add
        else:
            new_contacts = current_contacts + "," + contact_to_add
        sql_insert_contact = """UPDATE clients 
                            SET contacts = ?
                            WHERE username = ?;"""
        self.cursor.execute(sql_insert_contact, (new_contacts, username))
        self.connection.commit()
        self.close_connection()

    def select_contacts(self, username):
        """Returns the current contacts of client with username."""
        self.open_connection()
        data = ""
        if self.client_in_database(username):
            self.cursor.execute("SELECT contacts FROM clients WHERE username =?;", (username,))
            data = self.cursor.fetchall()
        self.close_connection()
        return data[0][0]

    def split_contacts(self, current_contacts):
        list_of_contacts = current_contacts.split(",")
        print(list_of_contacts)
        return list_of_contacts

    def contact_already_registered(self, new_contacts, list_of_contacts):
        return new_contacts in list_of_contacts
