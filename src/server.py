import websockets
import websockets.exceptions
import asyncio


class Server:
    def __init__(self,):
        self.clients = set()

        async def client_handler(websocket, path):
            """
            Manage a connection to the server from a client.
            """
            print("Youhou connecté")
            self.clients.add(websocket)
            try:
                async for message in websocket:  # Getting messages from the client
                    print("Message from client : \n", message)
                    # manage_message()
            except websockets.exceptions.ConnectionClosed as e:
                print("Client", websocket, " has disconnected")
                print(e)
            finally:
                self.clients.remove(websocket)

        start_server = websockets.serve(client_handler, "localhost", 8000)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
