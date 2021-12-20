import websockets
import websockets.exceptions
import asyncio
import ssl
import pathlib


class Server:
    def __init__(self):
        async def client_handler(websocket: websockets.WebSocketServerProtocol, path):
            """
            Manage a connection to the server from a client.
            """
            self.clients.add(websocket)
            try:
                async for message in websocket:  # Getting messages from the client
                    print("Message from client : \n", message)
                    # manage_message()
                    await websocket.send("Message reçu")
            except websockets.exceptions.ConnectionClosed as e:
                print("Client", websocket, " has disconnected")
                print(e)
            finally:
                self.clients.remove(websocket)
                print("Connection closed")

        self.clients = set()
        self.messages_to_read = list()
        self.messages_to_send = list()

        # TLS configuration (called ssl but is TLS)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        localhost_priv = pathlib.Path(__file__).with_name("keys") / "key.pem"
        localhost_cert = pathlib.Path(__file__).with_name("keys") / "cert.pem"
        ssl_context.load_cert_chain(localhost_cert, localhost_priv)

        start_server = websockets.serve(client_handler, "localhost", 8000, ssl=ssl_context)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
