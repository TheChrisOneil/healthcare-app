# Metadata
- **Document Purpose**: High-level understanding of the project architecture and setup.
- **Primary Audience**: Programmers, AI Agents
- **Focus Areas**: Architecture, Module Responsibilities, Environment Setup
- **Last Updated**: [Insert Date]
- **Maintainer**: [Name or Role, e.g., "Tech Lead"]

---

# System Overview
This project focuses on building a real-time transcription system for healthcare applications. It leverages microservices architecture with React for the frontend and AWS Transcribe for audio-to-text conversion. WebSockets enable real-time communication between components.

---

# Module Responsibilities
### Frontend
- Captures audio via the user's microphone.
- Streams audio to the backend over WebSockets.
- Displays transcription results in real time.

### API Gateway
- Routes requests to backend services, including the transcription agent and other microservices.
- Manages load balancing and request handling.

### Transcription Agent
- Processes audio streams received from the frontend.
- Uses AWS Transcribe Streaming for transcription.
- Publishes transcription data to NATS for other microservices.

### Messaging Service (NATS)
- Handles communication between the transcription agent and other services (e.g., Order Agent, Area of Focus Agent).

---

# Environment Setup
### Local Development
- **Containerization**: All components are containerized using Docker and orchestrated with Docker Compose.
- **Services**:
  - `frontend`: React application.
  - `api-gateway`: NGINX for routing.
  - `transcription-agent`: Python-based backend service for transcription.
  - `nats`: Messaging service.

### Environment Variables
- AWS credentials:
  - `AWS_REGION`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
- NATS configuration:
  - `NATS_SERVER=nats://nats:4222`

---

# Key Technical Insights
- **Real-Time Processing**:
  - WebSockets are used for streaming audio from the frontend to the backend.
  - AWS Transcribe Streaming handles audio-to-text conversion.

- **System Scaling**:
  - Microservices communicate asynchronously through NATS.

---

# Action Items
- Review WebSocket lifecycle in frontend for stability.
- Optimize backend transcription agent to handle high-concurrency scenarios.
- Increase test coverage for all services.
