export async function startStream(
  url: string,
  onMessage: (m: any) => void,
  source: "mic" | "tab"
): Promise<{ stop(): void; analyser: AnalyserNode; ws: WebSocket }> {
  let audioCtx: AudioContext;
  let stream: MediaStream;
  let ws: WebSocket;
  let workletNode: AudioWorkletNode;
  
  let sampleBuffer = new Float32Array(8000);
  let bufferIndex = 0;
  let shouldReconnect = true;
  let reconnectDelay = 1000;
  let recognition: any = null;

  if (source === "mic") {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 }
    });
  } else {
    stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
    stream.getVideoTracks().forEach(t => t.stop());
    if (stream.getAudioTracks().length === 0) throw new Error("No audio track: tick 'Share tab audio'");
  }

  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
  audioCtx = new AudioContextClass({ sampleRate: 16000 });
  await audioCtx.resume();
  
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 2048;

  await audioCtx.audioWorklet.addModule('/processor.js');
  workletNode = new AudioWorkletNode(audioCtx, 'decibel-processor');
  const sourceNode = audioCtx.createMediaStreamSource(stream);
  sourceNode.connect(workletNode);
  sourceNode.connect(analyser);

  function connectWebSocket() {
    if (!shouldReconnect) return;
    ws = new WebSocket(url);
    ws.onopen = () => { reconnectDelay = 1000; };
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } 
      catch (err) { onMessage(e.data); }
    };
    ws.onclose = () => {
      onMessage({ type: "status", state: "DISCONNECTED", ts: Date.now() });
      setTimeout(connectWebSocket, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 10000);
    };
    ws.onerror = () => ws.close();
  }

  connectWebSocket();

  if ('webkitSpeechRecognition' in window) {
    const SpeechRecognition = (window as any).webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    recognition.onresult = (event: any) => {
      const text = event.results[event.results.length - 1][0].transcript;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "transcript", text: text.trim(), final: true }));
      }
    };
    recognition.onend = () => {
      if (shouldReconnect) recognition.start();
    };
    recognition.start();
  }

  workletNode.port.onmessage = (e) => {
    const data = e.data;
    for (let i = 0; i < data.length; i++) {
      sampleBuffer[bufferIndex++] = data[i];
      if (bufferIndex === 8000) {
        // EXPLICIT LITTLE-ENDIAN ENCODING
        const buffer = new ArrayBuffer(16000);
        const view = new DataView(buffer);
        for (let j = 0; j < 8000; j++) {
          let s = Math.max(-1, Math.min(1, sampleBuffer[j]));
          let val = s < 0 ? s * 0x8000 : s * 0x7FFF;
          view.setInt16(j * 2, val, true); // true = little-endian
        }
        if (ws && ws.readyState === WebSocket.OPEN) ws.send(buffer);
        bufferIndex = 0;
      }
    }
  };

  return {
    analyser,
    ws,
    stop: () => {
      shouldReconnect = false;
      stream.getTracks().forEach(t => t.stop());
      audioCtx.close();
      if (ws) ws.close();
      if (recognition) recognition.stop();
    }
  };
}
