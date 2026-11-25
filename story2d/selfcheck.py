"""python -m story2d.selfcheck  -> prints what works on this computer"""
import sys, platform, tempfile, os
def main():
    out = [f'Python {sys.version.split()[0]} on {platform.platform()}']
    try:
        import PySide6; out.append('PySide6 OK ' + PySide6.__version__)
        from story2d.canvas import Canvas, init
        fam = init(); c = Canvas(640, 360); c.grad((10, 16, 40), (30, 36, 90)); c.t('AI की पूरी कहानी', 320, 180, 40)
        p = os.path.join(tempfile.gettempdir(), 'story2d_check.png'); c.save(p); c.close(); out.append(f'Qt drawing OK, font: {fam}, test image: {p}')
    except Exception as e: out.append(f'PROBLEM with PySide6/Qt: {e!r}  -> try: pip install --upgrade PySide6-Essentials  (Python 3.11 or 3.12 is the safest)')
    try:
        from story2d.audio import ffmpeg, duration; out.append('ffmpeg: ' + ffmpeg())
    except Exception as e: out.append(f'PROBLEM with ffmpeg: {e!r}  -> pip install imageio-ffmpeg')
    for m in ('numpy', 'pandas', 'docx', 'edge_tts', 'streamlit'):
        try: __import__(m); out.append(m + ' OK')
        except Exception as e: out.append(f'{m} MISSING ({e.__class__.__name__}) -> pip install -r requirements.txt')
    return out
if __name__ == '__main__':
    for st_ in (sys.stdout, sys.stderr):
        try: st_.reconfigure(encoding='utf-8', errors='replace')
        except Exception: pass
    print('\n'.join(main()))
