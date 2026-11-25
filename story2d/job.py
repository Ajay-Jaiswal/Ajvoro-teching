"""Background job: python -m story2d.job job.json   (keeps Qt out of Streamlit's threads, frees RAM afterwards)"""
import json, os, sys, time, traceback
from pathlib import Path
from . import audio, render, planner


def _prog(pf, phase, pct, msg='', **kw):
    # ensure_ascii + explicit utf-8 + atomic replace: safe on Windows (cp1252 default, file locks)
    data = json.dumps(dict(phase=phase, pct=pct, msg=msg, **kw))
    tmp = Path(str(pf) + '.tmp'); tmp.write_text(data, encoding='utf-8')
    for _ in range(40):
        try: os.replace(tmp, pf); return
        except PermissionError: time.sleep(0.05)


def run(job):
    wd = Path(job['workdir']); wd.mkdir(parents=True, exist_ok=True); pf = wd / 'progress.json'; scenes = job['scenes']; st = job['settings']; au = job.get('audio', {'mode': 'none'})
    try:
        if job.get('preview') is not None:
            i = job['preview']['index']; sc = scenes[i]; sc['idx'] = i; render.preview(sc, st, job['preview'].get('frac', 0.8), wd / 'preview.png'); _prog(pf, 'done', 100); return
        audio_path = None; mode = au.get('mode', 'none'); target = job.get('target')
        if mode == 'upload':
            _prog(pf, 'audio', 2, 'आवाज़ फ़ाइल पढ़ रहे हैं...'); src = au['path']; total = audio.duration(src)
            chars = [max(1, s.get('chars', len(s['text']))) for s in scenes]
            if au.get('sync', True): durs = audio.sync_durations(chars, total, audio.silences(src))
            else: durs = [total * c / sum(chars) for c in chars]
            for s, d in zip(scenes, durs): s['secs'] = d
            audio_path = Path(src)
        elif mode == 'tts':
            def tp(i, n): _prog(pf, 'voice', 2 + int(18 * i / n), f'आवाज़ बन रही है... {i}/{n}')
            texts = [s['text'].replace('#', '') for s in scenes]; rate = au.get('rate', 0)
            clips, durs = audio.tts_scenes(texts, au['voice'], rate, wd, tp)
            if target and au.get('fit', True):
                tot = sum(durs) + 0.4 * len(durs); r = tot / target; newrate = int(max(-35, min(60, round((r - 1) * 100 + rate))))
                if abs(newrate - rate) >= 4: clips, durs = audio.tts_scenes(texts, au['voice'], newrate, wd, tp)
            for s, d in zip(scenes, durs): s['secs'] = max(2.5, d + 0.4)
            audio_path = audio.build_voice(clips, durs, 0.4, wd)
            # rebuild so every scene's audio length matches its (possibly min-clamped) duration
        total_secs = sum(s['secs'] for s in scenes)
        if au.get('music', True):
            _prog(pf, 'audio', 22, 'बैकग्राउंड म्यूज़िक...'); m = audio.music(total_secs + 1, wd / 'music.wav')
            audio_path = audio.mix(audio_path, m, wd / 'mix.wav', au.get('music_vol', 0.2)) if audio_path else m
        out = Path(job['out']); out.parent.mkdir(parents=True, exist_ok=True)
        res = render.render(scenes, st, out, audio_path, lambda a, b: _prog(pf, 'render', 25 + int(73 * a / b), f'वीडियो बन रहा है... {a}/{b} frames', eta=None))
        out.with_suffix('.srt').write_text(render.srt(scenes), encoding='utf-8')
        _prog(pf, 'done', 100, 'तैयार!', result=dict(res, srt=str(out.with_suffix('.srt')), durations=[s['secs'] for s in scenes]))
    except BaseException as e:
        tb = traceback.format_exc(); sys.stderr.write(tb)
        try: _prog(pf, 'error', 0, str(e), trace=tb)
        except Exception: pass


if __name__ == '__main__':
    for st_ in (sys.stdout, sys.stderr):
        try: st_.reconfigure(encoding='utf-8', errors='replace')
        except Exception: pass
    run(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
