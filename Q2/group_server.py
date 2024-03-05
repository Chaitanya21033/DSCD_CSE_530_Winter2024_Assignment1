import zmq
import json
import time

class GroupServer:
    def __init__(self, group_id, message_server_address, message_server_ip_addr):
        '''
        A server for a group chat.    
        '''
        self.group_id = group_id
        self.users = set()  # Set of user UUIDs
        self.messages = []  # List of messages (dicts with 'user_id', 'timestamp', 'message')
        self.context = zmq.Context()
        self.message_server_address = message_server_address
        self.message_server_ip_addr = message_server_ip_addr
        self.register_with_message_server()

    def register_with_message_server(self):
        '''
        Register the group server with the message server.
        '''
        print(f"[GroupServer {self.group_id}] Registering with the message server.")
        socket = self.context.socket(zmq.REQ)
        socket.connect(self.message_server_address)
        socket.send_json({"action": "register", "group_id": self.group_id, "address": f"tcp://10.190.0.3:{self.group_id}"})
        response = socket.recv_json()
        print(f"[GroupServer {self.group_id}] Registration response: {response}")

    def handle_join(self, user_id):
        '''
        Add a user to the group.
        '''
        if user_id not in self.users:
            self.users.add(user_id)
            print(f"[GroupServer {self.group_id}] User {user_id} joined.")
            return "SUCCESS"
        else:
            return "USER ALREADY IN GROUP"

    def handle_leave(self, user_id):
        '''
        Remove a user from the group.
        '''
        if user_id in self.users:
            self.users.remove(user_id)
            print(f"[GroupServer {self.group_id}] User {user_id} left.")
            return "SUCCESS"
        else:
            return "USER NOT IN GROUP"

    def handle_send_message(self, user_id, message):
        '''
        Add a message to the group.
        '''
        if user_id in self.users:
            timestamp = time.time()
            self.messages.append({"user_id": user_id, "timestamp": timestamp, "message": message})
            print(f"[GroupServer {self.group_id}] Message received from user {user_id}.")
            return "SUCCESS"
        else:
            return "USER NOT IN GROUP"

    def handle_get_messages(self, user_id, timestamp=0):
        '''
        Send all messages since a given timestamp to a user.
        '''
        if user_id in self.users:
            messages_since = [msg for msg in self.messages if msg['timestamp'] >= timestamp]
            print(f"[GroupServer {self.group_id}] Sending messages to user {user_id} since timestamp {timestamp}.")
            return json.dumps(messages_since)
        else:
            return "USER NOT IN GROUP"

    def start(self):
        '''
        Start the server.
        '''
        print(f"[GroupServer {self.group_id}] Starting server.")
        socket = self.context.socket(zmq.REP)
        socket.bind(f"tcp://*:{self.group_id}")

        while True:
            message = socket.recv_json()
            action = message['action']
            user_id = message['user_id']

            if action == 'join':
                response = self.handle_join(user_id)
            elif action == 'leave':
                response = self.handle_leave(user_id)
            elif action == 'send_message':
                response = self.handle_send_message(user_id, message['message'])
            elif action == 'get_messages':
                timestamp = message.get('timestamp', 0)
                response = self.handle_get_messages(user_id, timestamp)
            else:
                response = "INVALID ACTION"
                print(f"[GroupServer {self.group_id}] Received invalid action: {action}")

            socket.send_json({"response": response})

def main(self_port):
    ip_addr = "10.190.0.2" #input("Enter Message Server IP Address: ")
    group_server = GroupServer(self_port, f"tcp://{ip_addr}:5555", ip_addr)
    group_server.start()