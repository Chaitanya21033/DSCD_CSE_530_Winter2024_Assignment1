import pika
import json
import threading

class YoutubeServer:
    
    def __init__(self):
        ''' 
        Server class for handling user and youtuber requests
        '''
        self.subscriptions = {}  # Format: { 'username': ['youtuber1', 'youtuber2'], ... }
        self.notifications = {}  # Format: { 'username': ['notification1', 'notification2'], ... }

    def consume_user_requests(self):
        '''
        Establish a new connection for this thread
        '''
        connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0'))
        channel = connection.channel()
        channel.queue_declare(queue='user_requests')

        def callback(ch, method, properties, body):
            '''
            Process user request
            '''
            request = json.loads(body)
            username = request['user']

            if 'subscribe' in request:
                self.update_subscription(username, request['youtuber'], request['subscribe'])
                action = 'subscribed' if request['subscribe'] else 'unsubscribed'
                print(f"{username} {action} to {request['youtuber']}")
            else:
                print(f"{username} logged in")
                self.send_notifications(username)

        channel.basic_consume(queue='user_requests', on_message_callback=callback, auto_ack=True)
        print("Consuming user requests...")
        try:
            channel.start_consuming()
        finally:
            connection.close()

    def consume_youtuber_requests(self):
        '''
        Establish a new connection for this thread
        '''
        connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0'))
        channel = connection.channel()
        channel.queue_declare(queue='youtuber_uploads')

        def callback(ch, method, properties, body):
            # Process youtuber video upload
            video_info = json.loads(body)
            youtuber = video_info['youtuber']
            video_name = video_info['videoName']
            print(f"{youtuber} uploaded {video_name}")
            self.notify_users(youtuber, video_name)

        channel.basic_consume(queue='youtuber_uploads', on_message_callback=callback, auto_ack=True)
        print("Consuming youtuber requests...")
        try:
            channel.start_consuming()
        finally:
            connection.close()

    def update_subscription(self, user, youtuber, subscribe):
        '''
        Update user subscription
        '''
        if subscribe:
            self.subscriptions.setdefault(user, set()).add(youtuber)
        else:
            self.subscriptions.get(user, set()).discard(youtuber)

    def notify_users(self, youtuber, video_name):
        '''
        Notify subscribed users of a new video
        '''
        notification = f"{youtuber} uploaded {video_name}"
        for user, subs in self.subscriptions.items():
            if youtuber in subs:
                # Ensure the user's notification queue exists
                connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0'))
                channel = connection.channel()
                channel.queue_declare(queue=user)  # User-specific queue named after their username
                
                # Publish the notification to the user's queue
                channel.basic_publish(exchange='', routing_key=user, body=notification)
                print(f"Notification sent to {user}: {notification}")
                
                connection.close()  # Close the connection after publishing


    def send_notifications(self, user):
        '''
        Assuming each user has a queue with their username for notifications
        '''
        connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0'))
        channel = connection.channel()
        channel.queue_declare(queue=user)  # Ensure the queue exists
        
        notifications = self.notifications.get(user, [])
        for notification in notifications:
            channel.basic_publish(exchange='', routing_key=user, body=notification)
            print(f"Notification sent to {user}: {notification}")
        
        self.notifications[user] = []  # Clear notifications after sending
        connection.close()

    def start(self):
        '''
        Start threads for consuming user and youtuber requests
        '''
        user_thread = threading.Thread(target=self.consume_user_requests)
        youtuber_thread = threading.Thread(target=self.consume_youtuber_requests)

        user_thread.start()
        youtuber_thread.start()

        user_thread.join()
        youtuber_thread.join()

if __name__ == '__main__':
    server = YoutubeServer()
    server.start()

