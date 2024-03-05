import pika
import sys
import json

server_ip_addr = "10.190.0.2"

def publish_video(youtuber, video_name):
    """
    Publishes a video upload message to the YouTube server via RabbitMQ.
    """
    # Establish connection to RabbitMQ
    credentials = pika.PlainCredentials('admin1', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(server_ip_addr, credentials=credentials))
    channel = connection.channel()

    # Ensure the queue exists
    channel.queue_declare(queue='youtuber_uploads')

    # Create and send message
    message = json.dumps({'youtuber': youtuber, 'videoName': video_name})
    channel.basic_publish(exchange='', routing_key='youtuber_uploads', body=message)
    print("SUCCESS: Video published")

    # Close the connection
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) <= 3 or sys.argv[1] == "-h":
        print("Usage: python3 youtuber.py <YoutuberName> <VideoName>")
        sys.exit(1)

    youtuber_name = sys.argv[1]
    video_name = ' '.join(sys.argv[2:])  # Allows for video names with spaces
    publish_video(youtuber_name, video_name)