/* KLB Quest Share: whitelisted quest data only; never saves api_token or raw packets. */
(function(root) {
"use strict";
const routes={"/kcsapi/api_get_member/questlist":"list","/kcsapi/api_req_quest/start":"start","/kcsapi/api_req_quest/stop":"stop","/kcsapi/api_req_quest/clearitemget":"clear"};
const safe=v=>String(v??"").replace(/<br\s*\/?\s*>/gi," ").replace(/<[^>]*>/g,"").replace(/[\u0000-\u001f\u007f]/g," ").replace(/\s+/g," ").trim().slice(0,800);
const integer=(v,fallback=null)=>v===null||v===undefined||v===""?fallback:(Number.isInteger(Number(v))&&Number(v)>=0?Number(v):fallback);
function parse(result) {
  if(!result||result.base64Encoded||typeof result.body!=="string") return null;
  try {
    const obj=JSON.parse(result.body.startsWith("svdata=")?result.body.slice(7):result.body);
    return Number(obj?.api_result)===1 ? (obj.api_data??{}) : null;
  } catch(_) { return null; }
}
function apply(previous,path,postData,result,at=new Date().toISOString()) {
  const kind=routes[path];if(!kind)return null;
  const data=parse(result);if(data===null)return null;
  const s=previous && typeof previous==="object" ? JSON.parse(JSON.stringify(previous)) : {};
  s.schema=1;s.quests=s.quests&&typeof s.quests==="object"?s.quests:{};
  s.pages=s.pages&&typeof s.pages==="object"?s.pages:{};
  s.changes=Array.isArray(s.changes)?s.changes:[];s.updatedAt=at;
  if(kind==="list"){
    if(!Array.isArray(data.api_list))return null;
    const params=new URLSearchParams(postData||"");
    const tab=safe(params.get("api_tab_id")||"all");
    const page=integer(params.get("api_page_no"),integer(data.api_disp_page,1));
    s.pages[tab+":"+page]={at,count:data.api_list.length};
    s.lastListAt=at;
    s.expectedAccepted=integer(data.api_exec_count,s.expectedAccepted??null);
    s.totalPages=integer(data.api_page_count,s.totalPages??null);
    for(const item of data.api_list){
      if(!item||typeof item!=="object")continue;
      const id=integer(item.api_no);if(!id||id>9999999)continue;
      const old=s.quests[id]||{};
      s.quests[id]={
        id,
        title:safe(item.api_title||old.title||("任務 #"+id)),
        detail:safe(item.api_detail||old.detail||""),
        category:integer(item.api_category,old.category??null),
        type:integer(item.api_type,old.type??null),
        state:integer(item.api_state,old.state??1),
        progress:integer(item.api_progress_flag,old.progress??0),
        seenAt:at
      };
    }
  }else{
    const id=integer(new URLSearchParams(postData||"").get("api_quest_id"));
    if(!id||id>9999999)return null;
    const old=s.quests[id]||{id,title:"任務 #"+id,detail:"",category:null,type:null,progress:0};
    const state=kind==="start"?2:kind==="stop"?1:0;
    s.quests[id]={...old,state,seenAt:at};
    s.changes.unshift({at,id,title:old.title,operation:kind});
    s.changes=s.changes.slice(0,20);
  }
  const records=Object.values(s.quests);
  if(records.length>400){
    records.sort((a,b)=>String(b.seenAt).localeCompare(String(a.seenAt)));
    s.quests=Object.fromEntries(records.slice(0,400).map(q=>[q.id,q]));
  }
  return s;
}
const isRelevant=path=>Object.prototype.hasOwnProperty.call(routes,path);
const active=s=>Object.values(s?.quests||{}).filter(q=>q.state===2||q.state===3).sort((a,b)=>a.id-b.id);
const observed=s=>Object.values(s?.quests||{}).filter(q=>q.state===1).sort((a,b)=>a.id-b.id);
const stamp=t=>t?new Date(t).toLocaleString("ja-JP"):"未取得";
function summary(s){
  const a=active(s), expected=s?.expectedAccepted??null;
  return {
    activeCount:a.length,completedCount:a.filter(q=>q.state===3).length,
    observedCount:Object.keys(s?.quests||{}).length,
    expectedAccepted:expected,pages:Object.keys(s?.pages||{}).length,
    updatedAt:s?.updatedAt||null,lastListAt:s?.lastListAt||null,
    uncertain:!s?.lastListAt||(expected!==null&&a.length!==expected)
  };
}
function formatPrompt(s,mode="active"){
  const a=active(s),stat=summary(s);
  const lines=[
    "艦これの任務状況を共有します。以下はゲーム通信から抽出した情報です。",
    "受注任務の優先順位と並行消化の候補を整理してください。期限付き・恒常的な入手手段がない報酬を優先し、資源・戦果中心は低優先。任務条件はwikiwiki.jp/kancolle/とzekamashi.netで確認してください。",
    "取得日時: "+stamp(s?.updatedAt)+" / 最終任務一覧取得: "+stamp(s?.lastListAt),
    "受注中・達成: "+a.length+"件 / 取得した任務ページ: "+stat.pages+"件 / API受注数: "+(stat.expectedAccepted??"不明"),
    "注意: 開いていない任務ページは取得されません。古い情報も残るため、未表示の任務を未受注と断定しないでください。50%/80%はゲームの段階表示です。",
    "","【受注中・達成（報酬未受領）】"
  ];
  if(!a.length)lines.push("（取得情報なし。ゲームの任務一覧を開いてください）");
  for(const q of a){
    const state=q.state===3?"達成（未受領）":"受注中";
    const progress=q.state===3?"達成":q.progress===2?"80%以上表示":q.progress===1?"50%以上表示":"進捗表示なし";
    lines.push("- #"+q.id+" "+q.title+"｜"+state+"｜"+progress+"｜確認:"+stamp(q.seenAt));
    if(mode==="all"&&q.detail)lines.push("  条件: "+q.detail);
  }
  if(mode==="all"){
    const other=observed(s);lines.push("","【表示済み未受注 "+other.length+"件】");
    for(const q of other){
      lines.push("- #"+q.id+" "+q.title+"｜確認:"+stamp(q.seenAt));
      if(q.detail)lines.push("  条件: "+q.detail);
    }
  }
  return lines.join("\n");
}
const api={isRelevant,apply,active,observed,summary,formatPrompt};
root.KLBQuestShare=api;
if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
