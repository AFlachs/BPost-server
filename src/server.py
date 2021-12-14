import websockets
import asyncio


class Server:
    def __init__(self,):
        async def client_handler(websocket, path):
            """
            Manage a connection to the server from a client.
            :param websocket: URL of the server
            :param path: URI for the handler
            :return:
            """
            await websocket.send("J'suis chauve.")
            data = await websocket.recv()

            reply = f"Data received as:  {data}!"

            await websocket.send(reply)

        start_server = websockets.serve(client_handler, "localhost", 8000)

        asyncio.get_event_loop().run_until_complete(start_server)

        asyncio.get_event_loop().run_forever()

