import socket
import threading
import pickle
import time
import os
import datetime

class Network():
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.running = True
        self.commands = []
        self.connected = False
        self.msg_id = 0
        self.header_size = 10
        self.part_size = 1024
        self.replay = Replay()

    def isConnected(self):
        return self.connected

    def getLatestCommand(self):
        if self.commands:
            return self.commands.pop(0)
        return None

    def close(self):
        self.running = False
        self.s.close()
        self.replay.save()
        os._exit(0)

class Server(Network, threading.Thread):
    def __init__(self, port):
        Network.__init__(self)
        threading.Thread.__init__(self)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(("", port))
        self.s.listen(1)

    def run(self):
        self.conn, addr = self.s.accept()  # this blocks
        print("connected to: " + str(addr))
        self.connected = True
        while self.running:
            self.receiveData()

    def receiveData(self):
        length = int(self.conn.recv(self.header_size).decode('utf-8'))

        data = b''
        while len(data) != length:
            part = self.conn.recv(min(self.part_size, length - len(data)))
            data += part
        data = pickle.loads(data)
        self.replay.addEvent(data, 2)
        self.commands.append(data)
        print(self.commands)

    def send(self, data):
        self.replay.addEvent(data, 1)
        data["ID"] = self.msg_id
        self.msg_id += 1
        data = pickle.dumps(data)
        data = bytes(f"{len(data):<{self.header_size}}", 'utf-8') + data
        self.conn.send(data)


class Client(Network, threading.Thread):
    def __init__(self, ip, port):
        Network.__init__(self)
        threading.Thread.__init__(self)
        self.connectToServer(ip, port)

    def connectToServer(self, ip, port):
        print("attemptting to connect to: " + str(ip) + " on port " + str(port))
        while self.s.connect_ex((ip, port)) != 0:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connection failed, retrying...")
            time.sleep(1)
        self.connected = True
        print("Connected to: " + str(ip) + ":" + str(port))

    def run(self):
        while self.running:
            self.receiveData()

    def receiveData(self):
        length = int(self.s.recv(self.header_size).decode('utf-8'))

        data = b''
        while len(data) != length:
            part = self.s.recv(min(self.part_size, length - len(data)))
            data += part
        data = pickle.loads(data)
        self.replay.addEvent(data, 2)
        self.commands.append(data)
        print(self.commands)

    def send(self, data):
        self.replay.addEvent(data, 1)
        data["ID"] = self.msg_id
        self.msg_id += 1
        data = pickle.dumps(data)
        data = bytes(f"{len(data):<{self.header_size}}", 'utf-8') + data
        self.s.send(data)

class Replay():
    def __init__(self):
        self.commands = []
        self.timestamp = datetime.datetime.now().strftime("%Y%b%d-%H%M%S")

    def addEvent(self, event, player_num):
        event["PLAYER"] = player_num
        self.commands.append(event)

    def save(self):
        if not os.path.exists('replays'):
            os.makedirs('replays')
        f = open("replays/" + self.timestamp + ".replay", "wb")
        print("saving replay...", end='')
        pickle.dump(self.commands, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.close()
        print("done!")

    def loadReplay(self, replay_file):
        with open(replay_file, 'rb') as f:
            replay_events = pickle.load(f)
        return replay_events
