(function(){
  // Cegah double inject
  if(window.__mgbot) { alert('Bot sudah jalan!'); return; }
  window.__mgbot = true;

  const BASE = 'https://web.mgkomik.cc';
  const DELAY = 1500;
  const REACTIONS = {upvote:1, funny:2, love:3};
  let stop = false;
  let stats = {komik:0, chapter:0, react:0};

  // Buat UI panel
  const panel = document.createElement('div');
  panel.id = '__mgbot_panel';
  panel.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#16213e;color:#fff;z-index:999999;font-family:Arial;font-size:12px;padding:10px;border-top:2px solid #e94560;max-height:45vh;overflow-y:auto;';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <b style="color:#e94560;">&#129302; MGKomik Bot</b>
      <div>
        <span id="__mg_stats" style="color:#f9c74f;">Komik:0 Chapter:0 Reaction:0</span>
        &nbsp;
        <button id="__mg_stop" style="background:#e74c3c;color:white;border:none;padding:4px 10px;border-radius:6px;cursor:pointer;">Stop</button>
        <button id="__mg_close" style="background:#555;color:white;border:none;padding:4px 8px;border-radius:6px;cursor:pointer;margin-left:4px;">X</button>
      </div>
    </div>
    <div id="__mg_log" style="font-family:monospace;font-size:11px;line-height:1.7;"><span style="color:#f9c74f;">Memulai bot...</span></div>
  `;
  document.body.appendChild(panel);

  document.getElementById('__mg_stop').onclick = () => { stop = true; log('[ STOP ditekan ]','#e74c3c'); };
  document.getElementById('__mg_close').onclick = () => { stop=true; panel.remove(); window.__mgbot=false; };

  function log(msg, color='#ccc') {
    const el = document.getElementById('__mg_log');
    if (!el) return;
    const d = document.createElement('div');
    d.style.color = color;
    d.textContent = msg;
    el.appendChild(d);
    el.scrollTop = el.scrollHeight;
  }

  function updStats() {
    const el = document.getElementById('__mg_stats');
    if(el) el.textContent = `Komik:${stats.komik} Chapter:${stats.chapter} Reaction:${stats.react}`;
  }

  function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }
  function rand(obj){ const k=Object.keys(obj); return k[Math.floor(Math.random()*k.length)]; }

  async function getHTML(url) {
    try {
      const r = await fetch(url, {credentials:'include'});
      if(!r.ok){ log('  HTTP '+r.status+' '+url,'#f47f7f'); return null; }
      return await r.text();
    } catch(e){ log('  Err: '+e.message,'#f47f7f'); return null; }
  }

  async function getKomikList() {
    const list = [];
    let page = 1;
    while(!stop) {
      const url = page===1 ? BASE+'/komik/' : BASE+'/komik/?page='+page;
      log('[PAGE '+page+'] '+url, '#56cfe1');
      const html = await getHTML(url);
      if(!html) break;
      const doc = new DOMParser().parseFromString(html,'text/html');
      log('  Title: '+(doc.title||''), '#aaa');
      let links = [];
      const sels=['.bsx a','.bs a','.listupd a','.utao a','article a','.lds a','.anmt a','.lsx a'];
      for(const sel of sels){
        doc.querySelectorAll(sel).forEach(a=>{
          const h=a.href||'';
          if(h.includes('/komik/')&&!h.includes('/chapter')&&!h.endsWith('/komik/')&&!list.includes(h)&&!links.includes(h)) links.push(h);
        });
        if(links.length) break;
      }
      if(!links.length){
        doc.querySelectorAll('a[href]').forEach(a=>{
          const h=a.href||'';
          if(h.includes('/komik/')&&!h.includes('/chapter')&&!h.endsWith('/komik/')&&!list.includes(h)&&!links.includes(h)) links.push(h);
        });
      }
      if(!links.length){ log('  Halaman '+page+' kosong, selesai.','#f9c74f'); break; }
      log('  '+links.length+' komik ditemukan','#6fcf97');
      list.push(...links);
      page++;
      await sleep(1500);
    }
    return list;
  }

  async function getChapters(url) {
    const html = await getHTML(url);
    if(!html) return [];
    const doc = new DOMParser().parseFromString(html,'text/html');
    let chs=[];
    const sels=['#chapterlist a','.eplister a','.cl a','li.wp-manga-chapter a','a[href*="/chapter"]'];
    for(const sel of sels){
      doc.querySelectorAll(sel).forEach(a=>{
        const h=a.href||'';
        if(h.includes('/chapter')&&!chs.includes(h)) chs.push(h);
      });
      if(chs.length) break;
    }
    return chs.sort();
  }

  async function sendReaction(url, reaction) {
    const html = await getHTML(url);
    if(!html) return;
    const doc = new DOMParser().parseFromString(html,'text/html');
    let postId=null;
    for(const attr of ['data-post-id','data-id','data-manga-id']){
      const el=doc.querySelector('['+attr+']');
      if(el){postId=el.getAttribute(attr);break;}
    }
    if(!postId){
      doc.querySelectorAll('script').forEach(sc=>{
        if(postId) return;
        const m=(sc.textContent||'').match(/["']?(?:post_id|postId)["']?[\s:=>'"]+([\d]{3,})/);
        if(m) postId=m[1];
      });
    }
    if(!postId){
      const sl=doc.querySelector('link[rel="shortlink"]');
      if(sl){const m=sl.href.match(/p=(\d+)/);if(m)postId=m[1];}
    }
    if(!postId) postId=url.replace(/\/$/,'').split('/').pop();

    const rid=REACTIONS[reaction]||1;
    const apis=[BASE+'/api/reaction', BASE+'/wp-json/manga/v1/reaction', BASE+'/wp-admin/admin-ajax.php'];
    for(const api of apis){
      try{
        const r=await fetch(api,{
          method:'POST', credentials:'include',
          headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest','Referer':url},
          body:JSON.stringify({post_id:postId,reaction:rid,action:'manga_reaction'})
        });
        if(r.status===200){
          const txt=await r.text();
          log('  [OK] '+reaction+' pid='+postId+' '+txt.slice(0,50),'#6fcf97');
          stats.react++; updStats();
          return;
        }
      }catch(e){}
    }
    log('  [FAIL] '+url.split('/').pop(),'#f47f7f');
  }

  // Main
  (async()=>{
    log('Domain: '+location.hostname,'#f9c74f');
    log('Mengambil daftar komik...','#f9c74f');
    const komikList = await getKomikList();
    log('Total: '+komikList.length+' komik','#f9c74f');
    if(!komikList.length){ log('Tidak ada komik ditemukan!','#f47f7f'); return; }

    for(let i=0;i<komikList.length&&!stop;i++){
      const url=komikList[i];
      const name=url.replace(/\/$/,'').split('/').pop();
      stats.komik++; updStats();
      log('['+(i+1)+'/'+komikList.length+'] '+name,'#56cfe1');

      const r1=rand(REACTIONS);
      await sendReaction(url,r1);
      await sleep(DELAY);

      const chs=await getChapters(url);
      log('  Chapter: '+chs.length,'#aaa');
      for(let j=0;j<chs.length&&!stop;j++){
        stats.chapter++; updStats();
        const r2=rand(REACTIONS);
        log('  ['+(j+1)+'/'+chs.length+'] '+chs[j].split('/').pop()+' -> '+r2,'#aaa');
        await sendReaction(chs[j],r2);
        await sleep(DELAY);
      }
    }
    log('=== SELESAI! Komik:'+stats.komik+' Reaction:'+stats.react+' ===','#6fcf97');
  })();

})();
