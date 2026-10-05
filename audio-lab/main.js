let audioCtx, stream, ws, workletNode, analyser, animationId;
let sampleBuffer = new Float32Array(8000);
let bufferIndex = 0;
const ROLLING_SAMPLES = 80000;
let rollingBuffer = new Int16Array(ROLLING_SAMPLES);
let rollingIndex = 0;
let reconnectDelay = 1000;
let shouldReconnect = true;
let isThreat = false;

const logEl = document.getElementById('log');
function log(msg) { logEl.textContent += msg + '\n'; logEl.scrollTop = logEl.scrollHeight; }

const canvas = document.getElementById('waveform');
const canvasCtx = canvas.getContext('2d');

function drawWaveform() {
  if (!analyser) return;
  animationId = requestAnimationFrame(drawWaveform);
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  analyser.getByteTimeDomainData(dataArray);

  canvasCtx.fillStyle = 'rgb(0, 0, 0)';
  canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
  canvasCtx.lineWidth = 2;
  canvasCtx.strokeStyle = isThreat ? 'rgb(255, 50, 50)' : 'rgb(50, 255, 100)';
  canvasCtx.beginPath();
  const sliceWidth = canvas.width * 1.0 / bufferLength;
  let x = 0;
  for (let i = 0; i < bufferLength; i++) {
    const v = dataArray[i] / 128.0;
    const y = v * (canvas.height / 2);
    if (i === 0) canvasCtx.moveTo(x, y);
    else canvasCtx.lineTo(x, y);
    x += sliceWidth;
  }
  canvasCtx.lineTo(canvas.width, canvas.height / 2);
  canvasCtx.stroke();
}

function connectWebSocket() {
  if (!shouldReconnect) return;
  ws = new WebSocket('ws://localhost:8000/stream');
  ws.onopen = () => { log("[+] WebSocket connected"); reconnectDelay = 1000; };
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === "verdict") isThreat = msg.verdict === "Fake";
      log("[Server] " + e.data);
    } catch(err) { log("[Server] " + e.data); }
  };
  ws.onclose = () => {
    log(`[-] WebSocket closed. Reconnecting...`);
    log("[UI Event] " + JSON.stringify({ type: "status", state: "DISCONNECTED", ts: Date.now() }));
    setTimeout(connectWebSocket, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 10000);
  };
  ws.onerror = () => ws.close();
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
}

function exportWav() {
  const outBuffer = new Int16Array(ROLLING_SAMPLES);
  let outIdx = 0;
  for (let i = rollingIndex; i < ROLLING_SAMPLES; i++) outBuffer[outIdx++] = rollingBuffer[i];
  for (let i = 0; i < rollingIndex; i++) outBuffer[outIdx++] = rollingBuffer[i];
  const wavBuffer = new ArrayBuffer(44 + outBuffer.length * 2);
  const view = new DataView(wavBuffer);
  writeString(view, 0, 'RIFF'); view.setUint32(4, 36 + outBuffer.length * 2, true);
  writeString(view, 8, 'WAVE'); writeString(view, 12, 'fmt '); view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, 16000, true);
  view.setUint32(28, 16000 * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeString(view, 36, 'data'); view.setUint32(40, outBuffer.length * 2, true);
  let offset = 44;
  for (let i = 0; i < outBuffer.length; i++, offset += 2) view.setInt16(offset, outBuffer[i], true);
  const blob = new Blob([view], { type: 'audio/wav' }); const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.style.display = 'none'; a.href = url; a.download = 'decibel_test_5s.wav';
  document.body.appendChild(a); a.click();
  setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  log("[+] Exported 5s WAV");
}

async function startAudio(mode) {
  document.getElementById('startBtn').disabled = true;
  document.getElementById('tabBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
  document.getElementById('wavBtn').disabled = false;
  shouldReconnect = true;
  
  try {
    if (mode === "mic") {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 } });
      log("[+] Mic stream started");
    } else {
      // P4-14: Tab capture
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      // Stop the video tracks immediately so we only capture audio
      stream.getVideoTracks().forEach(t => t.stop());
      if (stream.getAudioTracks().length === 0) {
        throw new Error("No audio track: tick 'Share tab audio'");
      }
      log("[+] Tab stream started");
    }

    audioCtx = new AudioContext({ sampleRate: 16000 });
    await audioCtx.resume();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    
    await audioCtx.audioWorklet.addModule('processor.js');
    workletNode = new AudioWorkletNode(audioCtx, 'decibel-processor');
    const source = audioCtx.createMediaStreamSource(stream);
    
    source.connect(workletNode);
    source.connect(analyser);
    
    connectWebSocket();
    drawWaveform();

    workletNode.port.onmessage = (e) => {
      const data = e.data;
      for (let i = 0; i < data.length; i++) {
        sampleBuffer[bufferIndex++] = data[i];
        if (bufferIndex === 8000) {
          const int16Buffer = new Int16Array(8000);
          for (let j = 0; j < 8000; j++) {
            let s = Math.max(-1, Math.min(1, sampleBuffer[j]));
            let val = s < 0 ? s * 0x8000 : s * 0x7FFF;
            int16Buffer[j] = val;
            rollingBuffer[rollingIndex] = val;
            rollingIndex = (rollingIndex + 1) % ROLLING_SAMPLES;
          }
          if (ws && ws.readyState === WebSocket.OPEN) ws.send(int16Buffer.buffer);
          bufferIndex = 0;
        }
      }
    };
  } catch (err) {
    log("[-] Error: " + err);
    document.getElementById('stopBtn').click(); // reset UI
  }
}

document.getElementById('startBtn').onclick = () => startAudio("mic");
document.getElementById('tabBtn').onclick = () => startAudio("tab");

document.getElementById('stopBtn').onclick = () => {
  document.getElementById('startBtn').disabled = false;
  document.getElementById('tabBtn').disabled = false;
  document.getElementById('stopBtn').disabled = true;
  document.getElementById('wavBtn').disabled = true;
  shouldReconnect = false;
  isThreat = false;
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (audioCtx) audioCtx.close();
  if (ws) ws.close();
  if (animationId) cancelAnimationFrame(animationId);
  
  canvasCtx.fillStyle = 'rgb(0, 0, 0)';
  canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
  canvasCtx.beginPath();
  canvasCtx.strokeStyle = '#333';
  canvasCtx.moveTo(0, canvas.height/2);
  canvasCtx.lineTo(canvas.width, canvas.height/2);
  canvasCtx.stroke();
  
  log("[-] Stopped.");
};

document.getElementById('wavBtn').onclick = exportWav;
