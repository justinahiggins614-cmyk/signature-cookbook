/* The Signature Cookbook — shared client logic (ES5) */
"use strict";
function cbesc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function cbfetch(url){return fetch(url).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r})}

/* ---------- recipe data ---------- */
var CB = {idx:null, chunks:{}, stats:null};
function cbChunkOf(id){var n=parseInt(id.split("-")[2],10);return "rc-"+String(Math.ceil(n/100)).padStart(5,"0")}
function cbLoadIdx(){
  if(CB.idx) return Promise.resolve(CB.idx);
  return cbfetch("data/index/recipes.idx.json").then(function(r){return r.json()}).then(function(j){CB.idx=j;return j});
}
function cbGunzip(buf){
  if(typeof DecompressionStream==="undefined") return Promise.reject(new Error("no gzip"));
  var ds=new DecompressionStream("gzip");
  var stream=new Blob([buf]).stream().pipeThrough(ds);
  return new Response(stream).text();
}
function cbLoadChunk(cn){
  if(CB.chunks[cn]) return Promise.resolve(CB.chunks[cn]);
  return cbfetch("data/recipes/chunks/"+cn+".jsonl.gz").then(function(r){return r.arrayBuffer()})
    .then(cbGunzip).then(function(t){
      var out={},lines=t.split("\n");
      for(var i=0;i<lines.length;i++){if(!lines[i].trim())continue;
        try{var r=JSON.parse(lines[i]);out[r.id]=r}catch(e){}}
      CB.chunks[cn]=out;return out;
    });
}
function cbGetRecipe(id){
  var cn=cbChunkOf(id);
  return cbLoadChunk(cn).then(function(m){
    if(m[id]) return m[id];
    throw new Error("recipe not found");
  });
}

/* ---------- rendering ---------- */
function cbIngHTML(r){
  return r.ingredients.map(function(i){
    return "<li><b>"+cbesc(i.qty+(i.unit?" "+i.unit:""))+"</b> "+cbesc(i.item)+"</li>";
  }).join("");
}
function cbStepsHTML(r){
  return r.steps.map(function(s){return "<li>"+cbesc(s)+"</li>"}).join("");
}
function cbMeta(r){
  return '<p class="rmeta">⏱ '+r.total_min+' min ('+r.prep_min+' prep + '+r.cook_min+' cook) · 🍽 Serves '+r.servings+
    ' · <b>'+cbesc(r.difficulty)+'</b> · '+cbesc(r.chapter)+' → '+cbesc(r.section)+'</p>';
}
function cbRecipeHTML(r){
  return '<article class="recipe" id="recipe-'+r.id+'">'+
    '<h2>'+cbesc(r.name)+'</h2>'+
    '<p class="hint">'+r.id+' · original Signature recipe</p>'+
    cbMeta(r)+
    '<div class="rtools">'+
    '<button class="btn big" onclick="cbCook(\''+r.id+'\')">🍳 Cook mode</button>'+
    '<button class="btn sm" onclick="cbRead(\''+r.id+'\')">🔊 Read aloud</button>'+
    '<button class="btn sm ghost" onclick="cbStop()">⏹ Stop</button>'+
    '<button class="btn sm ghost" onclick="cbCopy(\''+r.id+'\')">📋 Copy</button>'+
    '<button class="btn sm ghost" onclick="cbDownload(\''+r.id+'\')">⬇ Download .txt</button>'+
    '</div>'+
    '<div class="rtools"><span class="hint">Scale: </span>'+
    '<button class="btn sm ghost" onclick="cbSetScale(\''+r.id+'\',0.5)">½×</button>'+
    '<button class="btn sm ghost" onclick="cbSetScale(\''+r.id+'\',1)">1×</button>'+
    '<button class="btn sm ghost" onclick="cbSetScale(\''+r.id+'\',2)">2×</button>'+
    '<button class="btn sm ghost" onclick="cbSetScale(\''+r.id+'\',3)">3×</button>'+
    ' <span class="hint" id="scaleNote-'+r.id+'"></span></div>'+
    '<h3>Ingredients</h3><ul class="ings" id="ings-'+r.id+'">'+cbIngHTML(r)+'</ul>'+
    '<h3>Steps</h3><ol class="steps">'+cbStepsHTML(r)+'</ol>'+
    '<div class="card" style="margin-top:14px"><h3>🤖 Ask the cooking AI</h3>'+
    '<p class="hint">Substitutions, timing, servings — answered from this recipe.</p>'+
    '<input type="text" id="aiq-'+r.id+'" placeholder="e.g. can I swap the butter?" aria-label="Ask the cooking AI" onkeydown="if(event.key===\'Enter\')cbAssist(\''+r.id+'\')">'+
    '<div style="margin-top:8px"><button class="btn sm" onclick="cbAssist(\''+r.id+'\')">Ask</button></div>'+
    '<div id="aio-'+r.id+'" style="margin-top:8px"></div></div>'+
    '<p class="hint">Free forever — collect every recipe, no account, no catch.</p>'+
    '</article>';
}
function cbRecipeText(r){
  var t=r.name+" ("+r.id+")\n"+r.chapter+" > "+r.section+"\n";
  t+="Time: "+r.total_min+" min | Serves "+r.servings+" | "+r.difficulty+"\n\nIngredients:\n";
  r.ingredients.forEach(function(i){t+="- "+i.qty+(i.unit?" "+i.unit:"")+" "+i.item+"\n"});
  t+="\nSteps:\n";
  r.steps.forEach(function(s,i){t+=(i+1)+". "+s+"\n"});
  return t;
}

/* ---------- read aloud: tiered TTS, one global controller ---------- */
(function(){
  if(window.__JAHREAD) return;
  var R={audios:[]};
  R.stopAll=function(){
    try{if(window.speechSynthesis)window.speechSynthesis.cancel()}catch(e){}
    try{if(window.responsiveVoice&&window.responsiveVoice.cancel)window.responsiveVoice.cancel()}catch(e){}
    for(var i=0;i<R.audios.length;i++){try{R.audios[i].pause()}catch(e){}}
    R.audios.length=0;
    var els=document.querySelectorAll("audio");
    for(var j=0;j<els.length;j++){try{els[j].pause()}catch(e){}}
  };
  window.__JAHREAD=R;
})();
var CB_TIERS=[
  function(t){return "https://code.responsivevoice.org/getvoice.php?t="+encodeURIComponent(t)+"&tl=en-US&sv=g2&vn=&pitch=0.5&rate=0.95"},
  function(t){return "https://translate.google.com/translate_tts?ie=UTF-8&q="+encodeURIComponent(t)+"&tl=en&client=tw-ob"},
  function(t){return "https://translate.googleapis.com/translate_tts?ie=UTF-8&q="+encodeURIComponent(t)+"&tl=en&client=tw-ob"}
];
var CB_RD={queue:[],stopped:true,timer:null};
function cbChunks(t){
  t=String(t).replace(/\s+/g," ").trim();var out=[],cur="";
  var parts=t.match(/[^.!?]+[.!?]+/g)||[t];
  for(var i=0;i<parts.length;i++){var s=parts[i].trim();if(!s)continue;
    if((cur+" "+s).length>170){if(cur)out.push(cur);cur=s}else cur=(cur?cur+" ":"")+s;
  }
  if(cur)out.push(cur);return out.slice(0,80);
}
function cbStop(){if(window.__JAHREAD)window.__JAHREAD.stopAll();CB_RD.stopped=true;CB_RD.queue=[];if(CB_RD.timer){clearTimeout(CB_RD.timer);CB_RD.timer=null}}
function cbPlayTier(chunk,tier,done){
  if(CB_RD.stopped||tier>=CB_TIERS.length){done(false);return}
  var a=new Audio();a.src=CB_TIERS[tier](chunk);var fin=false;
  function next(ok){if(fin)return;fin=true;
    if(CB_RD.timer){clearTimeout(CB_RD.timer);CB_RD.timer=null}
    try{a.pause()}catch(e){}done(ok)}
  a.onended=function(){next(true)};a.onerror=function(){next(false)};
  CB_RD.timer=setTimeout(function(){cbPlayTier(chunk,tier+1,done)},12000);
  var p=a.play();if(p&&p.catch)p.catch(function(){next(false)});
}
function cbNext(){
  if(CB_RD.stopped||!CB_RD.queue.length){cbStop();return}
  var chunk=CB_RD.queue.shift(),tier=0;
  (function attempt(){
    if(CB_RD.stopped)return;
    cbPlayTier(chunk,tier,function(ok){
      if(CB_RD.stopped)return;
      if(ok){setTimeout(cbNext,250)}else{tier++;if(tier<CB_TIERS.length)attempt();else setTimeout(cbNext,250)}
    });
  })();
}
function cbRead(id){
  cbStop();
  cbGetRecipe(id).then(function(r){
    CB_RD.queue=cbChunks(cbRecipeText(r));
    if(!CB_RD.queue.length)return;
    CB_RD.stopped=false;cbNext();
  }).catch(function(){});
}
function cbCopy(id){
  cbGetRecipe(id).then(function(r){
    var t=cbRecipeText(r);
    function note(msg){
      var d=document.createElement("div");d.className="copynote";d.textContent=msg;
      d.style.cssText="position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:#2f7a3d;color:#fff;padding:10px 18px;border-radius:999px;z-index:99999;font-weight:700";
      document.body.appendChild(d);setTimeout(function(){d.remove()},1800);
    }
    function fallback(){
      var ta=document.createElement("textarea");ta.value=t;document.body.appendChild(ta);
      ta.select();try{document.execCommand("copy");note("Recipe copied!")}catch(e){note("Copy failed — select the text manually.");}document.body.removeChild(ta);
    }
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(t).then(function(){note("Recipe copied!")},function(){fallback()});
    }else fallback();
  });
}
function cbDownload(id){
  cbGetRecipe(id).then(function(r){
    var blob=new Blob([cbRecipeText(r)],{type:"text/plain"});
    var a=document.createElement("a");
    a.href=URL.createObjectURL(blob);a.download=id+".txt";
    document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},2000);
  });
}

/* ---------- Ask the AI (honest keyword find over the archive) ---------- */
function cbAsk(q, outEl){
  q=String(q||"").trim().toLowerCase();
  if(!q){outEl.innerHTML='<p class="hint">Ask me about a dish, ingredient, or chapter — e.g. "chocolate", "soup", "chicken".</p>';return}
  cbLoadIdx().then(function(rows){
    var words=q.split(/\s+/);
    var hits=rows.filter(function(r){
      var blob=(r.n+" "+r.c+" "+r.s).toLowerCase();
      return words.every(function(w){return blob.indexOf(w)>=0});
    }).slice(0,12);
    if(!hits.length){
      outEl.innerHTML='<p>I couldn\'t find a recipe matching "<b>'+cbesc(q)+'</b>" in the archive yet — the cookbook grows every 2 hours, so check back. Try "chicken", "cake", "soup", or "salad".</p>';
      return;
    }
    var h='<p>Here\'s what I found for "<b>'+cbesc(q)+'</b>":</p><ul class="hits">';
    hits.forEach(function(r){
      h+='<li><a href="archive.html?recipe='+r.id+'">'+cbesc(r.n)+'</a> <span class="hint">'+cbesc(r.c)+' → '+cbesc(r.s)+'</span></li>';
    });
    outEl.innerHTML=h+'</ul>';
  }).catch(function(){
    outEl.innerHTML='<p class="hint">The archive index is still loading — try again in a moment.</p>';
  });
}

/* ---------- serving-size scaling ---------- */
function cbParseQty(q){
  q=String(q==null?"":q).trim();
  var m=q.match(/^(\d+)\s+(\d+)\/(\d+)$/);if(m)return parseInt(m[1],10)+parseInt(m[2],10)/parseInt(m[3],10);
  m=q.match(/^(\d+)\/(\d+)$/);if(m)return parseInt(m[1],10)/parseInt(m[2],10);
  var v=parseFloat(q);return isNaN(v)?null:v;
}
function cbFmtQty(v){
  if(v==null||isNaN(v))return "";
  var fr=[[0,""],[0.125,"1/8"],[0.25,"1/4"],[1/3,"1/3"],[0.5,"1/2"],[2/3,"2/3"],[0.75,"3/4"]];
  var whole=Math.floor(v+1e-6),rem=v-whole,best="",bd=1e9;
  for(var i=0;i<fr.length;i++){var d=Math.abs(rem-fr[i][0]);if(d<bd){bd=d;best=fr[i][1]}}
  if(bd>0.06)return String(Math.round(v*100)/100);
  if(whole===0)return best||"0";
  return best?whole+" "+best:String(whole);
}
function cbSetScale(id,f){
  cbGetRecipe(id).then(function(r){
    var ul=document.getElementById("ings-"+id);if(!ul)return;
    ul.innerHTML=r.ingredients.map(function(i){
      var v=cbParseQty(i.qty),q=(v==null)?i.qty:cbFmtQty(v*f);
      return "<li><b>"+cbesc(q+(i.unit?" "+i.unit:""))+"</b> "+cbesc(i.item)+"</li>";
    }).join("");
    var n=document.getElementById("scaleNote-"+id);
    if(n)n.textContent=(f===1)?"":"scaled \u00d7"+f+" (\u2248 serves "+Math.round(r.servings*f)+")";
  }).catch(function(){});
}

/* ---------- guided cook mode: one step at a time ---------- */
var CB_COOK={r:null,i:0};
function cbCookShell(){
  if(document.getElementById("cookMode"))return;
  var d=document.createElement("div");d.id="cookMode";
  d.style.cssText="position:fixed;inset:0;z-index:100000;background:#1c100a;display:none;overflow-y:auto";
  d.innerHTML='<div style="max-width:720px;margin:0 auto;padding:18px 14px 60px">'+
   '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px">'+
   '<b id="cookTitle" style="color:#f5b06e;font-size:1.1rem"></b>'+
   '<button class="btn sm ghost" onclick="cbCookClose()">\u2715 Exit</button></div>'+
   '<div id="cookStep" style="font-size:1.35rem;line-height:1.7;margin:22px 0;min-height:120px"></div>'+
   '<div id="cookTimers" style="margin:12px 0"></div>'+
   '<div style="display:flex;gap:12px;margin-top:18px">'+
   '<button class="btn big" id="cookPrev" onclick="cbCookGo(-1)" style="flex:1">\u2190 Back</button>'+
   '<button class="btn big" id="cookNext" onclick="cbCookGo(1)" style="flex:1">Next \u2192</button></div>'+
   '<div style="margin-top:14px"><button class="btn sm" onclick="cbCookRead()">🔊 Read this step</button> '+
   '<span class="hint" id="cookProg"></span></div>'+
   '<div id="cookTimerBox" style="margin-top:14px"></div></div>';
  document.body.appendChild(d);
}
function cbCook(id){
  cbGetRecipe(id).then(function(r){
    CB_COOK.r=r;CB_COOK.i=0;cbCookShell();cbCookRender();
    document.getElementById("cookMode").style.display="block";
    document.body.style.overflow="hidden";
    try{if(navigator.wakeLock&&navigator.wakeLock.request)navigator.wakeLock.request("screen").catch(function(){})}catch(e){}
  }).catch(function(){});
}
function cbCookClose(){
  var m=document.getElementById("cookMode");if(m)m.style.display="none";
  document.body.style.overflow="";cbStopCookTimer();cbStop();
}
function cbCookGo(n){
  var r=CB_COOK.r;if(!r)return;
  var ni=CB_COOK.i+n;
  if(ni>r.steps.length){cbCookClose();return}
  CB_COOK.i=Math.max(0,ni);cbCookRender();
}
function cbCookRender(){
  var r=CB_COOK.r,i=CB_COOK.i,M=r.steps.length;
  document.getElementById("cookTitle").textContent=r.name;
  var html="";
  if(i===0){
    html="<b>Before you start</b><br><span class='hint'>\u23f1 "+r.total_min+" min \u00b7 \U0001F37D Serves "+r.servings+" \u00b7 "+cbesc(r.difficulty)+"</span>"+
     "<ul class='ings'>"+r.ingredients.map(function(g){
       return "<li><b>"+cbesc(g.qty+(g.unit?" "+g.unit:""))+"</b> "+cbesc(g.item)+"</li>"}).join("")+"</ul>"+
     "<p class='hint'>Get everything out, then tap Next.</p>";
  }else{html=cbesc(r.steps[i-1])}
  document.getElementById("cookStep").innerHTML=html;
  document.getElementById("cookProg").textContent=(i===0?"Ready":"Step "+i+" of "+M);
  document.getElementById("cookPrev").disabled=(i===0);
  document.getElementById("cookNext").textContent=(i>=M?"\u2713 Done":"Next \u2192");
  var times=(i===0)?[]:cbParseTimes(r.steps[i-1]),th="";
  for(var ix=0;ix<times.length;ix++){
    th+='<button class="btn sm" data-tsec="'+times[ix].sec+'" data-tlabel="'+cbesc(times[ix].label)+'" onclick="cbStartTimer(this.getAttribute(\'data-tsec\'),this.getAttribute(\'data-tlabel\'))">\u23f2 '+cbesc(times[ix].label)+'</button> ';
  }
  document.getElementById("cookTimers").innerHTML=th;
  document.getElementById("cookTimerBox").innerHTML="";
  document.getElementById("cookMode").scrollTop=0;
}
function cbCookRead(){
  var r=CB_COOK.r;if(!r)return;
  cbStop();
  var t=(CB_COOK.i===0)?("Before you start. "+cbRecipeText(r).split("\n").slice(0,8).join(" ")):r.steps[CB_COOK.i-1];
  CB_RD.queue=cbChunks(t);if(!CB_RD.queue.length)return;
  CB_RD.stopped=false;cbNext();
}

/* ---------- step timers ---------- */
function cbParseTimes(s){
  var out=[],re=/(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)/gi,m;
  while((m=re.exec(String(s)))){var v=parseInt(m[1],10),u=m[2].toLowerCase();
    out.push({label:m[0],sec:u.charAt(0)==="h"?v*3600:(u.charAt(0)==="s"?v:v*60)});}
  return out;
}
var CB_TMR=null;
function cbStopCookTimer(){if(CB_TMR){clearInterval(CB_TMR.iv);CB_TMR=null}}
function cbStartTimer(sec,label){
  sec=parseInt(sec,10);cbStopCookTimer();
  var box=document.getElementById("cookTimerBox");if(!box)return;
  var end=Date.now()+sec*1000;
  box.innerHTML='<div class="card"><b>\u23f2 '+cbesc(label)+'</b><div id="cookT" style="font-size:2rem;font-weight:800"></div><button class="btn sm ghost" onclick="cbStopCookTimer();document.getElementById(\'cookTimerBox\').innerHTML=\'\'">Cancel</button></div>';
  function tick(){
    var left=Math.max(0,Math.round((end-Date.now())/1000));
    var el=document.getElementById("cookT");
    if(el)el.textContent=Math.floor(left/60)+":"+("0"+(left%60)).slice(-2);
    if(left<=0){cbStopCookTimer();cbBeep();
      var b2=document.getElementById("cookTimerBox");
      if(b2)b2.innerHTML='<div class="card"><b>\u23f2 Time&rsquo;s up!</b></div>';}
  }
  tick();CB_TMR={iv:setInterval(tick,1000)};
}
function cbBeep(){
  try{var C=window.AudioContext||window.webkitAudioContext;var c=new C();
    var o=c.createOscillator();o.connect(c.destination);o.frequency.value=880;
    o.start();o.stop(c.currentTime+0.6);}catch(e){}
}

/* ---------- AI cooking assistant (grounded in the recipe) ---------- */
var CB_SUBS={
 "butter":["olive oil","coconut oil","margarine"],
 "egg":["flax egg (1 tbsp ground flax + 3 tbsp water per egg)","1/4 cup mashed banana per egg (sweet recipes)"],
 "milk":["almond milk","oat milk"],
 "heavy cream":["coconut cream","evaporated milk"],
 "flour":["gluten-free flour blend, 1:1","almond flour (denser result)"],
 "sugar":["honey (use 3/4 as much)","maple syrup"],
 "baking powder":["1/4 tsp baking soda + 1/2 tsp cream of tartar per tsp"],
 "salt":["sea salt, 1:1","soy sauce (reduce other liquids)"],
 "olive oil":["avocado oil","vegetable oil"],
 "garlic":["1/8 tsp garlic powder per clove","shallot"],
 "onion":["shallot","1 tsp onion powder per onion"],
 "chicken":["turkey","firm tofu (press it first)","chickpeas"],
 "beef":["ground turkey","lentils","mushrooms"],
 "rice":["quinoa","cauliflower rice","couscous"],
 "pasta":["gluten-free pasta","zucchini noodles"],
 "cheese":["nutritional yeast (dairy-free)","vegan cheese"],
 "cream cheese":["Greek yogurt (tangier)","mascarpone"],
 "sour cream":["Greek yogurt"],
 "yogurt":["sour cream","buttermilk"],
 "honey":["maple syrup","agave"],
 "vanilla":["almond extract (use half)","maple syrup"],
 "lemon juice":["lime juice","white vinegar"],
 "bread crumbs":["crushed crackers","panko"],
 "mayonnaise":["Greek yogurt","mashed avocado"]
};
function cbAssist(id){
  var inp=document.getElementById("aiq-"+id),out=document.getElementById("aio-"+id);
  if(!inp||!out)return;
  cbGetRecipe(id).then(function(r){
    out.innerHTML="<p>"+cbAssistAnswer(r,inp.value)+"</p>";
  }).catch(function(){out.innerHTML='<p class="hint">Could not load the recipe.</p>'});
}
function cbAssistAnswer(r,q){
  q=String(q||"").trim().toLowerCase();
  if(!q)return "Ask me anything about this recipe \u2014 substitutions, timing, servings.";
  if(/how long|how much time|total time/.test(q))
    return "Total time is <b>"+r.total_min+" minutes</b> ("+r.prep_min+" prep + "+r.cook_min+" cook).";
  if(/serv|feed|how many|double|half|scale/.test(q))
    return "This serves <b>"+r.servings+"</b>. Use the \u00bd\u00d7 / 2\u00d7 / 3\u00d7 buttons above the ingredients to scale it.";
  var sm=q.match(/step\s*(\d+)/);
  if(sm){var si=parseInt(sm[1],10)-1;
    if(r.steps[si])return "<b>Step "+sm[1]+":</b> "+cbesc(r.steps[si]);
    return "This recipe has "+r.steps.length+" steps.";}
  function stem(w){w=String(w).toLowerCase();return w.replace(/(ies)$/,"y").replace(/(es|s)$/,"")}
  function findSub(qq){
    for(var k in CB_SUBS){
      if(qq.indexOf(k)>=0||q.indexOf(k)>=0)return k;
      var ks=stem(k);
      if(ks!==k&&(qq.indexOf(ks)>=0||q.indexOf(ks)>=0))return k;
    }
    return null;
  }
  var subq=q.replace(/substitut\w*|instead of|replace|swap|alternative|can i use|what can i use/g," ");
  if(/substitut|instead of|replace|swap|alternative|what can i use/.test(q)){
    var hit=findSub(subq);
    if(hit)return "For <b>"+cbesc(hit)+"</b> try: "+CB_SUBS[hit].map(function(x){return cbesc(x)}).join(", ")+".";
    return "Tell me which ingredient to swap \u2014 e.g. \u201cswap the butter\u201d \u2014 and I\u2019ll suggest options.";
  }
  for(var j=0;j<r.ingredients.length;j++){
    var it=r.ingredients[j].item.toLowerCase();
    if(q.indexOf(it)>=0||it.split(" ").some(function(w){return w.length>3&&(q.indexOf(w)>=0||q.indexOf(stem(w))>=0);})){
      var ing=r.ingredients[j];
      return "You need <b>"+cbesc(ing.qty+(ing.unit?" "+ing.unit:""))+" "+cbesc(ing.item)+"</b>.";
    }
  }
  var hit2=findSub(q);
  if(hit2)return "For <b>"+cbesc(hit2)+"</b> try: "+CB_SUBS[hit2].map(function(x){return cbesc(x)}).join(", ")+".";
  return "I answer from this recipe: ask about <b>times</b>, <b>servings</b>, <b>steps</b> (\u201cstep 3\u201d), <b>ingredients</b>, or <b>substitutions</b> (\u201cswap the butter\u201d).";
}
