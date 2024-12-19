import asyncio
import json
from nats.aio.client import Client as NATS

# Configuration
NATS_SERVER = "nats://nats:4222"  # NATS broker address
TRANSCRIPTION_TOPIC = "transcription"  # NATS topic for transcription
ORDER_TOPIC = "order"  # NATS topic for publishing orders


async def monitor_transcription():
    """
    Monitor the transcription topic in NATS for potential orders.
    """
    # Connect to NATS
    nats = NATS()
    await nats.connect(NATS_SERVER)
    print("OrderAgent connected to NATS.")

    async def message_handler(msg):
        """
        Handle incoming transcription messages from the NATS topic.
        """
        data = json.loads(msg.data.decode())
        transcription_text = data.get("text", "")

        print(f"Received transcription: {transcription_text}")

        # Analyze transcription for order-related keywords
        detected_items = detect_order_keywords(transcription_text)

        if detected_items:
            print(f"Detected order items: {detected_items}")

            # Publish detected orders to the `order` topic
            order_message = {
                "items": detected_items,
                "original_text": transcription_text
            }
            await nats.publish(ORDER_TOPIC, json.dumps(order_message).encode())
            print(f"Order published: {order_message}")

    # Subscribe to the transcription topic
    await nats.subscribe(TRANSCRIPTION_TOPIC, cb=message_handler)


def detect_order_keywords(text):
    """
    Detect order-related keywords in the transcription text.
    Returns a list of detected items.
    """
    order_keywords = [
        "medication",
        "supplement",
        "device",
        "supply",
        "lab kit",
        "treatment plan"
    ]
    detected_items = [keyword for keyword in order_keywords if keyword in text.lower()]
    return detected_items


if __name__ == "__main__":
    print("Starting OrderAgent...")
    asyncio.run(monitor_transcription())
