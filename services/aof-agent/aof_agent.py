import asyncio
import json
from nats.aio.client import Client as NATS

# Configuration
NATS_SERVER = "nats://nats:4222"  # NATS broker address
TRANSCRIPTION_TOPIC = "transcription"  # NATS topic for transcription
HIGHLIGHT_TOPIC = "highlights"  # NATS topic for publishing highlights


async def analyze_transcription():
    """
    Analyze transcription messages for specific focus areas and publish highlights.
    """
    # Connect to NATS
    nats = NATS()
    await nats.connect(NATS_SERVER)
    print("AoFAgent connected to NATS.")

    async def message_handler(msg):
        """
        Handle incoming transcription messages from the NATS topic.
        """
        data = json.loads(msg.data.decode())
        transcription_text = data.get("text", "")

        print(f"Received transcription: {transcription_text}")

        # Detect focus areas in the transcription text
        focus_areas = detect_focus_areas(transcription_text)

        if focus_areas:
            print(f"Focus areas detected: {focus_areas}")

            # Publish focus areas to the `highlights` topic
            highlight_message = {
                "highlights": focus_areas,
                "original_text": transcription_text
            }
            await nats.publish(HIGHLIGHT_TOPIC, json.dumps(highlight_message).encode())
            print(f"Highlights published: {highlight_message}")

    # Subscribe to the transcription topic
    await nats.subscribe(TRANSCRIPTION_TOPIC, cb=message_handler)


def detect_focus_areas(text):
    """
    Detect focus areas in the transcription text.
    Returns a list of focus areas with suggested highlights.
    """
    focus_keywords = [
        "pain",
        "fever",
        "injury",
        "dizziness",
        "cough",
        "fatigue"
    ]
    focus_areas = [{"word": keyword, "color": "red"} for keyword in focus_keywords if keyword in text.lower()]
    return focus_areas


if __name__ == "__main__":
    print("Starting AoFAgent...")
    asyncio.run(analyze_transcription())
