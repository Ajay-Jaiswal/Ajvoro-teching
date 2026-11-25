"""Story2D Studio - text + duration -> 2D story / teaching video.  Run:  streamlit run app.py"""
import json, os, subprocess, sys, time, shutil, uuid
from pathlib import Path
import streamlit as st

import inspect
ROOT = Path(__file__).resolve().parent
WIDE = dict(width='stretch') if 'width' in inspect.signature(st.button).parameters else dict(use_container_width=True)
sys.path.insert(0, str(ROOT))
from story2d import planner
from story2d.art import THEMES
from story2d.audio import VOICES

OUT = ROOT / 'output'; OUT.mkdir(exist_ok=True)
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')


def read_pg(pf):
    try: return json.loads(Path(pf).read_text(encoding='utf-8'))
    except Exception: return None
st.set_page_config(page_title='Story2D Studio', page_icon='🎬', layout='wide')
S = st.session_state
for k, v in dict(scenes=[], result=None, script='', target=None).items(): S.setdefault(k, v)

st.title('🎬 Story2D Studio')
st.caption('टेक्स्ट + समय डालिए → 2D कहानी / टीचिंग वीडियो पाइए.  पूरी तरह ऑफ़लाइन, कोई AI मॉडल नहीं - 8 GB RAM में आराम से चलता है.')

with st.sidebar:
    st.header('⚙️ Settings')
    mode = st.radio('Video type', ['Story', 'Teaching'], horizontal=True, help='Story = characters और बातचीत ज़्यादा, Teaching = icons, lists, tables ज़्यादा')
    theme = st.selectbox('Look (theme)', list(THEMES))
    aspect = st.radio('Format', ['16:9', '9:16'], horizontal=True, format_func=lambda x: 'YouTube 16:9' if x == '16:9' else 'Shorts/Reels 9:16')
    res = st.select_slider('Quality', ['480p', '720p', '1080p'], value='720p', help='480p सबसे तेज़ और सबसे कम RAM')
    fps = st.select_slider('Frames per second', [12, 15, 24], value=15)
    captions = st.checkbox('Hindi/English captions on video', True)
    wm = st.text_input('Watermark text (optional)', '')
    font = st.text_input('Font name (optional)', '', help='खाली छोड़ें: Nirmala UI / Noto Sans Devanagari अपने-आप चुना जाएगा')
    with st.expander('🩺 Diagnose (अगर कुछ न चले)'):
        if st.button('Run self-check'):
            r = subprocess.run([sys.executable, '-m', 'story2d.selfcheck'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV, timeout=120)
            st.code(r.stdout + r.stderr)

tabs = st.tabs(['1️⃣ Script', '2️⃣ Scenes', '3️⃣ Voice & Music', '4️⃣ Create video'])

# ---------------------------------------------------------------- 1 script
with tabs[0]:
    c1, c2 = st.columns([3, 2])
    with c1:
        up = st.file_uploader('Script file (.txt / .docx)', type=['txt', 'docx'])
        if up is not None and S.get('_up') != up.name + str(up.size):
            S.script = planner.read_script(up.name, up.getvalue()); S['_up'] = up.name + str(up.size)
        b1, b2 = st.columns(2)
        if b1.button('📖 Sample: Hindi teaching'): S.script = (ROOT / 'examples/sample_teaching_hi.txt').read_text(encoding='utf-8'); S.mode_hint = 'Teaching'
        if b2.button('📖 Sample: English story'): S.script = (ROOT / 'examples/sample_story_en.txt').read_text(encoding='utf-8')
        S.script = st.text_area('Script / कहानी या पाठ यहाँ लिखें', S.script, height=330)
        st.caption(f'{len(S.script)} characters')
    with c2:
        st.subheader('Time / अवधि')
        natural = st.checkbox('Natural speaking speed (समय अपने-आप)', False)
        m = st.number_input('Minutes', 0, 180, 2, disabled=natural); sec = st.number_input('Seconds', 0, 59, 0, disabled=natural)
        target = None if natural else int(m * 60 + sec)
        avg = st.slider('Average scene length (sec)', 8, 45, 18, help='छोटा = ज़्यादा scenes और तेज़ बदलाव')
        blank = st.selectbox('Blank line = new scene?', ['Auto', 'Yes', 'No'])
        st.subheader('Title / Outro cards')
        ttl = st.text_input('Opening title (optional)', ''); sub = st.text_input('Subtitle (optional)', '')
        outro = st.checkbox('Add Like/Subscribe outro', False)
        with st.expander('📝 Script tips (markup)'):
            st.markdown('''
- खाली लाइन = नया scene (Auto mode में लंबे scripts अपने-आप बँटते हैं)
- `# शीर्षक` → उस scene का heading
- `[list]`, `[steps]`, `[compare]`, `[stat]`, `[timeline]`, `[question]`, `[bars]`, `[quote]`, `[title]`, `[outro]` → template खुद चुनें
- `[compare] बायाँ: बात1; बात2 | दायाँ: बात1; बात2`
- `[bars] नई नौकरियाँ: 170; खत्म: 92`
- `रवि: ...` / `मीरा: ...` लगातार लाइनें → बातचीत (dialogue)
- `- बुलेट` या `1. चरण` → list / steps अपने-आप
- साल (1950, 1997, 2022...) 3 से ज़्यादा हों → timeline; `53%`, `170 मिलियन` → बड़े आँकड़े
''')
    if st.button('✨ Plan scenes', type='primary', **WIDE):
        if len(S.script.strip()) < 20: st.error('पहले script डालें')
        else:
            sc = planner.parse(S.script, mode, avg, blank_break={'Auto': 'auto', 'Yes': True, 'No': False}[blank])
            planner.allocate(sc, target)
            if ttl.strip(): sc.insert(0, planner.title_card(ttl.strip(), sub.strip())); planner.allocate(sc, target) if target else None
            if outro: sc.append(planner.outro_card())
            S.scenes, S.target, S.result = sc, target, None
            st.success(f'{len(sc)} scenes बने - "2️⃣ Scenes" टैब में देखें / बदलें')

# ---------------------------------------------------------------- 2 scenes
with tabs[1]:
    sc = S.scenes
    if not sc: st.info('पहले "1️⃣ Script" टैब में Plan scenes दबाएँ')
    else:
        tot = sum(s['secs'] for s in sc)
        st.write(f'**{len(sc)} scenes · अनुमानित अवधि {int(tot // 60)}:{int(tot % 60):02d}**' + (f' (लक्ष्य {int(S.target // 60)}:{int(S.target % 60):02d})' if S.target else ''))
        import pandas as pd
        df = pd.DataFrame([dict(No=i + 1, template=s['tpl'], title=s.get('title', ''), secs=round(s['secs'], 1), text=s['text']) for i, s in enumerate(sc)])
        ed = st.data_editor(df, **WIDE, height=380, hide_index=True, disabled=['No'], num_rows='fixed', key='ed',
                            column_config=dict(template=st.column_config.SelectboxColumn(options=planner.TEMPLATES, required=True), secs=st.column_config.NumberColumn(min_value=2.0, max_value=300.0, step=0.5), text=st.column_config.TextColumn(width='large')))
        changed = False
        for i, row in ed.iterrows():
            s = sc[i]
            if row.template != s['tpl'] or row.text != s['text'] or row.title != s.get('title', ''):
                s['tpl'] = row.template; s['text'] = row.text; s['lines'] = [row.text]; s['title'] = row.title; s['chars'] = len(row.text); planner.payload(s); changed = True
            if abs(float(row.secs) - s['secs']) > 1e-6: s['secs'] = float(row.secs); changed = True
        b1, b2, b3 = st.columns(3)
        if b1.button('⏱ Fit all scenes to target time') and S.target: planner.allocate(sc, S.target); st.rerun()
        if b2.button('🗑 Delete last scene') and len(sc) > 1: sc.pop(); st.rerun()
        if b3.button('➕ Add outro card'): sc.append(planner.outro_card()); st.rerun()
        st.divider(); p1, p2 = st.columns([1, 2])
        with p1:
            idx = st.number_input('Preview scene #', 1, len(sc), 1) - 1; frac = st.slider('Moment in scene', 0.1, 1.0, 0.8)
            if st.button('👁 Preview scene'):
                wd = OUT / ('prev_' + uuid.uuid4().hex[:6]); wd.mkdir(); job = dict(scenes=sc, settings=dict(theme=theme, captions=captions, font=font or None, watermark=wm, aspect='16:9'), preview=dict(index=int(idx), frac=frac), workdir=str(wd))
                (wd / 'job.json').write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
                r = subprocess.run([sys.executable, '-m', 'story2d.job', str(wd / 'job.json')], cwd=ROOT, timeout=180, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV)
                S.prev = str(wd / 'preview.png')
                if not Path(S.prev).exists(): st.error('Preview नहीं बना'); st.code((r.stderr or '') + str((read_pg(wd / 'progress.json') or {}).get('trace', '')))
        with p2:
            if S.get('prev') and Path(S.prev).exists(): st.image(S.prev, **WIDE)

# ---------------------------------------------------------------- 3 voice
with tabs[2]:
    vm = st.radio('Voice', ['No voice (captions + music)', 'Upload my voiceover', 'Generate voice (Edge TTS - free, internet चाहिए)'])
    au = dict(mode='none')
    if vm.startswith('Upload'):
        f = st.file_uploader('Voiceover audio (mp3/wav/m4a)', type=['mp3', 'wav', 'm4a', 'aac', 'ogg'])
        sync = st.checkbox('Scenes को आवाज़ के pauses से sync करें (सुझाया गया)', True)
        st.caption('वीडियो की कुल अवधि = आपकी आवाज़ की अवधि. आप अपने Hindi TTS ऐप से बनी आवाज़ यहाँ डाल सकते हैं.')
        au = dict(mode='upload', sync=sync, file=f)
    elif vm.startswith('Generate'):
        vc = st.selectbox('Voice', list(VOICES)); rate = st.slider('Speed (%)', -30, 40, 0); fit = st.checkbox('Target time के अनुसार speed अपने-आप सेट करें', True)
        st.caption('Microsoft Edge की मुफ़्त आवाज़ें इस्तेमाल होती हैं (pip install edge-tts). पहली बार internet ज़रूरी है.')
        au = dict(mode='tts', voice=VOICES[vc], rate=rate, fit=fit)
    mus = st.checkbox('Soft background music', True); mv = st.slider('Music volume', 0.05, 0.6, 0.2)
    au.update(music=mus, music_vol=mv); S.au = au

# ---------------------------------------------------------------- 4 create
with tabs[3]:
    sc = S.scenes
    if not sc: st.info('पहले scenes बनाएँ')
    else:
        tot = sum(s['secs'] for s in sc); fr = int(tot * fps)
        st.write(f'**{len(sc)} scenes · ~{int(tot // 60)}:{int(tot % 60):02d} · {res} · {fps} fps · लगभग {fr:,} frames**')
        st.caption('अनुमानित render समय: आम laptop पर लगभग 0.3×–1× वीडियो अवधि (480p सबसे तेज़). RAM: ~300-500 MB.')
        if st.button('🎬 Create video', type='primary', **WIDE):
            wd = OUT / ('job_' + time.strftime('%H%M%S') + uuid.uuid4().hex[:4]); wd.mkdir(); au = dict(S.get('au', dict(mode='none')))
            f = au.pop('file', None)
            if au['mode'] == 'upload':
                if f is None: st.error('आवाज़ फ़ाइल डालें'); st.stop()
                p = wd / ('voice_in' + Path(f.name).suffix); p.write_bytes(f.getvalue()); au['path'] = str(p)
            name = (sc[0]['title'] if sc[0]['tpl'] == 'title' and sc[0]['title'] else 'story2d_video').replace(' ', '_')[:30]
            job = dict(scenes=sc, settings=dict(theme=theme, res=res, fps=fps, aspect=aspect, captions=captions, font=font or None, watermark=wm), audio=au, target=S.target,
                       out=str(wd / f'{name}.mp4'), workdir=str(wd))
            (wd / 'job.json').write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
            logf = open(wd / 'job.log', 'wb'); proc = subprocess.Popen([sys.executable, '-m', 'story2d.job', str(wd / 'job.json')], cwd=ROOT, env=ENV, stdout=logf, stderr=subprocess.STDOUT)
            bar = st.progress(0); msg = st.empty(); t0 = time.time(); pf = wd / 'progress.json'
            while proc.poll() is None:
                pg = read_pg(pf) or dict(pct=0, msg='शुरू हो रहा है...')
                bar.progress(min(100, int(pg.get('pct', 0))) / 100); msg.write(f"{pg.get('msg', '')}  ·  ⏱ {int(time.time() - t0)}s"); time.sleep(1.0)
            logf.close(); pg = read_pg(pf)
            if pg is None:
                log = (wd / 'job.log').read_text(encoding='utf-8', errors='replace')[-3000:]
                pg = dict(phase='error', msg='Render process बीच में बंद हो गया (नीचे log देखें, या sidebar में Diagnose चलाएँ)', trace=log)
            if pg.get('phase') == 'done': bar.progress(1.0); S.result = pg['result']; msg.success('✅ वीडियो तैयार!')
            else: st.error(f"Error: {pg.get('msg')}"); st.code(pg.get('trace', ''))
        r = S.result
        if r and Path(r['video']).exists():
            st.video(r['video']); d1, d2 = st.columns(2)
            d1.download_button('⬇️ Download MP4', Path(r['video']).read_bytes(), file_name=Path(r['video']).name, mime='video/mp4', **WIDE)
            d2.download_button('⬇️ Download subtitles (.srt)', Path(r['srt']).read_bytes(), file_name=Path(r['srt']).name, **WIDE)
            st.caption(f"Saved in: {r['video']}")
