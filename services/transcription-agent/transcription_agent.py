import asyncio
import websockets
import json
from nats.aio.client import Client as NATS

# Configuration
NATS_SERVER = "nats://nats:4222"  # NATS broker address
TRANSCRIPTION_TOPIC = "transcription"  # NATS topic for transcription messages


async def handle_websocket(websocket, path):
    """
    Handle incoming WebSocket connections for audio streaming.
    """
    # Connect to NATS
    nats = NATS()
    await nats.connect(NATS_SERVER)

    print("WebSocket connection established.")

    try:
        async for message in websocket:
            # Process incoming audio chunks (as bytes)
            transcription = process_audio(message)

            # Publish transcription to the NATS topic
            await nats.publish(
                TRANSCRIPTION_TOPIC,
                json.dumps({"text": transcription}).encode()
            )

            # Optional: Send acknowledgment or response to WebSocket client
            await websocket.send(
                json.dumps({"type": "transcription", "text": transcription})
            )
    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        await nats.close()
        print("NATS connection closed.")


def process_audio(audio_chunk):
    """
    Simulate processing of audio data into text transcription.
    Replace this with a real transcription engine (e.g., Google Speech-to-Text).
    """
    # Simulating transcription logic
    return f"Transcribed text for audio chunk: {len(audio_chunk)} bytes"


async def main():
    """
    Start the WebSocket server for the TranscriptionAgent.
    """
    print("Starting TranscriptionAgent WebSocket server...")
    server = await websockets.serve(handle_websocket, "0.0.0.0", 8000)
    await server.wait_closed()


# Run the server
if __name__ == "__main__":
    asyncio.run(main())
