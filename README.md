# 🎬 Story2D Studio

Text + time → 2D story / teaching video (MP4 + subtitles). Hindi और English दोनों.
No AI model, no GPU, no internet needed (internet सिर्फ़ तब, जब आप "Edge TTS" आवाज़ चुनें).

## Install (एक बार)
1. Python 3.10 – 3.12 install करें (python.org, "Add to PATH" tick करें).
2. **Windows:** `run_windows.bat` पर double-click.  **Mac/Linux:** `./run_mac_linux.sh`
   (पहली बार लगभग 300 MB packages download होते हैं - बाद में सीधे खुलता है.)
3. Browser में app खुलेगा: http://localhost:8501

## Use
1. **Script** टैब: text paste करें या .txt/.docx upload करें → समय (minutes:seconds) चुनें → **Plan scenes**
2. **Scenes** टैब: हर scene का template / title / seconds / text बदल सकते हैं, Preview देख सकते हैं
3. **Voice & Music**: No voice / अपनी voiceover upload / Edge TTS से आवाज़ generate
4. **Create video** → MP4 और .srt download

## Script markup (optional)
```
# शीर्षक                      -> scene heading
[list] [steps] [compare] [stat] [timeline] [question] [bars] [quote] [title] [outro]
[compare] बायाँ: बात1; बात2 | दायाँ: बात1; बात2
[bars] नई नौकरियाँ: 170; खत्म: 92
रवि: ...   मीरा: ...          -> बातचीत (dialogue)
- बुलेट  /  1. चरण            -> list / steps
[outro] धन्यवाद! | Like · Share · Subscribe
```
बिना markup के भी चलता है: app खुद साल (timeline), आँकड़े (53%, 170 मिलियन), सवाल (?), "बनाम" (compare), सूची आदि पहचानता है.

## 8 GB RAM
Frames सीधे ffmpeg में stream होते हैं, इसलिए RAM ~200–500 MB रहती है (19 मिनट का वीडियो भी). Render अलग process में चलता है, ख़त्म होते ही RAM वापस. तेज़ करने के लिए 480p + 12 fps चुनें; YouTube के लिए 720p + 15/24 fps.

## Voice से exact sync
* **Upload voiceover**: वीडियो की अवधि = आपकी audio की अवधि; "pauses से sync" scene बदलाव आवाज़ की चुप्पी पर रखता है.
* **Edge TTS**: हर scene की आवाज़ अलग बनती है, इसलिए picture और आवाज़ अपने-आप बराबर रहते हैं (internet चाहिए).

## Fonts
Windows पर Nirmala UI अपने-आप चुना जाता है, वरना bundled FreeSans (fonts/ folder). अपना font चाहें तो sidebar में नाम लिखें.

## Command line
`python -m story2d.cli script.txt --duration 300 --mode Teaching --theme "Classroom (light)" --res 720p --out video.mp4`

## अगर कोई error आए
* Sidebar → **🩺 Diagnose → Run self-check** चलाएँ: यह बताता है Qt, ffmpeg, font और packages ठीक हैं या नहीं.
* हर render की `output/job_.../job.log` फ़ाइल में पूरा error लिखा होता है.
* Python **3.11 या 3.12** सबसे सुरक्षित है (बहुत नए Python पर कुछ packages के wheels देर से आते हैं).
