'use strict';
const $ = (s, root = document) => root.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const main = $('#main'), modal = $('#modal'), modalBody = $('#modal-body');
let token = sessionStorage.getItem('northstar-demo-token'), boot, page = '', routeVersion = 0;
let conversation = [], sending = false, currentRecords = [], recordPage = 1, recordQuery = '', articles = [];
let toastTimer, ticketKey, draftWorkflow = null, activeCase = null, pendingMessage = null;
const labels = {overview:'Overview',assistant:'Support assistant',tickets:'My tickets',knowledge:'Knowledge center',status:'Service status',records:'Sample service desk'};
const scenarios = ['I cannot connect to VPN', 'I need password reset assistance', 'How do I request new software?'];
function toast(text){ $('#toast').textContent = text; $('#toast').classList.add('visible'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),5000); }
async function api(path, options={}){
  const headers = {...(options.body ? {'Content-Type':'application/json'} : {}), ...(token ? {'X-Demo-Token':token}:{}), ...options.headers};
  let response;
  try { response=await fetch('/api'+path,{...options,headers,signal:AbortSignal.timeout(45000)}); }
  catch { throw new Error('The service could not be reached. On free hosting it may be waking up; please retry shortly.'); }
  let data; try { data=await response.json(); } catch { throw new Error('The service returned an unexpected response. Please retry.'); }
  if(!response.ok){
    if(response.status===401){token=null;sessionStorage.removeItem('northstar-demo-token');}
    throw new Error(typeof data.detail==='string' ? data.detail : 'Please check the fields and try again.');
  }
  return data;
}
function badge(status){const cls = /degraded|waiting|investigating|high/i.test(status)?'warn':/progress|medium/i.test(status)?'purple':/open|low/i.test(status)?'blue':/operational|resolved|completed/i.test(status)?'':'neutral'; return '<span class="badge '+cls+'">'+esc(status)+'</span>';}
function heading(eyebrow,title,description,action=''){return '<div class="page-heading"><div><div class="eyebrow">'+esc(eyebrow)+'</div><h1>'+esc(title)+'</h1><p>'+esc(description)+'</p></div>'+action+'</div>';}
function stamp(value){return new Date(value).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'});}
function openModal(html){modalBody.innerHTML=html;if(!modal.open)modal.showModal();}
function closeModal(){modal.close();}
function ticketButton(label='New ticket'){return '<button class="button primary" data-new-ticket>＋ '+esc(label)+'</button>';}
function ticketRows(tickets,sample=false){return tickets.map(t=>'<tr tabindex="0" '+(sample?'data-record':'data-ticket')+'="'+esc(t.id)+'"><td><span class="ticket-id">'+esc(t.id)+'</span></td><td>'+esc(t.summary)+'<small>'+esc(sample?t.department:t.category)+'</small></td><td>'+badge(t.status)+'</td><td>'+badge(t.priority)+'</td></tr>').join('');}
function ticketTable(tickets,sample=false){return '<div class="table-wrap"><table class="ticket-table"><thead><tr><th>REQUEST ID</th><th>SUBJECT</th><th>STATUS</th><th>PRIORITY</th></tr></thead><tbody>'+ticketRows(tickets,sample)+'</tbody></table></div>';}
function emptyTickets(){return '<div class="empty"><div class="empty-icon">▤</div><h3>A fresh start for your requests</h3><p>Tickets you create appear here, only in your demo session.</p><button class="button" data-new-ticket>Create your first ticket ↗</button></div>';}
function articleRows(list){return list.map(a=>'<button class="article-row" data-article="'+esc(a.id)+'"><span>▧</span><span><strong>'+esc(a.title)+'</strong><small>'+esc(a.category)+' · Knowledge article</small></span><span class="arrow">↗</span></button>').join('');}
function overview(){
  const operational=boot.services.filter(s=>s.status==='Operational').length;
  main.innerHTML=heading('YOUR WORKDAY, CONNECTED','Good to have you here.','Everything you need to get back to doing your best work.','<span class="date-chip">◷ Demo snapshot · 20 Oct 2026</span>')+
  '<div class="stats">'+[
    ['Your open tickets',boot.tickets.filter(t=>t.status!=='Resolved').length,'Requests in your demo session','▤'],
    ['Knowledge articles',boot.articles,'Guides, policies & troubleshooting','▧'],
    ['Services operational',operational+' <small>/ '+boot.services.length+'</small>','Simulated service health','◉'],
    ['Sample requests',boot.counts.tickets,'Explore realistic support workflows','▦']
  ].map(s=>'<div class="stat"><div class="stat-top">'+s[0]+'<span class="stat-icon">'+s[3]+'</span></div><div class="stat-value">'+s[1]+'</div><div class="stat-foot">'+s[2]+'</div></div>').join('')+'</div>'+
  '<div class="grid-main"><div class="stack"><section class="card assistant-hero"><div class="orb" aria-hidden="true">✧</div><div class="hero-content"><div class="eyebrow">MEET YOUR SUPPORT ASSISTANT</div><h2>Less troubleshooting.<br>More getting things done.</h2><p>Describe the issue once. Get a diagnosis, approve the next action, and track resolution in one conversation.</p><a class="button primary" href="#assistant">Ask the assistant <span>↗</span></a><div class="hero-chips"><button data-prompt="I cannot connect to VPN">VPN not connecting</button><button data-prompt="How do I request new software?">Request software</button><button data-prompt="I need password reset assistance">Account access</button></div></div></section>'+
  '<section><h2 class="section-label">What can we help you with?</h2><div class="quick-grid"><button class="quick" data-new-ticket><span>＋</span><strong>Report an issue</strong><small>Let us take a look ↗</small></button><button class="quick" data-prompt="How do I request new software?"><span>▦</span><strong>Request software</strong><small>Get the tools you need ↗</small></button><a class="quick" href="#knowledge"><span>▧</span><strong>Find a guide</strong><small>A little help, on demand ↗</small></a></div></section>'+
  '<section class="card"><div class="card-head"><h2>Your recent requests</h2><a class="link" href="#tickets">View all ↗</a></div>'+(boot.tickets.length?ticketTable(boot.tickets.slice(0,4)):emptyTickets())+'</section></div>'+
  '<div class="stack"><section class="card"><div class="card-head"><h2>Service health</h2><a class="link" href="#status">View all ↗</a></div>'+
  ['vpn','email','wifi','identity'].map(id=>{let s=boot.services.find(s=>s.id===id);return '<div class="service-row"><span class="service-symbol">◈</span><span>'+esc(s.name)+'</span>'+badge(s.status)+'</div>';}).join('')+
  '<div class="status-summary">◷ Wi-Fi disruption · Bengaluru, floor 3<br>Wired Ethernet is available as a workaround.</div></section>'+
  '<section class="card"><div class="card-head"><h2>Popular guides</h2><a class="link" href="#knowledge">Browse ↗</a></div>'+articleRows([{id:'ns-001-e',title:'VPN connection timeout',category:'Network'},{id:'ns-010-e',title:'Password reset assistance',category:'Identity'},{id:'ns-011-e',title:'New software installation request',category:'Software'},{id:'ns-024-e',title:'New employee onboarding',category:'General'}])+'</section>'+
  '<section class="card"><div class="card-body"><div class="eyebrow">BUILT TO EXPLORE</div><h3>A complete fictional workplace</h3><p class="spaced">'+boot.counts.employees+' employees, '+boot.counts.assets+' assets and '+boot.counts.services+' services. Connected records show how an IT team works.</p><a class="link" href="#records">Explore the sample service desk ↗</a></div></section></div></div>';
}
function chatMessage(m){
  return '<div class="message '+esc(m.role)+'"><span class="message-icon">'+(m.role==='user'?'D':'✧')+'</span><div class="message-content"><div class="message-label">'+(m.role==='user'?'YOU':'NORTHSTAR ASSISTANT · '+(m.mode==='groq'?'AI + COMPANY KNOWLEDGE':m.mode==='pending'?'INVESTIGATION':'SUPPORT GUIDANCE'))+'</div><div class="message-text">'+esc(m.content)+'</div>'+
  (m.sources?.length?'<div class="source-chips">'+m.sources.map(s=>'<button data-article="'+esc(s.id)+'">▧ '+esc(s.title)+'</button>').join('')+'</div>':'')+
  (m.action?'<div class="spaced"><button data-workflow="'+esc(m.action.kind||'')+'" class="button" data-draft="'+esc(m.action.summary)+'" data-category="'+esc(m.action.category)+'">'+(m.action.type==='workflow'?'Start guided demo case':'Review ticket draft')+' ↗</button></div>':'')+
  (m.trace?.length?'<details class="trace"><summary>How this answer was prepared</summary><ul>'+m.trace.map(t=>'<li>'+esc(t)+'</li>').join('')+'</ul></details>':'')+'</div></div>';
}
function renderMessages(){
  const el=$('#chat-messages'); if(!el)return;
  el.innerHTML=conversation.length?conversation.map(chatMessage).join(''):'<div class="chat-welcome"><span class="sparkle">✧</span><h2>How can I help today?</h2><p>Describe the issue. We’ll find the right next step together.</p><div class="suggestions">'+scenarios.map(p=>'<button data-prompt="'+esc(p)+'">'+esc(p)+' ↗</button>').join('')+'</div></div>';
  if(sending)el.insertAdjacentHTML('beforeend','<div class="thinking" role="status">✧ Investigating your case. Checking the documentation and current results…</div>');
  el.scrollTop=el.scrollHeight;renderCase();
}
function assistant(){
  main.innerHTML=heading('SUPPORT, WITHOUT THE WAIT','Your IT copilot.','Grounded guidance. Clear sources. You stay in control.')+
  '<div class="assistant-layout"><section class="card chat-panel"><div class="card-head"><h2>Support assistant</h2><span class="badge purple">'+(boot.ai_available?'AI + knowledge search':'Local knowledge search')+'</span></div><div id="chat-messages" class="chat-messages" aria-live="polite" aria-label="Conversation"></div><div id="active-case" aria-live="polite"></div><form id="chat-form" class="composer"><div class="composer-inner"><textarea id="chat-input" aria-label="Describe your IT issue" maxlength="1500" placeholder="Tell us what’s getting in your way…" rows="2" required></textarea><button class="button primary" type="submit" id="send-chat" aria-label="Send message" '+(sending?'disabled':'')+'>↑</button></div><small>Use fictional details only. '+(boot.ai_available?'Messages and retrieved guides may be sent to Groq. ':'')+'Never share passwords, MFA codes or private information.</small><p id="chat-error" class="error-text" role="alert"></p></form></section><div class="stack"><section class="card"><div class="card-head"><h2>Here to help with</h2></div><div class="helper-list"><div><strong>▧ Find a reliable answer</strong><p>Search approved fictional IT guides and inspect the sources.</p></div><div><strong>◉ Understand service issues</strong><p>Check a clearly labeled snapshot of our demo services.</p></div><div><strong>▤ Prepare a support ticket</strong><p>Your issue opens a linked ticket automatically. Investigation, approvals and resolution stay in this chat.</p></div><div><strong>⌘ Keep access safe</strong><p>Resolve fictional VPN, account-access and software issues through confirmed, audited demo tools. Real accounts and devices are never changed.</p></div></div></section><section class="card"><div class="card-body"><h3>Not sure where to start?</h3><p class="spaced">Include the application, what you expected, and the error you saw.</p><button class="link" data-prompt="I cannot connect to VPN">Try the VPN scenario ↗</button></div></section></div></div>';
  renderMessages();
}
function renderCase(){
  const el=$('#active-case');if(!el)return;
  if(!activeCase){el.innerHTML='';return;}
  const c=activeCase;
  const stage={intake:'One detail needed',proposed:'Approval needed',awaiting_confirmation:'Please confirm the result',resolved:'Resolved',escalated:'Escalated',guidance:'Try the suggested steps',needs_detail:'More detail needed'}[c.stage]||c.stage;
  el.innerHTML='<div class="case-strip"><div><strong>'+esc(c.ticket_id)+'</strong> '+badge(stage)+' <button class="link" data-ticket="'+esc(c.ticket_id)+'">View ticket & history ↗</button></div><p>'+esc(c.explanation)+'</p><div class="workflow-actions">'+c.actions.map(a=>'<button class="button '+(['approve','resolved','helped'].includes(a.id)?'primary':'')+'" data-chat-action="'+esc(a.id)+'" '+(sending?'disabled':'')+'>'+esc(a.label)+'</button>').join('')+'</div><small>Actions affect demo resources only. You can reply naturally here; approvals apply only to this case and its current step.</small></div>';
}
async function acceptResult(data){
  activeCase=data.case||null;
  conversation.push({role:'assistant',content:data.answer,sources:data.sources,trace:data.tool_trace,mode:data.mode});
  if(data.ticket){const i=boot.tickets.findIndex(t=>t.id===data.ticket.id);if(i<0)boot.tickets.unshift(data.ticket);else boot.tickets[i]=data.ticket;updateCount();}
  renderMessages();
}
async function sendMessage(text,action=null){
  if(sending||text.trim().length<2)return;
  if(page!=='assistant'){location.hash='assistant';await route();}
  const payload={message:text,request_key:crypto.randomUUID(),case_id:activeCase?.ticket_id||null,revision:activeCase?.revision??null,action};
  if(pendingMessage&&pendingMessage.message===text&&pendingMessage.action===action)Object.assign(payload,pendingMessage);
  pendingMessage=payload;
  sending=true;conversation.push({role:'user',content:text});renderMessages();
  $('#chat-input').value='';$('#send-chat').disabled=true;$('#chat-error').textContent='';
  try{const data=await api('/assist',{method:'POST',body:JSON.stringify(payload)});pendingMessage=null;await acceptResult(data);}
  catch(e){if($('#chat-error')){$('#chat-error').textContent=e.message;$('#chat-input').value=text;}else toast(e.message);
    try{const fresh=await api('/bootstrap');activeCase=fresh.active_case;boot.tickets=fresh.tickets;updateCount();}catch{}
  }
  finally{sending=false;renderMessages();if($('#send-chat'))$('#send-chat').disabled=false;}
}
async function continueChat(id){
  const data=await api('/tickets/'+encodeURIComponent(id)+'/continue',{method:'POST'});
  closeModal();location.hash='assistant';await route();await acceptResult(data);
}
async function ticketsPage(version){
  const data=await api('/tickets');if(version!==routeVersion)return;boot.tickets=data.tickets;updateCount();
  main.innerHTML=heading('YOUR SUPPORT REQUESTS','A clear path to resolution.','Create and track requests in your isolated demo session.',ticketButton())+
  '<section class="card"><div class="card-head"><h2>My tickets</h2><small>'+boot.tickets.length+' requests · demo only</small></div>'+(boot.tickets.length?ticketTable(boot.tickets):emptyTickets())+'</section>'+
  '<p class="dataset-note spaced">These are your requests, not the fictional company’s historical records. Demo tickets are not routed to a real IT team.</p>';
}
function newTicket(summary='',category='General',kind=null){
  draftWorkflow=kind;
  ticketKey=crypto.randomUUID();
  openModal('<div class="eyebrow">NEW SUPPORT REQUEST</div><h2 id="modal-title">Let’s get this sorted.</h2><p>Submit once. The agent will investigate your description and continue with you in chat.</p>'+(kind?'<div class="form-note">This starts the '+esc(kind)+' agent workflow on fictional resources. The agent will ask for confirmation before changes. When AI is enabled, case details and retrieved guides are sent to Groq.</div>':'')+'<form id="ticket-form"><label class="form-field">Summary<input name="summary" minlength="5" maxlength="160" required value="'+esc(summary)+'" placeholder="A short description of the issue"></label><label class="form-field">What happened?<textarea name="description" minlength="10" maxlength="3000" required placeholder="What were you trying to do? Include the error and steps already tried. Use fictional details only.">'+(kind?esc('Demo scenario: '+summary+'. Please investigate using the documented procedure.'):'')+'</textarea></label><div class="form-row"><label class="form-field">Category<select name="category">'+['General','Network','Identity','Software','Hardware'].map(x=>'<option '+(x===category?'selected':'')+'>'+x+'</option>').join('')+'</select></label><label class="form-field">Impact<select name="priority"><option value="Low">Low · workaround available</option><option value="Medium" selected>Medium · one person blocked</option><option value="High">High · multiple people affected</option></select></label></div><div class="form-note">This creates a demo ticket and starts investigation. When AI is enabled, the description and company guides are sent to Groq. No real accounts or devices are changed. Do not include secrets or personal information.</div><p class="error-text" id="ticket-error" role="alert"></p><div class="form-actions"><button type="button" class="button" data-close>Cancel</button><button type="submit" class="button primary" id="confirm-ticket">Create ticket & investigate ↗</button></div></form>');
}
async function submitTicket(form){
  const data=Object.fromEntries(new FormData(form));data.request_key=ticketKey;data.investigate=true;
  $('#confirm-ticket').disabled=true;$('#confirm-ticket').textContent='Creating ticket & investigating…';
  try{const t=await api('/tickets',{method:'POST',body:JSON.stringify(data)});if(!boot.tickets.some(x=>x.id===t.id))boot.tickets.unshift(t);updateCount();closeModal();location.hash='assistant';await route();
    if(t.assistant)await acceptResult(t.assistant);else await continueChat(t.id);
    toast('Ticket '+t.id+' is linked to this conversation.');
  }catch(e){if($('#ticket-error')){$('#ticket-error').textContent=e.message;$('#confirm-ticket').disabled=false;$('#confirm-ticket').textContent='Retry investigation';}else toast(e.message);}
}
async function viewTicket(id,sample=false){
  const t=sample?currentRecords.find(t=>t.id===id):await api('/tickets/'+encodeURIComponent(id));
  if(!t)return;
  openModal('<div class="eyebrow">'+(sample?'SYNTHETIC HISTORICAL RECORD':'YOUR DEMO REQUEST')+'</div><h2 id="modal-title">'+esc(t.summary)+'</h2><p>'+esc(t.id)+' · '+esc(t.category)+' · '+stamp(t.created_at)+'</p>'+badge(t.status)+' '+badge(t.priority)+
  (sample?'<p class="spaced">'+esc(t.requester)+' · '+esc(t.department)+' · Asset '+esc(t.asset_id)+'</p><div class="timeline">'+t.timeline.map(x=>'<div><small>'+esc(new Date(x.at).toLocaleString())+'</small><h3>'+esc(x.event)+'</h3><p>'+esc(x.note)+'</p></div>').join('')+'</div><button class="button" data-article="'+esc(t.article_id)+'">Read linked knowledge article ↗</button>':'<p class="article-text spaced">'+esc(t.description)+'</p><div class="timeline"><div><small>'+stamp(t.created_at)+'</small><h3>Request received</h3><p>Saved in your demo workspace. No real service team has been notified.</p></div></div>'+workflowPanel(t)));
}
function workflowPanel(t){
  const w=t.workflow;
  return '<section class="workflow-panel"><div class="eyebrow">AGENT INVESTIGATION</div><h3>'+(w?'Your case progress':'Investigate this request')+'</h3><p>'+esc(w?w.explanation:'The agent will read this ticket description. You will not need to enter it again.')+'</p>'+
  (w?'<div class="spaced">'+badge(w.stage.replaceAll('_',' '))+' '+badge(w.mode==='groq'?'LLM + company knowledge':w.mode==='pending'?'Awaiting information':'Documented guidance')+'</div>':'')+
  '<button class="button primary" data-continue-case="'+esc(t.id)+'">'+(w?'Continue in chat':'Investigate from this description')+' ↗</button>'+
  (w?.verification?'<p class="form-note">✓ '+esc(w.verification.check)+'</p>':'')+
  (w?'<details class="trace"><summary>Investigation & action history</summary><div class="timeline">'+w.events.map(e=>'<div><small>'+esc(new Date(e.at).toLocaleString())+'</small><h3>'+esc(e.event)+'</h3><p>'+esc(e.note)+'</p></div>').join('')+'</div></details>':'')+'</section>';
}
async function knowledgePage(version){
  const data=await api('/knowledge');if(version!==routeVersion)return;articles=data.articles;
  main.innerHTML=heading('THE KNOWLEDGE CENTER','Answers worth keeping.','Explore fictional policies, troubleshooting guides and service desk runbooks.')+
  '<div class="searchbar"><input id="knowledge-search" aria-label="Search knowledge articles" placeholder="Search by topic, service or keyword…"><select id="knowledge-category" aria-label="Filter category"><option value="">All categories</option>'+['Network','Identity','Software','Hardware','General'].map(x=>'<option>'+x+'</option>').join('')+'</select><select id="knowledge-audience" aria-label="Filter audience"><option value="employee">Employee guides</option><option value="all">All articles & runbooks</option></select></div><p id="article-count" class="dataset-note"></p><div id="knowledge-grid" class="knowledge-grid"></div>';
  filterArticles();
}
function filterArticles(){
  const query=$('#knowledge-search').value.toLowerCase(),category=$('#knowledge-category').value,audience=$('#knowledge-audience').value;
  const items=articles.filter(a=>(!query||(a.title+' '+a.category).toLowerCase().includes(query))&&(!category||a.category===category)&&(audience==='all'||!a.id.endsWith('-s')));
  $('#article-count').textContent=items.length+' articles · All policies belong to the fictional Northstar company';
  $('#knowledge-grid').innerHTML=items.map(a=>'<button class="knowledge-card" data-article="'+esc(a.id)+'"><span class="doc-icon">▧</span><h3>'+esc(a.title)+'</h3><small>'+esc(a.category)+' <span>↗</span></small></button>').join('')||'<div class="empty"><h3>No matching articles</h3><p>Try a broader term or another category.</p></div>';
}
async function viewArticle(id){
  const a=await api('/knowledge/'+encodeURIComponent(id));
  const text=a.content.split('\n').slice(1).map(line=>line.startsWith('## ')?'<h3>'+esc(line.slice(3))+'</h3>':esc(line)).join('\n');
  openModal('<div class="eyebrow">'+esc(a.category)+' · KNOWLEDGE ARTICLE</div><h2 id="modal-title">'+esc(a.title)+'</h2><p>'+esc(a.source)+'</p><div class="article-text">'+text+'</div>');
}
function statusPage(){
  main.innerHTML=heading('SERVICE HEALTH','Know what’s happening.','Simulated service snapshot as of 20 October 2026. This is not live monitoring.','<span class="badge warn">1 degraded service</span>')+
  '<div class="status-grid">'+boot.services.map(s=>'<section class="card service-card">'+badge(s.status)+'<h3>'+esc(s.name)+'</h3><p>'+esc(s.note)+'</p><small>Owner: '+esc(s.owner)+'</small></section>').join('')+'</div>'+
  '<section class="card spaced"><div class="card-head"><h2>Incident & maintenance history</h2><small>'+boot.incidents.length+' synthetic records</small></div>'+boot.incidents.map(i=>'<div class="incident">'+badge(i.status)+'<h3>'+esc(i.title)+'</h3><p>'+esc(i.impact)+'</p><small>'+esc(i.id)+' · '+stamp(i.updated_at)+'</small></div>').join('')+'</section>';
}
async function recordsPage(version){
  main.innerHTML=heading('BEHIND THE SERVICE DESK','Every request has a story.','Browse 600 linked historical tickets from our fictional organization.')+
  '<p class="dataset-note">Read-only synthetic records · '+boot.counts.employees+' employees · '+boot.counts.assets+' assigned assets · 90-day sample</p><form id="records-search" class="searchbar"><input id="records-query" maxlength="120" aria-label="Search sample requests" placeholder="Search by issue, status, category or request ID…" value="'+esc(recordQuery)+'"><button class="button">Search</button></form><section class="card" id="records-card"><div class="empty">Loading sample records…</div></section>';
  await loadRecords(version);
}
async function loadRecords(version=routeVersion){
  const data=await api('/demo-records?q='+encodeURIComponent(recordQuery)+'&page='+recordPage);
  if(version!==routeVersion||!$('#records-card'))return;
  currentRecords=data.records;
  $('#records-card').innerHTML=(data.records.length?ticketTable(data.records,true):'<div class="empty">No records match this search.</div>')+
  '<div class="table-footer"><span>'+data.total+' matching records</span><div class="pagination"><button class="button compact" id="records-prev" '+(recordPage<=1?'disabled':'')+'>←</button><span>Page '+recordPage+' / '+Math.max(1,Math.ceil(data.total/20))+'</span><button class="button compact" id="records-next" '+(recordPage*20>=data.total?'disabled':'')+'>→</button></div></div>';
}
function updateCount(){$('#ticket-count').textContent=boot.tickets.length;}
async function route(){
  if(!boot)return;
  page=location.hash.slice(1);if(!labels[page])page='overview';
  const version=++routeVersion;
  $('#page-label').textContent=labels[page];
  document.title=labels[page]+' • Northstar IT';
  document.querySelectorAll('[data-page]').forEach(a=>{a.classList.toggle('active',a.dataset.page===page);if(a.dataset.page===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  try{
    if(page==='overview')overview();
    else if(page==='assistant')assistant();
    else if(page==='tickets')await ticketsPage(version);
    else if(page==='knowledge')await knowledgePage(version);
    else if(page==='status')statusPage();
    else await recordsPage(version);
  }catch(e){if(version===routeVersion)errorScreen(e);}
}
function errorScreen(e){main.innerHTML='<div class="loading-page"><h1>Let’s reconnect.</h1><p>'+esc(e.message)+'</p><button class="button primary" id="retry-app">Try again</button></div>';}
function privacy(){
  openModal('<div class="eyebrow">YOUR DEMO SESSION</div><h2 id="modal-title">A workspace of your own.</h2><p>Tickets and messages are tied to a random session token stored in this browser tab. Other visitors cannot access them through the app. This is not an employee login.</p><p>Demo records expire after 7 days and are removed on startup or when a new session is created. The hosting operator can access stored data; use fictional details only.</p><p>'+(boot.ai_available?'AI explanations are enabled. Questions, recent conversation and retrieved guides can be sent to Groq.':'AI explanations are currently disabled. Answers use local knowledge search.')+'</p><p>Limits: 80 messages and 20 tickets per session, plus request-rate limits. Sample company records are read-only.</p><div class="form-note">Deleting this session permanently removes your demo tickets, conversation and audit records. It does not remove the fictional sample dataset.</div><div class="form-actions"><button class="button" data-close>Keep exploring</button><button class="button primary" id="delete-session">Delete my session</button></div>');
}
async function start(){
  try{
    if(!token){const s=await api('/session',{method:'POST'});token=s.token;sessionStorage.setItem('northstar-demo-token',token);}
    boot=await api('/bootstrap');activeCase=boot.active_case;$('#ai-mode').textContent=boot.ai_available?'AI':'KB';const h=await api('/history');conversation=h.messages;updateCount();await route();
  }catch(e){errorScreen(e);}
}
document.addEventListener('click',async e=>{
  const target=e.target.closest('button,a,tr');if(!target)return;
  try{
    if(target.matches('[data-new-ticket]')||target.id==='header-ticket'){if(boot)newTicket();}
    else if(target.dataset.prompt){const text=target.dataset.prompt;location.hash='assistant';await route();await sendMessage(text);}
    else if(target.dataset.draft)newTicket(target.dataset.draft,target.dataset.category,target.dataset.workflow||null);
    else if(target.dataset.continueCase){target.disabled=true;target.textContent='Reading your case…';try{await continueChat(target.dataset.continueCase);}catch(err){target.disabled=false;target.textContent='Retry investigation';throw err;}}
    else if(target.dataset.chatAction)await sendMessage(target.textContent.trim(),target.dataset.chatAction);
    else if(target.dataset.article)await viewArticle(target.dataset.article);
    else if(target.dataset.ticket)await viewTicket(target.dataset.ticket);
    else if(target.dataset.record)await viewTicket(target.dataset.record,true);
    else if(target.matches('[data-close]')||target.id==='close-modal')closeModal();
    else if(target.id==='privacy-button'||target.matches('[data-privacy]')){if(boot)privacy();}
    else if(target.id==='retry-app')await start();
    else if(target.id==='records-next'){recordPage++;await loadRecords();}
    else if(target.id==='records-prev'){recordPage--;await loadRecords();}
    else if(target.id==='delete-session'){
      target.disabled=true;await api('/session',{method:'DELETE'});token=null;sessionStorage.removeItem('northstar-demo-token');boot=null;conversation=[];activeCase=null;pendingMessage=null;closeModal();
      main.innerHTML='<div class="loading-page"><h1>Your session has been deleted.</h1><p>Your demo tickets and messages have been removed.</p><button class="button primary" id="retry-app">Start a new session</button></div>';
    }
  }catch(error){toast(error.message);}
});
document.addEventListener('submit',async e=>{
  if(e.target.id==='chat-form'){e.preventDefault();await sendMessage($('#chat-input').value.trim());}
  if(e.target.id==='ticket-form'){e.preventDefault();await submitTicket(e.target);}
  if(e.target.id==='records-search'){e.preventDefault();recordQuery=$('#records-query').value;recordPage=1;try{await loadRecords();}catch(error){toast(error.message);}}
});
document.addEventListener('input',e=>{if(e.target.id==='knowledge-search')filterArticles();});
document.addEventListener('change',e=>{if(e.target.id==='knowledge-category'||e.target.id==='knowledge-audience')filterArticles();});
document.addEventListener('keydown',e=>{
  if(e.target.matches('tr[data-ticket],tr[data-record]')&&e.key==='Enter')e.target.click();
  if(e.target.id==='chat-input'&&e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('#chat-form').requestSubmit();}
});
window.addEventListener('hashchange',route);
start();
