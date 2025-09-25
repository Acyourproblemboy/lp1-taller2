import asyncio
import websockets
import json
import uuid

PORT = 9000
GAMES = []  # Lista de partidas activas

class Game:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.board = [' '] * 9
        self.players = []  # Lista de sockets (máx 2)
        self.spectators = []
        self.current_turn = 0  # 0 = jugador X, 1 = jugador O
        self.symbols = ['X', 'O']
        self.finished = False

    def get_state(self):
        return {
            "type": "state",
            "game_id": self.id,
            "board": self.board,
            "players": len(self.players),
            "turn": self.symbols[self.current_turn],
            "finished": self.finished
        }

    def is_valid_move(self, pos):
        return 0 <= pos < 9 and self.board[pos] == ' '

    def make_move(self, player_idx, pos):
        if self.finished or self.current_turn != player_idx or not self.is_valid_move(pos):
            return False
        self.board[pos] = self.symbols[player_idx]
        if self.check_winner(self.symbols[player_idx]):
            self.finished = True
        elif ' ' not in self.board:
            self.finished = True  # empate
        else:
            self.current_turn = 1 - self.current_turn
        return True

    def check_winner(self, symbol):
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        return any(all(self.board[i] == symbol for i in pattern) for pattern in win_patterns)

    async def broadcast(self):
        state = json.dumps(self.get_state())
        for player in self.players + self.spectators:
            try:
                await player.send(state)
            except:
                pass  # cliente desconectado


async def handle_client(websocket, path):
    role = None
    game = None

    try:
        async for message in websocket:
            data = json.loads(message)

            if data['type'] == 'join':
                role = data.get('role')
                if role == 'player':
                    # Buscar partida con menos de 2 jugadores
                    game = next((g for g in GAMES if len(g.players) < 2 and not g.finished), None)
                    if not game:
                        game = Game()
                        GAMES.append(game)
                    game.players.append(websocket)
                    player_idx = len(game.players) - 1
                    await websocket.send(json.dumps({
                        "type": "joined",
                        "symbol": game.symbols[player_idx],
                        "game_id": game.id
                    }))
                    await game.broadcast()

                elif role == 'spectator':
                    # Espectador elige una partida
                    game_id = data.get('game_id')
                    game = next((g for g in GAMES if g.id == game_id), None)
                    if game:
                        game.spectators.append(websocket)
                        await websocket.send(json.dumps({
                            "type": "joined",
                            "role": "spectator",
                            "game_id": game.id
                        }))
                        await game.broadcast()
                    else:
                        await websocket.send(json.dumps({"type": "error", "message": "Juego no encontrado"}))

            elif data['type'] == 'move':
                pos = data.get('position')
                if game and websocket in game.players:
                    idx = game.players.index(websocket)
                    if game.make_move(idx, pos):
                        await game.broadcast()
                    else:
                        await websocket.send(json.dumps({"type": "error", "message": "Movimiento inválido"}))

    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado")
    finally:
        if game:
            if websocket in game.players:
                game.players.remove(websocket)
            elif websocket in game.spectators:
                game.spectators.remove(websocket)
            await game.broadcast()


start_server = websockets.serve(handle_client, "localhost", PORT)
print(f"Servidor iniciado en ws://localhost:{PORT}")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
