"""Command line:  python -m story2d.cli script.txt --duration 120 --out video.mp4"""
import argparse, json, tempfile
from pathlib import Path
from . import planner, job

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('script'); ap.add_argument('--duration', type=float, default=0, help='seconds (0 = natural speaking speed)')
    ap.add_argument('--mode', default='Story'); ap.add_argument('--theme', default='Midnight'); ap.add_argument('--res', default='720p'); ap.add_argument('--fps', type=int, default=15)
    ap.add_argument('--scene-secs', type=float, default=20); ap.add_argument('--out', default='video.mp4'); ap.add_argument('--no-music', action='store_true'); ap.add_argument('--aspect', default='16:9')
    a = ap.parse_args(); txt = Path(a.script).read_text(encoding='utf-8')
    sc = planner.parse(txt, a.mode, a.scene_secs); planner.allocate(sc, a.duration or None)
    j = dict(scenes=sc, settings=dict(theme=a.theme, res=a.res, fps=a.fps, aspect=a.aspect, captions=True), audio=dict(mode='none', music=not a.no_music), out=str(Path(a.out).resolve()), workdir=tempfile.mkdtemp())
    job.run(j); print(Path(j['workdir'], 'progress.json').read_text(encoding='utf-8'))
