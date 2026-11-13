import {Client} from '/Volumes/EXTERNAL/自媒体/工具验证/video-mcp-20261007/upstream/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from '/Volumes/EXTERNAL/自媒体/工具验证/video-mcp-20261007/upstream/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const [mode='tools',id,extra]=process.argv.slice(2);
if(!['tools','info','analyze','burst'].includes(mode))throw new Error('Unsupported read mode');
if(mode!=='tools'&&!/^\d{19}$/.test(id??''))throw new Error('Exact video ID required');
const source=id?path.join(root,'media',id+'.mp4'):null;
if(source&&!JSON.parse(readFileSync(path.join(root,'allowed-files.json'),'utf8')).includes(source))throw new Error('Source is not in exact research whitelist');
const dir=path.join(root,'evidence',id??'boundary');mkdirSync(dir,{recursive:true});
const output=path.join(dir,mode==='burst'?'burst-'+(extra??'0')+'.json':mode+'.json');
if(existsSync(output))throw new Error('Receipt exists; inspect it instead of overwriting or repeating');
const client=new Client({name:'ai1000-public-local-reader',version:'2.0.0'});
const transport=new StdioClientTransport({command:process.execPath,args:[path.join(root,'launch.mjs')],env:{PATH:'/usr/bin:/bin'},stderr:'pipe'});
try{
 await client.connect(transport);
 let result;
 if(mode==='tools')result=await client.listTools();
 else{
  const name={info:'video_info',analyze:'video_analyze',burst:'video_get_frame_burst'}[mode];
  const burstRequest=mode==='burst'?JSON.parse(readFileSync(path.join(dir,extra+'.request.json'),'utf8')):null;
  if(burstRequest&&Object.hasOwn(burstRequest,'source'))throw new Error('Burst request cannot override its video source');
  const args=mode==='info'?{source,response_format:'json'}:mode==='analyze'?{source,detail:'detailed',max_frames:30,mode:'interval',language:'zh',skip_ocr:true,inline_images:true,response_format:'json'}:{...burstRequest,source};
  result=await client.callTool({name,arguments:args},undefined,{timeout:600000});
 }
 writeFileSync(output,JSON.stringify(result,null,2));
 const s=result.structuredContent;
 console.log(JSON.stringify({success:!result.isError,receipt:output,info:s?.info??(mode==='info'?s:undefined),transcript:s?.transcript,frames:s?.frames,inlineCount:s?.inlineCount,warnings:s?.warnings,tools:mode==='tools'?result.tools:undefined},null,2));
 if(result.isError)process.exitCode=1;
}finally{await client.close();}
