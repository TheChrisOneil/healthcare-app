import React, { useState, useEffect, useRef } from "react";

const RealTimeTranscription = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [error, setError] = useState("");
  const websocketRef = useRef(null);
  const audioContextRef = useRef(null);

  useEffect(() => {
    let reconnectTimeout;

    const connectWebSocket = () => {
      const socket = new WebSocket("ws://localhost:8000");

      socket.onopen = () => {
        console.log("WebSocket connected");
        clearTimeout(reconnectTimeout);
      };

      socket.onclose = (event) => {
        console.error(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
        console.log("WebSocket disconnected. Attempting to reconnect...");
        reconnectTimeout = setTimeout(connectWebSocket, 2000);
      };

      socket.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.text) {
          setTranscription((prev) => prev + " " + data.text);
        }
      };

      websocketRef.current = socket;
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, []);

  const startRecording = async () => {
    console.log("Starting the recording...");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1, // Mono
          sampleRate: 16000, // 16kHz
        },
      });
      console.log("Microphone access granted, stream initialized.");

      // Initialize AudioContext
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      console.log("AudioContext initialized with sample rate:", audioContext.sampleRate);

      // Add the audio worklet module for PCM encoding
      await audioContext.audioWorklet.addModule("/pcm-processor.js");
      console.log("AudioWorklet module added successfully.");

      const source = audioContext.createMediaStreamSource(stream);
      console.log("MediaStreamSource created.");

      // Create AudioWorkletNode
      const audioWorkletNode = new AudioWorkletNode(audioContext, "pcm-processor");
      audioWorkletNode.port.onmessage = (event) => {
        const pcmData = event.data;
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          console.log(`Sending PCM data: ${pcmData.byteLength} bytes.`);
          websocketRef.current.send(pcmData);
        } else {
          console.warn("WebSocket is not open. PCM data not sent.");
        }
      };

      source.connect(audioWorkletNode);
      console.log("Connected MediaStreamSource to AudioWorkletNode.");

      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone or initializing recording:", err);
      setError("Unable to access microphone or initialize recording. Please check your permissions.");
    }
  };

  const stopRecording = () => {
    console.log("Stopping the recording...");
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      const controlMessage = JSON.stringify({ type: "control", action: "stop" });
      console.log(`Sending control message: ${controlMessage}`);
      websocketRef.current.send(controlMessage);
    } else {
      console.error("WebSocket is not open. Unable to send stop command.");
    }
    if (audioContextRef.current) {
      console.log("Closing audio context...");
      audioContextRef.current.close();
    }
    setIsRecording(false);
  };

  return (
    <div>
      <h1>Real-Time Transcription</h1>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
      <div>
        <h2>Transcription:</h2>
        <div style={{ whiteSpace: "pre-wrap", border: "1px solid #ccc", padding: "10px", borderRadius: "5px" }}>
          {transcription || "Start speaking to see the transcription..."}
        </div>
      </div>
    </div>
  );
};

export default RealTimeTranscription;
