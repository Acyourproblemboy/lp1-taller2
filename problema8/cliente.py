import asyncio
import websockets
import json

async def play():
    uri = "ws://localhost:9000"
    async with websockets.connect(uri) as websocket:
        role = input("¿Eres jugador o espectador? (player/spectator): ")
        join_msg = {"type": "join", "role": role}
        if role == "spectator":
            join_msg["game_id"] = input("ID del juego: ")

        await websocket.send(json.dumps(join_msg))

        async def receive():
            async for msg in websocket:
                data = json.loads(msg)
                print("📩 Evento:", data)

        async def send_moves():
            while True:
                pos = int(input("Posición (0-8): "))
                await websocket.send(json.dumps({"type": "move", "position": pos}))

        await asyncio.gather(receive(), send_moves())

asyncio.run(play())
