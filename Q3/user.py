import pika
import json
import sys
import threading

server_ip_addr = "10.190.0.2"

def listen_for_notifications(user):
    """
    Listens for notifications on a user-specific queue.
    """
    credentials = pika.PlainCredentials('admin1', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(server_ip_addr, credentials=credentials))
    channel = connection.channel()
    
    # Declare a queue for receiving notifications. Queue name is user's name for simplicity.
    channel.queue_declare(queue=user)
    
    def callback(ch, method, properties, body):
        print(f"Notification: {body.decode()}")
    
    channel.basic_consume(queue=user, on_message_callback=callback, auto_ack=True)
    
    print(f"Listening for notifications for {user}...")
    channel.start_consuming()

def send_user_request(user, youtuber=None, action=None):
    """
    Sends a user request to the YouTube server.
    """
    credentials = pika.PlainCredentials('admin1', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(server_ip_addr, credentials=credentials))
    channel = connection.channel()
    
    channel.queue_declare(queue='user_requests')
    
    if action:  # Subscribe/Unsubscribe
        message = json.dumps({
            "user": user,
            "youtuber": youtuber,
            "subscribe": True if action == "s" else False
        })
    else:  # Login
        message = json.dumps({"user": user})
    
    channel.basic_publish(exchange='', routing_key='user_requests', body=message)
    print("Request sent successfully.")
    connection.close()

    # Start listening for notifications in a separate thread after sending login request
    if not action:  # If action is None, it's a login attempt
        notification_thread = threading.Thread(target=listen_for_notifications, args=(user,))
        notification_thread.start()

if __name__ == "__main__":
    if len(sys.argv) not in [2, 4] or sys.argv[1] == "-h":
        print("Usage:")
        print("Login: python3 user.py <username>")
        print("Subscribe/Unsubscribe: python3 user.py <username> <s/u> <YoutuberName>")
        sys.exit(1)
    
    username = sys.argv[1]
    
    if len(sys.argv) == 4:
        action = sys.argv[2]  # 's' for subscribe, 'u' for unsubscribe
        youtuber_name = sys.argv[3]
        send_user_request(username, youtuber_name, action)
    else:
        send_user_request(username)