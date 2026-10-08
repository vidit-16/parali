// Push-to-talk recorder: 16 kHz mono 16-bit PCM, base64, for Amazon Transcribe streaming.
export class Recorder {
  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.rate = this.ctx.sampleRate;
    const src = this.ctx.createMediaStreamSource(this.stream);
    this.node = this.ctx.createScriptProcessor(4096, 1, 1);
    this.chunks = [];
    this.node.onaudioprocess = (e) => this.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    src.connect(this.node);
    this.node.connect(this.ctx.destination);
    this.t0 = performance.now();
  }

  async stop() {
    this.node.disconnect();
    this.stream.getTracks().forEach((t) => t.stop());
    await this.ctx.close();
    const seconds = (performance.now() - this.t0) / 1000;
    const flat = concat(this.chunks);
    const pcm = toPcm16(downsample(flat, this.rate, 16000));
    return { b64: base64(pcm), seconds };
  }
}

function concat(chunks) {
  const out = new Float32Array(chunks.reduce((n, c) => n + c.length, 0));
  let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out;
}

function downsample(buf, from, to) {
  if (from === to) return buf;
  const ratio = from / to, n = Math.floor(buf.length / ratio), out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const a = Math.floor(i * ratio), b = Math.min(buf.length, Math.floor((i + 1) * ratio));
    let s = 0;
    for (let j = a; j < b; j++) s += buf[j];
    out[i] = s / Math.max(1, b - a);
  }
  return out;
}

function toPcm16(f32) {
  const out = new Uint8Array(f32.length * 2), v = new DataView(out.buffer);
  for (let i = 0; i < f32.length; i++) v.setInt16(i * 2, Math.max(-1, Math.min(1, f32[i])) * 0x7fff, true);
  return out;
}

function base64(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

// Fallback when the server has no Transcribe: the browser's own Hindi recognition (Chrome, Edge).
export function browserRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  return () => new Promise((resolve, reject) => {
    const r = new SR();
    r.lang = "hi-IN";
    r.interimResults = false;
    r.onresult = (e) => resolve(e.results[0][0].transcript);
    r.onerror = (e) => reject(new Error(e.error));
    r.start();
  });
}
