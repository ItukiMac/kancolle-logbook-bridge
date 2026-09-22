async function send(m){return await chrome.runtime.sendMessage(m)}
function esc(s){return String(s??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")}
async function refresh(){
 const r=await send({type:"status"});
 const c=document.getElementById("cdp"),p=document.getElementById("plugin"),h=document.getElementById("captures");
 if(!r?.ok){c.innerHTML=`<span class="err">${esc(r?.error)}</span>`;return}
 const t=r.activeTab,s=r.activeState,ps=r.pluginState||{};
 if(!t?.isGame)c.innerHTML='<span class="muted">艦これのDMMタブを前面にしてください。</span>';
 else if(s?.attached)c.innerHTML=`<span class="ok">CDP接続中</span>\n取得件数: ${esc(s.captureCount||0)}\nエラー: ${esc(s.lastError||"なし")}`;
 else c.innerHTML=`<span class="err">CDP未接続</span>\n${esc(s?.lastError||"")}`;
 p.innerHTML=ps.status==="connected"
   ? `<span class="ok">connected</span>\n${esc(ps.lastHealth||"")}\n送信: ${esc(ps.sent||0)}`
   : `<span class="err">${esc(ps.status||"unknown")}</span>\nエラー: ${esc(ps.lastError||"なし")}`;
 if(!r.captures?.length){h.innerHTML='<div class="capture muted">まだ取得していません。</div>';return}
 h.innerHTML=r.captures.slice(0,20).map(x=>`<div class="capture">${esc(x.method)} ${esc(x.path)}<br>HTTP=${esc(x.httpStatus)} RESPONSE=${esc(x.responseBytes)}B POST=${esc(x.postDataBytes)}B SVDATA=${x.looksLikeSvdata?"YES":"NO"} SESSION=${esc(x.session)} DIRECT=${x.direct?"YES":"NO"}</div>`).join("");
}
document.getElementById("start").onclick=async()=>{const r=await send({type:"startActive"});if(!r?.ok)alert(r?.error);refresh()};
document.getElementById("stop").onclick=async()=>{await send({type:"stopActive"});refresh()};
document.getElementById("health").onclick=async()=>{await send({type:"health"});refresh()};
document.getElementById("clear").onclick=async()=>{await send({type:"clearCaptures"});refresh()};
refresh();
