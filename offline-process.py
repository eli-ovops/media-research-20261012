from pathlib import Path
import json,subprocess
p=Path(__file__).parent;vid='7694280596605052005';e=p/'evidence'/vid
node='/Users/USER/.local/nodejs/node-v22.16.0-darwin-arm64/bin/node'
for mode in ['info','analyze']:
 with (e/(mode+'.log')).open('w') as log:subprocess.run([node,str(p/'read-public-video.mjs'),mode,vid],stdout=log,stderr=log,check=True)
a=json.loads((e/'analyze.json').read_text())['structuredContent'];duration=a['info']['durationSec']
(e/'fullspan.request.json').write_text(json.dumps({'start_sec':0,'end_sec':duration-.2,'count':30,'inline_images':False,'response_format':'json'}))
with (e/'burst-fullspan.log').open('w') as log:subprocess.run([node,str(p/'read-public-video.mjs'),'burst',vid,'fullspan'],stdout=log,stderr=log,check=True)
subprocess.run(['/Users/USER/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(p/'evidence-helper.py'),'sheets',vid,'fullspan'],check=True)
print('offline complete, read required')
