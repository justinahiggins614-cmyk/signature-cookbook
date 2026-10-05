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
    '<button class="btn sm" onclick="cbRead(\''+r.id+'\')">🔊 Read aloud</button>'+
    '<button class="btn sm ghost" onclick="cbStop()">⏹ Stop</button>'+
    '<button class="btn sm ghost" onclick="cbCopy(\''+r.id+'\')">📋 Copy</button>'+
    '<button class="btn sm ghost" onclick="cbDownload(\''+r.id+'\')">⬇ Download .txt</button>'+
    '</div>'+
    '<h3>Ingredients</h3><ul class="ings">'+cbIngHTML(r)+'</ul>'+
    '<h3>Steps</h3><ol class="steps">'+cbStepsHTML(r)+'</ol>'+
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
  t.split(/(?<=[.!?])\s+/).forEach(function(s){
    if((cur+" "+s).length>170){if(cur)out.push(cur);cur=s}else cur=(cur?cur+" ":"")+s;
  });
  if(cur)out.push(cur);return out.slice(0,80);
}
function cbStop(){if(window.__JAHREAD)window.__JAHREAD.stopAll();CB_RD.stopped=true;CB_RD.queue=[];if(CB_RD.timer){clearTimeout(CB_RD.timer);CB_RD.timer=null}}
function cbPlayTier(chunk,tier,done){
  if(CB_RD.stopped||tier>=CB_TIERS.length){done(false);return}
  var a=new Audio();a.src=CB_TIERS[tier](chunk);var fin=false;
  function next(ok){if(fin)return;fin=true;try{a.pause()}catch(e){}done(ok)}
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
