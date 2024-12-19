CREATE TABLE transcription_metadata (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    clinician_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    audio_file_path TEXT,
    transcription_file_path TEXT
);
