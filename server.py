#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def send_history(self):
         for message in self.server.history[-10::]:
            print(message)
            self.transport.write(message.encode())

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()
        count = 0

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login_test = decoded.replace("login:", "").replace("\r\n", "")
                for user in self.server.clients:
                    if user.login == login_test:
                        count = count + 1
                if count > 0:
                    self.transport.write(f"Логин {login_test} занят, попробуйте другой".encode())
                    self.transport.close()
                else:
                    self.login = login_test
                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
