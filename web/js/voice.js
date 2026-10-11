// Tap-to-talk recorder: 16 kHz mono 16-bit PCM, base64, for speech to text.
// It listens for the end of speech itself: onEnd("silence") after SILENCE_MS of quiet once the person has spoken,
// onEnd("nothing") if nothing was said for NOTHING_MS, onEnd("limit") at LIMIT_MS. onLevel(0..1) drives the ring.
const SILENCE_MS = 4000, NOTHING_MS = 8000, LIMIT_MS = 30000, LOUD = 0.02;
export class Recorder {
  constructor({ onEnd = null, onLevel = null } = {}) {
    this.onEnd = onEnd;
    this.onLevel = onLevel;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.rate = this.ctx.sampleRate;
    const src = this.ctx.createMediaStreamSource(this.stream);
    this.node = this.ctx.createScriptProcessor(4096, 1, 1);
    this.chunks = [];
    this.spoke = false;
    this.lastLoud = performance.now();
    this.node.onaudioprocess = (e) => {
      const data = e.inputBuffer.getChannelData(0);
      this.chunks.push(new Float32Array(data));
      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
      const rms = Math.sqrt(sum / data.length), now = performance.now();
      this.onLevel?.(Math.min(1, rms * 12));
      if (rms > LOUD) { this.spoke = true; this.lastLoud = now; }
      if (this.ended) return;
      const why = this.spoke && now - this.lastLoud > SILENCE_MS ? "silence" : !this.spoke && now - this.t0 > NOTHING_MS ? "nothing"
        : now - this.t0 > LIMIT_MS ? "limit" : null;
      if (why) { this.ended = true; this.onEnd?.(why); }
    };
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
