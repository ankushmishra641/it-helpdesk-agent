"""Generate the shareable project brief with ReportLab."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'pdf'/'Northstar_Project_Brief.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
W,H=595.28,841.89
INK='#20263e'; MUTED='#68738b'; PURPLE='#705ce7'; NAV='#171d32'
styles={
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=16,textColor=HexColor(MUTED)),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8,leading=12,textColor=HexColor(MUTED)),
 'h2':ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=16,leading=21,textColor=HexColor(INK)),
 'h3':ParagraphStyle('h3',fontName='Helvetica-Bold',fontSize=11,leading=16,textColor=HexColor(INK)),
}
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Northstar IT Service Desk | Project & Engineering Brief')
c.setAuthor('IT Helpdesk Agent project')
def para(text,x,y,width,style='body'):
 p=Paragraph(text,styles[style]);_,height=p.wrap(width,700);p.drawOn(c,x,y-height);return y-height
def base(number,title,kicker):
 c.setFillColor(HexColor('#f8f9fc'));c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(HexColor(NAV));c.rect(0,H-90,W,90,fill=1,stroke=0)
 c.setFillColor(HexColor('#b0a3ff'));c.setFont('Helvetica-Bold',10);c.drawString(42,H-34,'NORTHSTAR / IT SERVICE DESK')
 c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica',9);c.drawString(42,H-57,kicker)
 c.setFillColor(HexColor(INK));c.setFont('Helvetica-Bold',26);c.drawString(42,H-137,title)
 c.setStrokeColor(HexColor('#e0e4ed'));c.line(42,48,W-42,48)
 c.setFillColor(HexColor(MUTED));c.setFont('Helvetica',8);c.drawString(42,32,'PUBLIC DEMO  /  SYNTHETIC DATA  /  27 OCTOBER 2026')
 c.drawRightString(W-42,32,f'{number:02d} / 04')
 return H-160
def section(title,body,y):
 y=para(title,42,y,W-84,'h2')-9
 y=para(body,42,y,W-84)-23
 return y
def card(x,y,w,title,text):
 c.setFillColor(HexColor('#ffffff'));c.setStrokeColor(HexColor('#e4e7ef'));c.roundRect(x,y-110,w,110,9,fill=1,stroke=1)
 para(title,x+15,y-15,w-30,'h3');para(text,x+15,y-39,w-30,'small')
y=base(1,'Better support. Clearer next steps.','PRODUCT & ENGINEERING BRIEF')
y=para('A working employee-support experience built for public exploration. Search IT procedures, understand service health and create a request in a private demo workspace.',42,y,W-84)-30
c.setFillColor(HexColor('#eeeafb'));c.roundRect(42,y-95,W-84,95,10,fill=1,stroke=0)
for x,num,label in [(60,'60','knowledge articles'),(185,'600','sample tickets'),(310,'150','fictional employees'),(435,'20','demo services')]:
 c.setFillColor(HexColor(PURPLE));c.setFont('Helvetica-Bold',27);c.drawString(x,y-37,num)
 c.setFont('Helvetica',8);c.setFillColor(HexColor(MUTED));c.drawString(x,y-59,label)
y-=126
y=section('One connected service desk','The portal brings together an overview, support assistant, personal tickets, knowledge center, simulated service status and read-only historical requests. The responsive layout uses consistent navigation, source cards, visible confirmation steps and helpful error states.',y)
card(42,y,246,'Grounded support','A bounded LangGraph workflow retrieves approved fictional articles. Optional Groq explanations remain separate from actions.')
card(307,y,246,'Visitor-owned requests','Opaque session tokens scope persistent tickets and conversations. Retried submissions return the original request.')
y-=137
y=section('Honest demonstration boundaries','No real employee directory, identity provider or monitoring service is connected. Password resets are disabled. Historical records and service health are labeled as simulated. This release is a public-demo foundation, not an enterprise production certification.',y)
c.showPage()
y=base(2,'Architecture that keeps actions safe.','SYSTEM DESIGN & SECURITY')
y=para('The application runs as one FastAPI service with a buildless browser frontend. The small knowledge corpus is indexed locally using BM25, avoiding model downloads and a heavyweight vector database on a free host.',42,y,W-84)-25
for x,w,title in [(42,145,'BROWSER PORTAL'),(225,145,'FASTAPI'),(408,145,'POSTGRESQL')]:
 c.setFillColor(HexColor('#eeeafb'));c.roundRect(x,y-47,w,47,7,fill=1,stroke=0)
 c.setFillColor(HexColor(PURPLE));c.setFont('Helvetica-Bold',9);c.drawCentredString(x+w/2,y-28,title)
c.setStrokeColor(HexColor('#b7adc9'));c.line(187,y-23,225,y-23);c.line(370,y-23,408,y-23)
y-=72
y=section('A bounded model workflow','Retrieve evidence, then explain it. Groq receives only the question, limited recent context and selected guides. The model has no mutation tools or database credential. Ticket creation uses a separate validated endpoint after the visitor reviews the form.',y)
y=section('Security improvements','The original caller-controlled identity flag and unsafe tool server are removed from public use. Session ownership is enforced server-side. Request bodies and field lengths are capped; client-supplied history is rejected. Dynamic content is escaped and the portal uses a restrictive Content Security Policy.',y)
y=section('Persistence and limits','SQLAlchemy provides local SQLite and hosted PostgreSQL support. Tickets, counters and audit events are transactional. A unique request key prevents duplicates. Daily model/session allowances are stored atomically in the database; short-term throttling and concurrency limits assume one application worker.',y)
y=section('Remaining enterprise work','Before using real company data: add SSO, RBAC, verified identity-provider flows, permission-scoped ITSM connectors, distributed limits, explicit upgrade migrations, backup restore testing and an independent security review. AI text can still be inaccurate; source inspection remains important.',y)
c.showPage()
y=base(3,'A fictional company with connected data.','CONTENT & DEMONSTRATION')
y=para('The snapshot models Northstar Systems, a distributed technology company. All content is synthetic. Email addresses use the reserved .example domain. Snapshot date: 20 October 2026.',42,y,W-84)-23
rows=[('Knowledge','60 articles','30 employee guides paired with desk runbooks'),
('People','150 employees','Departments, offices and manager relationships'),
('Assets','250 records','Assigned laptops, docks and monitors'),
('Support','600 tickets','Requesters, assets, timelines and linked guides'),
('Operations','20 services / 40 incidents','Service ownership, maintenance and impact')]
for i,(a,b,d) in enumerate(rows):
 c.setFillColor(HexColor('#ffffff' if i%2==0 else '#f0f2f8'));c.rect(42,y-46,W-84,46,fill=1,stroke=0)
 para(a,53,y-12,92,'h3');para(b,145,y-12,115,'small');para(d,270,y-12,267,'small');y-=46
y-=27
y=section('Documentation that supports a workflow','Each active article includes an owner, audience, version, review dates, symptoms, prerequisites, resolution, validation, escalation and evidence/privacy instructions. The six prototype notes are preserved in an archive and excluded from retrieval.',y)
y=section('Suggested five-minute walkthrough','<b>1.</b> Inspect the overview and the labeled Wi-Fi incident.<br/><b>2.</b> Ask: "I cannot connect to VPN" and open the cited guide.<br/><b>3.</b> Ask to create a ticket; review and confirm the form.<br/><b>4.</b> Open My tickets and inspect the saved request.<br/><b>5.</b> Browse a historical ticket and its resolution timeline.<br/><b>6.</b> Ask for a password reset and observe the enforced boundary.',y)
y=section('Reproducible by design','The seed script recreates linked records and active articles deterministically. Visitor tickets do not modify the historical dataset. Sample statistics are record counts, not fabricated operational performance metrics.',y)
c.showPage()
y=base(4,'Release evidence and launch checklist.','VERIFICATION & OPERATIONS')
y=section('Verified locally','22 automated tests pass in a clean Python environment. Coverage includes visitor isolation, authentication, expiry, deletion, persistence, concurrent duplicate submissions, provider failure, request limits, retrieval scenarios and dataset integrity. Dependency auditing reported no known vulnerabilities across 48 resolved packages on 27 October 2026.',y)
y=section('Target deployment','Render Free serves the portal and backend through one HTTPS URL. Supabase Free provides PostgreSQL persistence in a private helpdesk schema. Groq is optional; local knowledge search works without a key. Free services can sleep or pause, so this is not an always-on SLA.',y)
y=section('Deployment gates','<b>Before publishing:</b> select the release branch, configure the private database URI, verify role/schema permissions and run the staging database smoke test.<br/><br/><b>After publishing:</b> test health, two-session isolation, ticket creation, refresh and redeploy persistence, mobile behavior, and provider fallback. Verify a backup restore before storing records that matter.',y)
y=section('Operational defaults','7-day session expiry; 50 new sessions per day globally; 80 messages and 20 tickets per session; 8 chat requests per minute per session; 100 optional model calls per day; 2 concurrent provider calls. These are resource bounds, not a monetary guarantee.',y)
y=section('Release status','Prepared for deployment. A live Render URL, target PostgreSQL behavior, backup restoration and live provider answer quality must be verified in the selected accounts. Detailed API, security, architecture, deployment and operations guides are included in the repository.',y)
c.save()
print(OUT)
