import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.handlers import TranscriptResultStreamHandler
import os
import wave

# REference: https://docs.aws.amazon.com/transcribe/latest/APIReference/API_Types_Amazon_Transcribe_Streaming_Service.html

# load the environment variables
from dotenv import load_dotenv
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TranscriptionAgent")

# AWS Transcribe Client Initialization
def initialize_transcribe_streaming_client():
    """
    Initialize the AWS Transcribe Streaming client and log the process.
    """
    try:
        logger.info("Initializing AWS Transcribe Streaming client...")
        client = TranscribeStreamingClient(region="us-east-1")
        logger.info("AWS Transcribe Streaming client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize AWS Transcribe Streaming client: {e}")
        raise

transcribe_streaming_client = initialize_transcribe_streaming_client()

class WebSocketTranscriptionHandler(TranscriptResultStreamHandler):
    def __init__(self, output_stream, websocket):
        super().__init__(output_stream)
        self.websocket = websocket

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # Log the raw transcript_event object to inspect its structure
        #logger.debug(f"Raw Transcript Event: {transcript_event}")
        try:
            # Log details about the transcript object
            transcript = transcript_event.transcript
            #logger.debug(f"Transcript Object Type: {type(transcript)}")
            #logger.debug(f"Transcript Object Attributes: {vars(transcript) if transcript else 'None'}")
            if not transcript_event.transcript.results:
                logger.warning("Transcript event contains no results.")
                return

            for result in transcript_event.transcript.results:
                transcription = result.alternatives[0].transcript if result.alternatives else None

                if transcription is None:
                    logger.warning(f"No transcription found in result: {result}")
                    continue
                if not result.is_partial:
                    logger.info(f"Final transcription received: {transcription}")
                    await self.websocket.send(json.dumps({"type": "transcription", "text": transcription}))
                    # TODO save the transcription to a file
                else:
                    logger.debug(f"Ignoring partial transcription: {transcription}")
        except Exception as e:
            logger.error(f"Error processing transcript event: {e}")        

async def write_chunks_from_file(input_stream):
    """
    Stream audio chunks from a hardcoded PCM file to the transcription input stream.
    """
    pcm_file_path = "test_audio.pcm"  # Hardcoded path to the PCM file
    try:
        with open(pcm_file_path, "rb") as pcm_file:
            while chunk := pcm_file.read(3200):  # Read 3200 bytes at a time (200ms at 16kHz mono PCM)
                logger.debug(f"Read audio chunk from file: {len(chunk)} bytes")
                await input_stream.send_audio_event(audio_chunk=chunk)
                await asyncio.sleep(0.2)  # Simulate real-time streaming
    except FileNotFoundError:
        logger.error(f"PCM file not found at path: {pcm_file_path}")
    except Exception as e:
        logger.error(f"Error reading PCM file: {e}")
    finally:
        await input_stream.end_stream()




async def write_chunks(websocket, input_stream, audio_buffer):
    """
    Connect the raw audio chunks from the WebSocket to the transcription stream.
    If no audio data is received within a timeout period, send silence to keep the stream alive.
    """
    TIMEOUT_SECONDS = 15
    SILENCE_CHUNK = b'\x00' * 3200  # 10ms of silence for 16kHz, 16-bit mono PCM

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=TIMEOUT_SECONDS)
                if isinstance(message, str):
                    # Handle control messages
                    try:
                        control_message = json.loads(message)
                        logger.debug(f"Received control message: {control_message}")                        
                        if control_message.get("type") == "control":
                            action = control_message.get("action")
                            if action == "stop":
                                logger.info("Received 'stop' command. Ending transcription session.")
                                break
                            elif action == "pause":
                                logger.info("Received 'pause' command. Sending silence.")
                                await input_stream.send_audio_event(audio_chunk=SILENCE_CHUNK)
                            elif action == "ping":
                                logger.info("Received 'ping' message. Responding with 'pong'.")
                                await websocket.send(json.dumps({"type": "control", "message": "pong"}))
                            else:
                                logger.warning(f"Unknown control action received: {action}")
                        else:
                            logger.warning(f"Message type is not 'control': {control_message}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message received: {message}")
                else:
                    # Handle audio chunks
                    logger.debug(f"Received audio chunk: {len(message)} bytes")
                    audio_buffer.append(message)
                    # await input_stream.send_audio_event(audio_chunk=message)
            except asyncio.TimeoutError:
                logger.warning("No audio received from client. Sending silence to keep the stream alive.")
                await input_stream.send_audio_event(audio_chunk=SILENCE_CHUNK)
    except websockets.ConnectionClosed as e:
        logger.info(f"WebSocket connection closed: {e}")
    except Exception as e:
        logger.error(f"Error in write_chunks: {e}")
    finally:
        logger.debug(f"Closing AWS Transcribe connection. Ending transcription session.")
        await input_stream.end_stream()

def save_audio_file(audio_data, filename="recorded_audio.wav"):
    """
    Save raw audio data to a WAV file in the specified directory.
    """
    recordings_dir = os.getenv("RECORDINGS_DIR")
    logger.debug(f"Recordings directory: {recordings_dir}")
    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)

    filepath = os.path.join(recordings_dir, filename)
    try:
        logger.info(f"Saving audio data to {filepath}...")
        with wave.open(filepath, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_data)
        logger.info(f"Audio data saved successfully to {filepath}.")
    except Exception as e:
        logger.error(f"Failed to save audio file: {e}")

async def transcribe_audio_stream(websocket, use_pcm_file=False):
    """
    Handle audio streaming and real-time transcription via AWS Transcribe Streaming.
    """
    logger.info("Starting transcription session...")
    stream = None
    audio_buffer = []
    try:
        stream = await transcribe_streaming_client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=16000,
            media_encoding="pcm",
        )
        logger.info("AWS Transcribe Streaming session started.")

        handler = WebSocketTranscriptionHandler(stream.output_stream, websocket)
        
        if use_pcm_file:
            await asyncio.gather(write_chunks_from_file(stream.input_stream), handler.handle_events())
        else:
            await asyncio.gather(write_chunks(websocket, stream.input_stream, audio_buffer), handler.handle_events())
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        await websocket.send(json.dumps({"type": "error", "message": "Transcription failed"}))
    finally:
        logger.debug("AWS Transcribe Streaming session is ending.")
        if stream and hasattr(stream, 'input_stream'):
            try:
                logger.debug(f"Closing AWS Transcribe connection. Ending transcription session.")
                await stream.input_stream.end_stream()
            except Exception as e:
                logger.error(f"Error while ending the AWS Transcribe stream: {e}")
        else:
            logger.warning("No active transcription stream to close.")

        if audio_buffer:
            try:
                logger.debug("Saving raw audio data.")
                filename = f"recorded_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                save_audio_file(b"".join(audio_buffer), filename=filename)
                logger.info(f"Audio data saved to {filename}.")
            except Exception as e:
                logger.error(f"Error while saving audio file: {e}")

        logger.info("Transcription session ended.")

async def handle_websocket(websocket):
    """
    Manage WebSocket connections.
    """
    logger.info(f"New WebSocket connection from {websocket.remote_address}")
    try:
        await transcribe_audio_stream(websocket)
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket connection closed with code {e.code} and reason: {e.reason}")
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")
    finally:
        logger.info(f"WebSocket connection closed for {websocket.remote_address}")





async def main():
    """
    Start the WebSocket server for real-time transcription.
    """
    logger.info("Starting TranscriptionAgent WebSocket server...")
    server = await websockets.serve(
        handle_websocket,
        "0.0.0.0",
        8000,
        ping_interval=30,
        ping_timeout=60
    )
    logger.info("WebSocket server started on ws://0.0.0.0:8000")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())