import {readFileSync,realpathSync,lstatSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const upstreamRoot='/Volumes/EXTERNAL/自媒体/工具验证/video-mcp-20261007';
const mediaRoot=path.resolve(root,'media');
const allowed=JSON.parse(readFileSync(path.join(root,'allowed-files.json'),'utf8'));
if(!Array.isArray(allowed)||allowed.some(p=>typeof p!=='string'||!path.isAbsolute(p)))throw new Error('Exact absolute public media paths required');
for(const p of allowed){
  if(lstatSync(p).isSymbolicLink()||!lstatSync(p).isFile())throw new Error('Regular media files only');
  const rel=path.relative(mediaRoot,realpathSync(p));
  if(rel.startsWith('..')||path.isAbsolute(rel)||!rel)throw new Error('Public research media root only');
}
mkdirSync(path.join(root,'cache'),{recursive:true});
process.env.VIDEO_MCP_WORK_DIR=path.join(root,'cache');
process.env.VIDEO_MCP_ALLOWED_FILES=JSON.stringify(allowed);
process.env.VIDEO_MCP_DISABLE_OCR='1';
process.env.VIDEO_MCP_WRITE_SIDECARS='0';
process.env.FFMPEG_BIN='/Users/USER/.local/bin/ffmpeg';
process.env.FFPROBE_BIN=path.join(upstreamRoot,'bin','avprobe');
process.env.WHISPER_CPP_BIN=path.join(upstreamRoot,'whisper.cpp','build','bin','whisper-cli');
process.env.WHISPER_CPP_MODEL=path.join(upstreamRoot,'models','ggml-base.bin');
process.env.WHISPER_LANGUAGE='zh';
delete process.env.OPENAI_API_KEY;
delete process.env.YTDLP_COOKIES;
delete process.env.YTDLP_COOKIES_FROM_BROWSER;
globalThis.fetch=async()=>{throw new Error('Network access disabled in this local-only research MCP');};
const {default:start}=await import(path.join(upstreamRoot,'upstream','dist','serve.js'));
await start();
