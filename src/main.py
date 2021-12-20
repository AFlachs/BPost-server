from server import Server
from Database import *

PORT = 6666
SEP = "<SEP>"


def main():
    print("Hello")
    # serv = Server()
    # print("Welcome in BPost-Server")
    test = Database("client_db.db")
    test.insert_new_client('jszpirer', '1234')
    test.select_contacts('jszpirer')
    test.add_contact('jszpirer', 'gszpirer')
    test.select_contacts('jszpirer')

if __name__ == '__main__':
    main()
