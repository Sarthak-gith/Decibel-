class DecibelProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      // Send raw float32 samples to the main thread
      this.port.postMessage(Float32Array.from(input[0]));
    }
    return true;
  }
}
registerProcessor('decibel-processor', DecibelProcessor);
