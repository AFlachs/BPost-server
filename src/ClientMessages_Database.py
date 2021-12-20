import sqlite3
from sqlite3 import Error


class ClientMessages_Database:
    location = None
    connection = None
    cursor = None

    def __init__(self, location):
        self.location = location
        self.__create_table()

    def __open_connection(self):
        """Creates the connection with the database if the database does not already exist."""
        try:
            self.connection = sqlite3.connect(self.location)
            self.cursor = self.connection.cursor()
        except Error as e:
            print(e)

    def __close_connection(self):
        """Closes all the connections."""
        self.cursor.close()
        self.connection.close()

    def __create_table(self):
        """Creates the table containing usernames, passwords (and contacts?)."""
        self.__open_connection()
        sql_request = """CREATE TABLE IF NOT EXISTS clients(
                                username text PRIMARY KEY,
                                password text NOT NULL,
                                contacts text NOT NULL);"""
        try:
            self.cursor.execute(sql_request)
        except Error as e:
            print(e)
        sql_request = """CREATE TABLE IF NOT EXISTS messages(
                                        timestamp text PRIMARY KEY,
                                        username1 text NOT NULL,
                                        message text NOT NULL,
                                        username2 text NOT NULL);"""
        try:
            self.cursor.execute(sql_request)
        except Error as e:
            print(e)
        self.connection.commit()
        self.__close_connection()

    def insert_new_client(self, username, password):
        """Insert a new client in the database if he/she is not already in it."""
        if password == "":
            print("The password can't be empty.")
            return False
        if self.client_in_database(username):
            print("The client already exists.")
            return False
        else:
            print("Client doesn't exist so we're gonna add it.")
            self.__open_connection()
            sql_insert_client = """INSERT INTO clients VALUES('""" + username + """','""" + password + """','');"""
            self.cursor.execute(sql_insert_client)
            self.connection.commit()
            self.__close_connection()
            return True

    def client_in_database(self, username):
        """Check if a client is already in the database."""
        self.__open_connection()
        sql_select = """SELECT * FROM clients WHERE username = '""" + username + """';"""
        self.cursor.execute(sql_select)
        data = self.cursor.fetchall()
        self.__close_connection()
        if len(data) == 0:
            print('There is no client named %s.' % username)
            return False
        else:
            print('Client %s found.' % username)
            return True

    def add_contact(self, username, contact_to_add):
        """Add a new contact to the client with username."""
        current_contacts = self.select_contacts(username)
        list_of_contacts = self.__split_contacts(current_contacts)
        if self.__contact_already_registered(contact_to_add, list_of_contacts):
            print("The new contact already is in the list.")
            return
        if self.client_in_database(contact_to_add):
            self.__open_connection()
            if list_of_contacts[0] == "":
                new_contacts = contact_to_add
            else:
                new_contacts = current_contacts + "," + contact_to_add
            sql_insert_contact = """UPDATE clients 
                                SET contacts = ?
                                WHERE username = ?;"""
            self.cursor.execute(sql_insert_contact, (new_contacts, username))
            self.connection.commit()
            self.__close_connection()
        else:
            print("The contact is not a client in our database.")
            return

    def select_contacts(self, username):
        """Returns the current contacts of client with username."""
        data = ""
        if self.client_in_database(username):
            self.__open_connection()
            self.cursor.execute("SELECT contacts FROM clients WHERE username =?;", (username,))
            data = self.cursor.fetchall()
            self.__close_connection()
        return data[0][0]

    def select_password(self, username):
        """Returns the current password of client with username."""
        data = ""
        if self.client_in_database(username):
            self.__open_connection()
            self.cursor.execute("SELECT password FROM clients WHERE username = ?;", (username,))
            password = self.cursor.fetchall()
            data = password[0][0]
            self.__close_connection()
        return data

    def __split_contacts(self, current_contacts):
        """Makes a list with the string containing all contacts."""
        list_of_contacts = current_contacts.split(",")
        return list_of_contacts

    def __contact_already_registered(self, new_contacts, list_of_contacts):
        """Checks if the contact is already in the contact list of the user."""
        return new_contacts in list_of_contacts

    def check_password(self, username, password):
        """Checks if the password and the username correspond to each other.
        Return false also if the client doesn't exist."""
        password_in_db = self.select_password(username)
        if password_in_db == password:
            return True
        print("The username and/or the password are/is not correct.")
        return False

    def modify_password(self, username, current_password, new_password):
        """Change the current_password to the new_password if the current_password
        corresponds to this in the database."""
        if self.check_password(username, current_password):
            self.__open_connection()
            sql_insert_contact = """UPDATE clients 
                                        SET password = ?
                                        WHERE username = ?;"""
            self.cursor.execute(sql_insert_contact, (new_password, username))
            self.connection.commit()
            self.__close_connection()
            return True
        return False

    def insert_new_message(self, username1, message, username2):
        self.__open_connection()
        sql_insert = """INSERT INTO messages VALUES(datetime('now'),'""" + username1 + """','""" + message \
                     + """','""" + username2 + """');"""
        self.cursor.execute(sql_insert)
        self.connection.commit()
        self.__close_connection()

    def select_and_display_all_messages(self, username):
        self.__open_connection()
        sql_select = """SELECT * FROM messages WHERE username1 = '"""+username+"""';"""
        self.cursor.execute(sql_select)
        data = self.cursor.fetchall()
        for row in data:
            print(row)
