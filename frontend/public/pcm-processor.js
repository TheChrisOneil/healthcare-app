class PCMProcessor extends AudioWorkletProcessor {
    process(inputs) {
        const input = inputs[0];
        if (input && input[0]) {
            const buffer = input[0];
            const pcmData = this.encodePCM(buffer);
            this.port.postMessage(pcmData);
        }
        return true;
    }

    encodePCM(buffer) {
        const output = new DataView(new ArrayBuffer(buffer.length * 2));
        for (let i = 0; i < buffer.length; i++) {
            const sample = Math.max(-1, Math.min(1, buffer[i]));
            output.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
        }
        return output.buffer;
    }
}

registerProcessor('pcm-processor', PCMProcessor);
