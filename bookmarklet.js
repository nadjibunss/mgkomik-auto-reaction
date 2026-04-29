(function(){
  if(window.__mgbot){ alert('Bot sudah jalan!'); return; }
  window.__mgbot = true;

  const BASE  = 'https://web.mgkomik.cc';
  const DELAY = 1500;
  const RXMAP = {upvote:1, funny:2, love:3};
  let stop = false;
  let stats = {komik:0, chapter:0, react:0, page:0};

  // UI Panel
  const panel = document.createElement('div');
  panel.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#16213e;color:#fff;z-index:999999;font-family:Arial;font-size:12px;padding:10px 12px;border-top:2px solid #e94560;max-height:50vh;overflow-y:auto;';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
      <b style="color:#e94560;">&#129302; MGKomik Bot</b>
      <div>
        <span id="__mgs" style="color:#f9c74f;font-size:11px;">Page:0 Komik:0 React:0</span>
        <button id="__mgstop" style="background:#e74c3c;color:#fff;border:none;padding:3px 9px;border-radius:5px;cursor:pointer;margin-left:6px;">Stop</button>
        <button id="__mgx" style="background:#444;color:#fff;border:none;padding:3px 7px;border-radius:5px;cursor:pointer;margin-left:3px;">X</button>
      </div>
    </div>
    <div id="__mgl" style="font-family:monospace;font-size:11px;line-height:1.7;"></div>
  `;
  document.body.appendChild(panel);
  document.getElementById('__mgstop').onclick = ()=>{ stop=true; log('[ STOP ]','#e74c3c'); };
  document.getElementById('__mgx').onclick = ()=>{ stop=true; panel.remove(); window.__mgbot=false; };

  function log(msg, c='#ccc'){
    const el=document.getElementById('__mgl'); if(!el) return;
    const d=document.createElement('div'); d.style.color=c; d.textContent=msg;
    el.appendChild(d); el.scrollTop=el.scrollHeight;
  }
  function upd(){
    const el=document.getElementById('__mgs');
    if(el) el.textContent=`Page:${stats.page} Komik:${stats.komik} Ch:${stats.chapter} React:${stats.react}`;
  }
  const sleep = ms => new Promise(r=>setTimeout(r,ms));
  function randRx(){ const k=Object.keys(RXMAP); return k[Math.floor(Math.random()*k.length)]; }

  async function getHTML(url){
    try{
      const r=await fetch(url,{credentials:'include'});
      if(!r.ok){log('  HTTP '+r.status,'#f47f7f');return null;}
      return await r.text();
    }catch(e){log('  ERR: '+e.message,'#f47f7f');return null;}
  }

  // Ambil komik dari 1 halaman listing
  async function getPageKomik(page){
    const url = page===1 ? BASE+'/komik/' : BASE+'/komik/?page='+page;
    log(`[PAGE ${page}] Ambil daftar...`, '#56cfe1');
    const html = await getHTML(url);
    if(!html) return null; // null = error
    const doc = new DOMParser().parseFromString(html,'text/html');
    const title = doc.title||'';
    log('  Title: '+title, '#aaa');
    if(/(just a moment|cloudflare)/i.test(title)){
      log('  CF block!','#f47f7f'); return null;
    }
    let links=[];
    const sels=['.bsx a','.bs a','.listupd a','.utao a','article a','.lds a','.anmt a','.lsx a'];
    for(const sel of sels){
      doc.querySelectorAll(sel).forEach(a=>{
        const h=a.href||'';
        if(h.includes('/komik/')&&!h.includes('/chapter')&&!h.endsWith('/komik/')&&!links.includes(h)) links.push(h);
      });
      if(links.length) break;
    }
    if(!links.length){
      doc.querySelectorAll('a[href]').forEach(a=>{
        const h=a.href||'';
        if(h.includes('/komik/')&&!h.includes('/chapter')&&!h.endsWith('/komik/')&&!links.includes(h)) links.push(h);
      });
    }
    if(!links.length) return []; // kosong = halaman habis
    log(`  ${links.length} komik ditemukan`, '#6fcf97');
    return links;
  }

  async function getChapters(url){
    const html=await getHTML(url); if(!html) return [];
    const doc=new DOMParser().parseFromString(html,'text/html');
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

  async function sendReaction(url, reaction){
    const html=await getHTML(url); if(!html) return;
    const doc=new DOMParser().parseFromString(html,'text/html');
    let pid=null;
    for(const attr of ['data-post-id','data-id','data-manga-id']){
      const el=doc.querySelector('['+attr+']');
      if(el){pid=el.getAttribute(attr);break;}
    }
    if(!pid) doc.querySelectorAll('script').forEach(sc=>{
      if(pid) return;
      const m=(sc.textContent||'').match(/["']?(?:post_id|postId)["']?[\s:=>'"]+([\d]{3,})/);
      if(m) pid=m[1];
    });
    if(!pid){const sl=doc.querySelector('link[rel="shortlink"]');if(sl){const m=sl.href.match(/p=(\d+)/);if(m)pid=m[1];}}
    if(!pid) pid=url.replace(/\/$/,'').split('/').pop();

    const rid=RXMAP[reaction]||1;
    const apis=[BASE+'/api/reaction',BASE+'/wp-json/manga/v1/reaction',BASE+'/wp-admin/admin-ajax.php'];
    for(const api of apis){
      try{
        const r=await fetch(api,{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest','Referer':url},
          body:JSON.stringify({post_id:pid,reaction:rid,action:'manga_reaction'})});
        if(r.status===200){
          const txt=await r.text();
          log(`    [OK] ${reaction} pid=${pid} ${txt.slice(0,50)}`,'#6fcf97');
          stats.react++; upd(); return;
        }
      }catch(e){}
    }
    log('    [FAIL] '+url.split('/').pop(),'#f47f7f');
  }

  // MAIN: page by page
  (async()=>{
    log('=== MGKomik Bot START ===','#56cfe1');
    let page=1;
    while(!stop){
      stats.page=page; upd();
      log(`\n====== PAGE ${page} ======`,'#e94560');

      const komikList = await getPageKomik(page);
      if(komikList===null){ log('Error ambil halaman, stop.','#f47f7f'); break; }
      if(komikList.length===0){ log('Halaman kosong, semua page selesai!','#6fcf97'); break; }

      // Proses setiap komik di page ini + semua chapter-nya
      for(let i=0; i<komikList.length && !stop; i++){
        const url=komikList[i];
        const name=url.replace(/\/$/,'').split('/').pop();
        stats.komik++; upd();
        log(`\n  [${i+1}/${komikList.length}] ${name}`,'#56cfe1');

        // Reaction halaman komik
        await sendReaction(url, randRx());
        await sleep(DELAY);

        // Ambil dan reaction semua chapter
        const chs=await getChapters(url);
        log(`    ${chs.length} chapter`,'#aaa');
        for(let j=0;j<chs.length&&!stop;j++){
          stats.chapter++; upd();
          const cname=chs[j].replace(/\/$/,'').split('/').pop();
          log(`    [Ch ${j+1}/${chs.length}] ${cname}`,'#aaa');
          await sendReaction(chs[j], randRx());
          await sleep(DELAY);
        }
      }

      log(`\n====== PAGE ${page} SELESAI ======`,'#6fcf97');
      page++;
      await sleep(2000);
    }
    log('\n=== SELESAI TOTAL ===','#6fcf97');
    log(`Komik:${stats.komik} Chapter:${stats.chapter} Reaction:${stats.react}`,'#f9c74f');
  })();

})();
