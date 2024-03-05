import zmq
import json

def main():
    '''
    Start the message server.
    '''
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")  # Bind to a TCP port
    print("Message Server is running on port 5555.")

    groups = {}

    while True:
        try:
            # Wait for a request from a client
            message = socket.recv_json()
            action = message.get('action')

            if action == 'register':
                # Register a new group server
                group_id = message['group_id']
                group_address = message['address']
                groups[group_id] = group_address
                print(f"Registering group '{group_id}' with address '{group_address}'.")
                socket.send_json({"status": "SUCCESS"})
            elif action == 'get_groups':
                # Send the list of groups to a user
                print("Received request for group list. Sending group list.")
                socket.send_json(groups)
            else:
                print(f"Received unknown action: {action}")
                socket.send_json({"status": "ERROR", "message": "Unknown action"})
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
