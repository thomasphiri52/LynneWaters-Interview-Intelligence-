const content=document.getElementById("content");
const title=document.getElementById("pageTitle");
const navs=document.querySelectorAll(".nav");
const modal=document.getElementById("interviewModal");
let interviews=JSON.parse(localStorage.getItem("lw_interviews")||"[]");

const pages={
dashboard(){title.textContent="Executive Intelligence";content.innerHTML=`
<div class="actions"><button class="primary" onclick="openModal()">＋ NEW INTERVIEW</button><button class="secondary" onclick="showPage('documents')">▣ UPLOAD DOCUMENT</button><button class="secondary" onclick="showPage('reports')">▤ REPORT BUILDER</button></div>
<div class="stats">
${[['64','INTERVIEWS'],['241','DOCUMENTS'],['98','FINDINGS'],['31','REQUIREMENTS'],['R2.4M','OPPORTUNITY VALUE']].map(x=>`<div class="glass stat"><div class="muted">${x[1]}</div><div class="value">${x[0]}</div></div>`).join('')}</div>
<div class="grid2">
<div class="glass card"><h3>Priority Findings</h3><div class="list">
<div class="row"><span>Data fragmentation</span><span class="badge high">HIGH</span></div>
<div class="row"><span>Manual processes</span><span class="badge high">HIGH</span></div>
<div class="row"><span>Reporting delays</span><span class="badge medium">MEDIUM</span></div>
<div class="row"><span>Limited automation</span><span class="badge verified">VERIFIED</span></div></div></div>
<div class="glass card"><h3>Knowledge Health</h3>
${[['Evidence coverage','91%','91'],['Requirement clarity','89%','89'],['Verification','84%','84']].map(x=>`<div class="metric"><div class="metric-top"><span>${x[0]}</span><b>${x[1]}</b></div><div class="bar"><i style="width:${x[2]}%"></i></div></div>`).join('')}</div></div>
<div class="glass card" style="margin-top:16px"><h3>Recent Interviews</h3>${interviews.length?`<table class="table"><tr><th>Title</th><th>Interviewee</th><th>Organisation</th><th>Date</th></tr>${interviews.slice(-5).reverse().map(i=>`<tr><td>${i.title}</td><td>${i.person}</td><td>${i.org}</td><td>${i.date}</td></tr>`).join('')}</table>`:'<div class="empty">No local interviews yet. Create your first interview session.</div>'}</div>`},
interviews(){title.textContent="Interviews";content.innerHTML=`<div class="actions"><button class="primary" onclick="openModal()">＋ NEW INTERVIEW</button></div><div class="glass page-card"><h3>Interview Sessions</h3>${interviews.length?`<table class="table"><tr><th>Title</th><th>Interviewee</th><th>Position</th><th>Organisation</th><th>Date</th><th>Status</th></tr>${interviews.map(i=>`<tr><td>${i.title}</td><td>${i.person}</td><td>${i.position}</td><td>${i.org}</td><td>${i.date}</td><td><span class="badge verified">ACTIVE</span></td></tr>`).join('')}</table>`:'<div class="empty">No interview sessions created.</div>'}</div>`},
documents(){simple("Documents","Upload and organise documents supplied during interviews.",["Company profiles","Strategy documents","Requirements","Process documents","Spreadsheets","Scanned evidence"])},
findings(){simple("Findings","Capture, verify and trace findings back to interview answers and evidence.",["Data fragmentation","Manual processes","Reporting delays","Customer experience gaps"])},
requirements(){simple("Requirements","Convert validated findings into structured business and technical requirements.",["Functional requirements","Technical requirements","Business requirements","Acceptance criteria"])},
risks(){simple("Risks","Track risks, severity, evidence and mitigation actions.",["Data quality","Process dependency","Missing documentation","Information conflicts"])},
opportunities(){simple("Opportunities","Prioritise improvement opportunities using impact, cost and urgency.",["Automation","Data centralisation","Analytics","Process optimisation"])},
actions(){simple("Actions","Track owners, deadlines, priorities and completion status.",["Validate requirements","Review documents","Prepare recommendations","Schedule follow-up"])},
reports(){simple("Report Builder","Generate a professional interview and business discovery report.",["Executive Summary","Interview Overview","Key Findings","Requirements","Evidence Register","Action Plan","Recommendations"])},
settings(){simple("Settings","Configure workspace, users, confidentiality and reporting preferences.",["Workspace profile","Access control","Report branding","Data preferences"])}
};
function simple(t,desc,items){title.textContent=t;content.innerHTML=`<div class="glass page-card"><div class="eyebrow">MODULE</div><h2>${t}</h2><p class="muted">${desc}</p><div class="list" style="margin-top:22px">${items.map(x=>`<div class="row"><span>${x}</span><span class="badge verified">READY</span></div>`).join('')}</div></div>`}
function showPage(v){pages[v]();navs.forEach(n=>n.classList.toggle("active",n.dataset.view===v))}
navs.forEach(n=>n.addEventListener("click",()=>showPage(n.dataset.view)));
function openModal(){modal.classList.remove("hidden");document.getElementById("iDate").value=new Date().toISOString().slice(0,10)}
document.getElementById("closeModal").onclick=()=>modal.classList.add("hidden");
document.getElementById("createInterview").onclick=()=>{
 const i={title:document.getElementById("iTitle").value||"Business Discovery Interview",person:document.getElementById("iPerson").value||"Unknown",position:document.getElementById("iPosition").value||"—",org:document.getElementById("iOrg").value||"—",purpose:document.getElementById("iPurpose").value||"",date:document.getElementById("iDate").value||new Date().toISOString().slice(0,10)};
 interviews.push(i);localStorage.setItem("lw_interviews",JSON.stringify(interviews));modal.classList.add("hidden");showPage("interviews");
};
showPage("dashboard");
