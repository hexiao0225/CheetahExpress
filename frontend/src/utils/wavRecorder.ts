/**
 * Record microphone to WAV (16 kHz mono, 16-bit) using Web Audio API.
 * Sends WAV to the backend so no ffmpeg/WebM conversion is needed.
 */

const WAV_SAMPLE_RATE = 16000;

function writeWavHeader(
  dataView: DataView,
  numSamples: number,
  sampleRate: number,
  numChannels: number
): void {
  const byteRate = sampleRate * numChannels * 2;
  const blockAlign = numChannels * 2;
  const dataSize = numSamples * blockAlign;
  const fileSize = 36 + dataSize;

  const setU16 = (offset: number, val: number) => dataView.setUint16(offset, val, true);
  const setU32 = (offset: number, val: number) => dataView.setUint32(offset, val, true);
  const setStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) dataView.setUint8(offset + i, str.charCodeAt(i));
  };

  setStr(0, "RIFF");
  setU32(4, fileSize);
  setStr(8, "WAVE");
  setStr(12, "fmt ");
  setU32(16, 16);
  setU16(20, 1);
  setU16(22, numChannels);
  setU32(24, sampleRate);
  setU32(28, byteRate);
  setU16(32, blockAlign);
  setU16(34, 16);
  setStr(36, "data");
  setU32(40, dataSize);
}

function resample(
  samples: Float32Array,
  sourceRate: number,
  targetRate: number
): Float32Array {
  if (sourceRate === targetRate) return samples;
  const ratio = sourceRate / targetRate;
  const outLength = Math.round(samples.length / ratio);
  const out = new Float32Array(outLength);
  for (let i = 0; i < outLength; i++) {
    const srcIndex = i * ratio;
    const j = Math.floor(srcIndex);
    const f = srcIndex - j;
    out[i] = samples[j] * (1 - f) + (samples[j + 1] ?? samples[j]) * f;
  }
  return out;
}

/**
 * Start recording from the given stream. Stops automatically after maxSeconds.
 * Call stop() to stop early and get the WAV blob.
 */
export function createWavRecorder(
  stream: MediaStream,
  maxSeconds: number
): { stop: () => Promise<Blob> } {
  let resolveBlob!: (blob: Blob) => void;
  const blobPromise = new Promise<Blob>((resolve) => {
    resolveBlob = resolve;
  });

  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const bufferSize = 4096;
  const processor = ctx.createScriptProcessor(bufferSize, 1, 1);
  const chunks: Float32Array[] = [];

  processor.onaudioprocess = (e: AudioProcessingEvent) => {
    const input = e.inputBuffer.getChannelData(0);
    chunks.push(new Float32Array(input));
  };

  source.connect(processor);
  processor.connect(ctx.destination);

  const finish = () => {
    try {
      processor.disconnect();
      source.disconnect();
      stream.getTracks().forEach((t) => t.stop());
    } catch (_) {
      /* ignore */
    }
    const totalLength = chunks.reduce((acc, c) => acc + c.length, 0);
    const all = new Float32Array(totalLength);
    let offset = 0;
    for (const c of chunks) {
      all.set(c, offset);
      offset += c.length;
    }
    const resampled = resample(all, ctx.sampleRate, WAV_SAMPLE_RATE);
    const numSamples = resampled.length;
    const headerLength = 44;
    const buffer = new ArrayBuffer(headerLength + numSamples * 2);
    const dataView = new DataView(buffer);
    writeWavHeader(dataView, numSamples, WAV_SAMPLE_RATE, 1);
    for (let i = 0; i < numSamples; i++) {
      const s = Math.max(-1, Math.min(1, resampled[i]));
      dataView.setInt16(headerLength + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    resolveBlob(new Blob([buffer], { type: "audio/wav" }));
  };

  const timeoutId = setTimeout(finish, maxSeconds * 1000);

  return {
    stop: () => {
      clearTimeout(timeoutId);
      finish();
      return blobPromise;
    },
  };
}
