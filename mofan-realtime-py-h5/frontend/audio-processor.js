class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 8192;
    this.buffer = new Int16Array(this.bufferSize);
    this.bufferIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      const channelData = input[0]; // Use the first channel (mono)
      
      for (let i = 0; i < channelData.length; i++) {
        // Convert Float32 to Int16
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        this.buffer[this.bufferIndex++] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;

        if (this.bufferIndex >= this.bufferSize) {
          this.port.postMessage(this.buffer);
          this.buffer = new Int16Array(this.bufferSize);
          this.bufferIndex = 0;
        }
      }
    }
    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
