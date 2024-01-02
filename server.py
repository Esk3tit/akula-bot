from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import hashlib
import hmac
import os
import json
import pika

load_dotenv()
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue
channel.queue_declare(queue='twitch_notifications')

app = Flask(__name__)
CORS(app)


@app.route('/twitch/eventsub', methods=['POST'])
def twitch_webhook():
    """
    Description: Process webhook notifications/events from Twitch
    """

    """
    Verify event message (see if it came from Twitch)
    """
    message_id = request.headers.get('Twitch-Eventsub-Message-Id')
    timestamp = request.headers.get('Twitch-Eventsub-Message-Timestamp')
    signature = request.headers.get('Twitch-Eventsub-Message-Signature')
    body = request.data.decode()  # get the raw string of the body

    # HMAC signature
    hmac_message = message_id + timestamp + body
    computed_signature = 'sha256=' + hmac.new(WEBHOOK_SECRET.encode(), msg=hmac_message.encode(),
                                              digestmod=hashlib.sha256).hexdigest()

    # Compare computed signature with message signature
    if not hmac.compare_digest(computed_signature, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    """
    Process subscription notifications
    """
    data = request.json
    app.logger.debug(data)

    # Twitch verification challenge
    # Body of request has challenge value that must be sent back
    message_type = request.headers.get('Twitch-Eventsub-Message-Type')
    if message_type == 'webhook_callback_verification':
        challenge = data['challenge']
        return Response(challenge, content_type='text/plain', status=200)
    elif message_type == 'notification':
        match data['subscription']['type']:
            case 'stream.online':
                message = json.dumps({"streamer_name": data['event']['broadcaster_user_name'],
                                      "type": "live", "started_at": data['event']['started_at']})
                channel.basic_publish(exchange='', routing_key='twitch_notifications', body=message)
                app.logger.debug(f"{data['event']['broadcaster_user_name']} is live! Sent message to queue")

    return jsonify({'status': 'received'}), 200


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
