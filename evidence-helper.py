from pathlib import Path
import json, sys, shutil, hashlib, wave, statistics, re

root = Path(__file__).resolve().parent
mode, vid = sys.argv[1:3]
e = root / 'evidence' / vid
session = Path('/Users/USER/.codex/sessions/2026/10/07/rollout-2026-10-07T10-47-54-01a11442-a6d9-7413-88b3-191ce5cb037b.jsonl')

if mode == 'register':
    src = Path(sys.argv[3]); dst = root / 'media' / (vid + '.mp4')
    assert not dst.exists()
    shutil.copy2(src, dst); e.mkdir(exist_ok=True)
    p = root / 'allowed-files.json'; allowed = json.loads(p.read_text())
    allowed.append(str(dst)); p.write_text(json.dumps(allowed, ensure_ascii=False, indent=2))
    (e / 'source.json').write_text(json.dumps(dict(video_id=vid, url='https://www.douyin.com/video/'+vid,
        source_export=str(src), local_path=str(dst), sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
        bytes=dst.stat().st_size, date=sys.argv[4] if len(sys.argv)>4 else '2026-10-07'), indent=2))
elif mode == 'sheets':
    from PIL import Image, ImageDraw
    label = sys.argv[3] if len(sys.argv)>3 else 'samples'
    receipt = 'analyze.json' if label=='samples' else 'burst-'+label+'.json'
    fs = json.loads((e/receipt).read_text())['structuredContent']['frames']
    probe = Image.open(fs[0]['path'])
    cw,ch = (640,360) if probe.width > probe.height else (360,640)
    for k in range((len(fs)+5)//6):
        p=e/f'{label}-{k+1}.jpg'; assert not p.exists()
        canvas=Image.new('RGB',(cw*3,(ch+40)*2),'white'); draw=ImageDraw.Draw(canvas)
        for j,f in enumerate(fs[k*6:k*6+6]):
            im=Image.open(f['path']); im.thumbnail((cw,ch))
            x=j%3*cw; y=j//3*(ch+40); canvas.paste(im,(x,y+30))
            draw.text((x+5,y+5),f"index {f['index']} / {f['timeSec']} sec",fill='black')
        canvas.save(p)
    print('Created',len(fs),'frame contact sheets; viewing not yet recorded')
elif mode == 'coverage':
    # Caller must have inspected every frame before invoking this mode.
    actual_read = int(sys.argv[3]); handle = sys.argv[4]
    a=json.loads((e/'analyze.json').read_text())['structuredContent']
    src=json.loads((e/'source.json').read_text()); calls=[]; nav_lines=[]
    for ln,line in enumerate(session.read_text().splitlines(),1):
        p=json.loads(line).get('payload',{});t=p.get('arguments',p.get('input',''))
        if p.get('name')=='js' and isinstance(t,str) and handle in t and vid in t and any(op in t for op in ['.goto(', 'createBrowserTab(']): nav_lines.append(ln)
    source_start=max(nav_lines) if nav_lines else 0
    for ln,line in enumerate(session.read_text().splitlines(),1):
        p=json.loads(line).get('payload',{}); t=p.get('arguments',p.get('input',''))
        if p.get('type') not in ('function_call','custom_tool_call') or not isinstance(t,str): continue
        if (p.get('name')=='js' and handle in t and ln>=source_start) or (p.get('name')=='exec' and re.match(r'for\s*\(',t.lstrip()) and 'view_image' in t and vid+'/' in t):
            calls.append(dict(call_id=p.get('call_id'),input_jsonl_line=ln,tool=p.get('name')))
    matches=[]
    for x in (root/'cache/audio').glob('*/transcript.json'):
        tr=json.loads(x.read_text())
        if tr.get('segments') == a['transcript']['segments'] or (tr.get('fullText') == a['transcript'].get('fullText') and tr.get('segments',[])[:len(a['transcript']['segments'])] == a['transcript']['segments']): matches.append(x.parent/'audio.wav')
    assert len(matches)==1, 'Require exact cached transcript match for audio provenance'
    with wave.open(str(matches[0])) as w:
        audio=dict(path=str(matches[0]),rate=w.getframerate(),channels=w.getnchannels(),samples=w.getnframes(),duration_sec=w.getnframes()/w.getframerate(),full_track_extraction=True)
    fs=[dict(f,set='interval',actually_read=True,read_via=str(e/f"samples-{f['index']//6+1}.jpg")) for f in a['frames']]
    for p in sorted(e.glob('burst-*.json')):
        label=p.stem.removeprefix('burst-')
        fs += [dict(f,set=label,actually_read=True,read_via=str(e/f"{label}-{f['index']//6+1}.jpg")) for f in json.loads(p.read_text())['structuredContent']['frames']]
    assert len(fs)==actual_read
    src.update(source_session=str(session),browser_calls=[x for x in calls if x['tool']=='js'])
    (e/'source.json').write_text(json.dumps(src,ensure_ascii=False,indent=2))
    cov=dict(video_id=vid,standard='V2',status='SUBMITTED_PENDING_PMO',source=src,info=a['info'],audio=audio,asr=a['transcript'],
        asr_full_text_actually_read=True,asr_tail_unlabelled_sec=round(a['info']['durationSec']-a['transcript']['segments'][-1]['end'],4),
        asr_tail_silence='UNKNOWN',frames_generated=len(fs),frames_actually_read=actual_read,frames=fs,
        sampling_interval_sec=round(a['frames'][1]['timeSec']-a['frames'][0]['timeSec'],6),source_and_image_read_calls=calls,direct_complete_audiovisual=False,
        original_media_sha_unchanged=hashlib.sha256(Path(src['local_path']).read_bytes()).hexdigest()==src['sha256'],warnings=a['warnings'])
    assert cov['original_media_sha_unchanged']
    (e/'coverage.json').write_text(json.dumps(cov,ensure_ascii=False,indent=2))
    print(json.dumps(dict(video_id=vid,frames=actual_read,audio=audio,read_calls=len(calls))))
else:
    raise ValueError('Unsupported mode')
