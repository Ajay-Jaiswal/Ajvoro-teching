"""Audio helpers: ffmpeg lookup, background music, silence-sync, optional Edge-TTS voice."""
import subprocess, re, wave, os, asyncio
from pathlib import Path


def ffmpeg():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def _run(args):
    return subprocess.run([ffmpeg(), '-hide_banner', '-loglevel', 'info', *args], capture_output=True, text=True)


def duration(path):
    m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', _run(['-i', str(path)]).stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def music(total, out):
    import numpy as np
    sr = 22050; t = np.arange(int(total * sr)) / sr; y = np.zeros_like(t)
    ch = [(220, 261.63, 329.63), (174.61, 220, 261.63), (261.63, 329.63, 392), (196, 246.94, 293.66)]
    for i in range(int(total // 5) + 1):
        s0 = i * 5; m = (t >= s0) & (t < s0 + 6); tt = t[m] - s0
        env = np.minimum(1, tt / 1.5) * np.clip((6 - tt) / 1.5, 0, 1)
        y[m] += env * sum(np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2 * tt + 0.3) + 0.3 * np.sin(2 * np.pi * f * 1.003 * tt) for f in ch[i % 4]) / 9
    y *= 0.5 * np.clip((total - t) / 3, 0, 1) * np.clip(t / 2, 0, 1)
    with wave.open(str(out), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype('<i2').tobytes())
    return out


def silences(path):
    err = _run(['-i', str(path), '-af', 'silencedetect=n=-35dB:d=0.35', '-f', 'null', '-']).stderr
    st = [float(x) for x in re.findall(r'silence_start:\s*([\d.]+)', err)]; en = [float(x) for x in re.findall(r'silence_end:\s*([\d.]+)', err)]
    return [(a + b) / 2 for a, b in zip(st, en)]


def sync_durations(chars, total, sil, tol=0.35):
    """scene boundaries start proportional to text length, then snap to the nearest pause in the voice"""
    tot = float(sum(chars)); b, acc = [], 0
    for c in chars[:-1]:
        acc += c; b.append(acc / tot * total)
    out, prev = [], 0.0
    for i, x in enumerate(b):
        lo = prev + 2.0; win = tol * (chars[i] / tot * total)
        cand = [s for s in sil if abs(s - x) <= max(2.0, win) and s > lo]
        nb = min(cand, key=lambda s: abs(s - x)) if cand else max(x, lo)
        out.append(nb); prev = nb
    bounds = [0.0] + out + [total]
    return [max(1.0, bounds[i + 1] - bounds[i]) for i in range(len(chars))]


VOICES = {'हिंदी - Swara (महिला)': 'hi-IN-SwaraNeural', 'हिंदी - Madhur (पुरुष)': 'hi-IN-MadhurNeural',
          'English India - Neerja (F)': 'en-IN-NeerjaNeural', 'English India - Prabhat (M)': 'en-IN-PrabhatNeural',
          'English US - Jenny (F)': 'en-US-JennyNeural', 'English US - Guy (M)': 'en-US-GuyNeural'}


def tts_scenes(texts, voice, rate_pct, workdir, progress=None):
    """Edge-TTS (free, needs internet, no login).  Returns clip paths + durations."""
    import edge_tts
    rate = f'{int(rate_pct):+d}%'; clips, durs = [], []
    async def one(txt, out):
        await edge_tts.Communicate(txt, voice, rate=rate).save(str(out))
    for i, t in enumerate(texts):
        out = Path(workdir) / f'tts_{i:03d}.mp3'
        asyncio.run(one(t, out)); clips.append(out); durs.append(duration(out))
        if progress: progress(i + 1, len(texts))
    return clips, durs


def build_voice(clips, durs, pad, workdir):
    """pad every clip to scene length and concatenate -> one wav"""
    lst = []
    for i, (c, d) in enumerate(zip(clips, durs)):
        w = Path(workdir) / f'pad_{i:03d}.wav'
        _run(['-y', '-i', str(c), '-ar', '22050', '-ac', '1', '-af', f'apad=pad_dur={pad}', str(w)]); lst.append(w)
    lf = Path(workdir) / 'voice.txt'; lf.write_text(''.join(f"file '{p.as_posix()}'\n" for p in lst), encoding='utf-8')
    out = Path(workdir) / 'voice.wav'; _run(['-y', '-f', 'concat', '-safe', '0', '-i', str(lf), '-c', 'copy', str(out)]); return out


def mix(voice, mus, out, music_vol=0.2):
    r = _run(['-y', '-i', str(voice), '-i', str(mus), '-filter_complex', f'[1:a]volume={music_vol}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]', '-map', '[a]', str(out)])
    if not Path(out).exists() or Path(out).stat().st_size < 1000:
        _run(['-y', '-i', str(voice), '-i', str(mus), '-filter_complex', f'[1:a]volume={music_vol * 2}[m];[0:a][m]amix=inputs=2:duration=first[a]', '-map', '[a]', str(out)])
    return out
