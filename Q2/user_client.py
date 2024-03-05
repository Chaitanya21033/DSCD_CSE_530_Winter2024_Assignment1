import zmq
import json
import uuid

class UserClient:
    def __init__(self, message_server_address):
        '''
        User client for the group chat application.
        '''
        self.user_id = str(uuid.uuid4())
        self.context = zmq.Context()
        self.message_server_address = message_server_address
        self.group_sockets = {}
        self.group_addresses = {}

    def get_groups(self):
        '''
        Get the list of available groups from the message server.
        '''
        socket = self.context.socket(zmq.REQ)
        socket.connect(self.message_server_address)
        socket.send_json({"action": "get_groups"})
        groups = socket.recv_json()
        print("Available groups:")
        for group_id, address in groups.items():
            self.group_addresses[group_id] = address
            print(f"  {group_id} - {address}")
        return groups

    def join_group(self, group_id):
        '''
        Join a group.
        '''
        if group_id not in self.group_addresses:
            print(f"Group {group_id} does not exist.")
        elif group_id not in self.group_sockets:
            socket = self.context.socket(zmq.REQ)
            socket.connect(self.group_addresses[group_id])
            socket.send_json({"action": "join", "user_id": self.user_id})
            response = socket.recv_json()
            print(f"Response to joining group {group_id}: {response['response']}")
            if response['response'] == "SUCCESS":
                self.group_sockets[group_id] = socket
        else:
            print(f"Group {group_id} already joined.")

    def leave_group(self, group_id):
        '''
        Leave a group.
        '''
        if group_id in self.group_sockets:
            socket = self.group_sockets[group_id]
            socket.send_json({"action": "leave", "user_id": self.user_id})
            response = socket.recv_json()
            print(f"Response to leaving group {group_id}: {response['response']}")
            del self.group_sockets[group_id]

    def send_message(self, group_id, message):
        '''
        Send a message to a group.
        '''        
        if group_id in self.group_sockets:
            # Check if the user is part of the group
            socket = self.group_sockets[group_id]
            socket.send_json({"action": "send_message", "user_id": self.user_id, "message": message})
            response = socket.recv_json()
            print(f"Response to sending message to group {group_id}: {response['response']}")
        else:
            # User is not part of the group, print a failed message
            print(f"Failed to send message: You are not a member of group {group_id}")


    def get_messages(self, group_id, timestamp=0):
        '''
        Get messages from a group.
        '''
        if group_id in self.group_sockets:
            socket = self.group_sockets[group_id]
            socket.send_json({"action": "get_messages", "user_id": self.user_id, "timestamp": timestamp})
            response = socket.recv_json()
            print(f"Messages from group {group_id}: {response['response']}")

    def user_interface(self):
        '''
        User interface for the group chat application.
        '''
        while True:
            print("\nMenu:")
            print("1. Get list of groups")
            print("2. Join a group")
            print("3. Leave a group")
            print("4. Send a message")
            print("5. Get messages")
            print("6. Exit")
            choice = input("Enter your choice: ")

            if choice == '1': # Get list of groups
                self.get_groups()
            elif choice == '2': # Join a group
                group_id = input("Enter group ID to join: ")
                self.join_group(group_id)
            elif choice == '3': # Leave a group
                group_id = input("Enter group ID to leave: ")
                self.leave_group(group_id)
            elif choice == '4': # Send a message
                group_id = input("Enter group ID to send message: ")
                message = input("Enter your message: ")
                self.send_message(group_id, message)
            elif choice == '5': # Get messages
                group_id = input("Enter group ID to get messages from: ")
                timestamp = input("Enter timestamp (leave empty for all messages): ")
                timestamp = float(timestamp) if timestamp else 0
                self.get_messages(group_id, timestamp)
            elif choice == '6':
                print("Exiting the application.")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    '''
    Start the user client.
    '''
    client = UserClient("tcp://10.190.0.2:5555")
    client.user_interface()