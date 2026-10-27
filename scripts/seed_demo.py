"""Deterministic, linked synthetic data. Never imports real employees or tickets."""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# title, category, symptoms, resolution, escalation, service
TOPICS = [
('VPN connection timeout','Network','GlobalProtect remains on Connecting or reports a gateway timeout.',
'Confirm internet access by opening the company portal. Close other VPN clients. Select the Northstar gateway in the approved client. Reconnect once and approve the MFA prompt you initiated. If the service snapshot shows an incident, follow the incident workaround instead of reinstalling.',
'Escalate after one retry with the client version, gateway region, error code and local timestamp. Never collect an MFA code.','vpn'),
('VPN connected but internal apps unavailable','Network','VPN shows Connected but an internal application cannot be reached.',
'Check whether other internal applications work. Confirm the assigned gateway region. Disconnect and reconnect once. Test the application in a private browser window. Record whether the same URL works on the office network.',
'Route a single-application failure to its owner; route failures across multiple applications to Network Operations.','vpn'),
('Corporate Wi-Fi authentication failure','Network','Northstar-Secure rejects the managed device or repeatedly asks for credentials.',
'Confirm the device clock is synchronized. Choose Northstar-Secure rather than Guest. Run Company Portal sync. Verify the server certificate against the managed profile; do not accept an unexpected certificate. Forget and rejoin the network only if the device is managed.',
'Send the device asset ID, office, floor and error text to Network Operations. Stop if a certificate warning appears.','wifi'),
('Wi-Fi intermittent connection','Network','Wireless drops during meetings, especially in a specific office zone.',
'Check the service incident board for your office. Move to a different access-point area or use approved wired Ethernet. Record the floor and approximate disconnect times. Reconnect after moving and test a short call.',
'Escalate repeated drops affecting multiple people as High priority. Include location and timestamps, not packet captures containing personal traffic.','wifi'),
('Email synchronization delay','Software','Outlook shows old mail or stays on Updating folder.',
'Check the email service snapshot. Open the approved web mail application to distinguish a client problem from a service problem. Confirm network connectivity and available mailbox space. Restart Outlook once. Do not remove a profile without helpdesk guidance.',
'Provide the client version and whether web mail works. Redact message content and recipient addresses from screenshots.','email'),
('Mailbox storage quota','Software','Sending mail fails with a mailbox full warning.',
'Review mailbox storage in web mail settings. Archive eligible mail under the retention policy. Empty Deleted Items only after reviewing its contents. Do not delete legal-hold or retention-protected material. Recheck the quota after synchronization.',
'Ask Messaging Operations to review approved archive capacity if policy-compliant cleanup does not resolve it.','email'),
('Missing MFA notification','Identity','A sign-in you started does not produce an authenticator notification.',
'Open the enrolled authenticator app and check network access. Enable automatic device time. Use an already-enrolled alternate factor if available. Cancel unexpected prompts. If no approved factor works, request Identity support.',
'Identity support must verify ownership through the approved identity provider. Never ask for a one-time code in chat.','identity'),
('Lost phone and MFA recovery','Identity','The employee no longer has access to their enrolled authenticator device.',
'Report the lost device through the service desk. Use an existing recovery method only through the approved sign-in page. Do not enroll a replacement phone through an unsolicited link. Submit an Identity request describing the lost factor without sharing credentials.',
'An authorized Identity administrator must perform recovery after verified identity checks; manager approval alone is not technical verification.','identity'),
('Account lockout recovery','Identity','Sign-in reports too many failed attempts or a locked account.',
'Stop retrying the old password. Check for stale credentials in approved mail or VPN clients. Use the self-service recovery flow if available. Submit an Identity ticket if the lockout recurs; include timestamps and affected applications.',
'Repeated lockouts after recovery require investigation of stale credentials or suspicious sign-in events.','identity'),
('Password reset assistance','Identity','An employee forgot a password or needs account recovery.',
'Use the approved self-service identity portal and complete its verification flow. Never share a password, temporary password, recovery code or MFA code in this demo. An employee ID does not establish identity. If self-service fails, submit an Identity ticket.',
'Real resets are disabled in the public demo. Enterprise recovery requires authenticated identity-provider integration and audit logging.','identity'),
('New software installation request','Software','A required application is not available on the managed device.',
'Search the approved software catalog. If available, install through Company Portal. Otherwise submit the product name, business justification, license requirement and manager. Security and procurement review unapproved products before packaging.',
'Route unapproved software to Software Asset Management. Do not download installers from third-party mirrors.','software'),
('Software license unavailable','Software','An approved application reports that no license is assigned.',
'Confirm you are signing in with the correct work account. Review the license request status. Sign out and back in after a confirmed assignment. Include the application name and entitlement request ID in a support ticket.',
'Software Asset Management checks available seats and approval history; do not borrow another employee account.','software'),
('Device running slowly','Hardware','A managed laptop is slow during ordinary work.',
'Save your work and restart once. Review available disk space and close unused applications. Run Company Portal sync. Record when the slowdown happens and which applications are affected. Do not disable endpoint protection or install cleanup utilities.',
'Route persistent device-wide slowness to Endpoint Engineering with the asset ID and a redacted screenshot of resource usage.','devices'),
('Low disk space on laptop','Hardware','The system drive has less than the recommended free space.',
'Use the operating-system storage settings to inspect usage. Remove approved temporary files and move work documents to the managed cloud drive. Review before deleting anything. Do not remove system folders or retained evidence.',
'Escalate if free space remains low after safe cleanup or storage errors appear. Include disk capacity and available space.','devices'),
('Device encryption recovery','Identity','The device requests an encryption recovery key after a change or restart.',
'Keep the device powered and record its recovery identifier. Contact the authorized service desk using another device. Do not post the recovery screen or key in public chat. Do not reinstall the operating system.',
'Endpoint administrators retrieve recovery material only after verified identity and asset ownership checks. No keys are provided by this demo.','devices'),
('Managed operating system updates','Hardware','An update is pending or repeatedly fails on a work device.',
'Connect power and a reliable network. Save work and schedule a restart within the maintenance window. Run the approved update interface once. Record the error code if the update fails; do not disable update services.',
'Endpoint Engineering reviews repeated failures, rollback events or devices outside the compliance window.','devices'),
('Printer queue not available','Hardware','The office printer is missing or a print job remains queued.',
'Join the secure office network or approved VPN. Select the printer for your office in Company Portal. Confirm the printer has no local paper or toner alert. Cancel only your own stuck jobs and retry a small non-sensitive page.',
'Include the printer asset label, office and queue name. Do not attach confidential documents as examples.','printing'),
('Dock and external monitor not detected','Hardware','A monitor stays blank when connected through a USB-C dock.',
'Confirm the monitor power and input selection. Reconnect the display cable and dock once. Test the laptop display directly. Use only approved adapters and firmware from Company Portal. Save work before restarting.',
'Endpoint support checks dock model, power supply and display compatibility. Include device and dock asset IDs.','devices'),
('Meeting microphone not working','Software','Other meeting participants cannot hear the user.',
'Check the meeting app input device and mute control. Confirm operating-system microphone permission. Run the app test call. Disconnect unused audio devices and select the intended headset. Restart the app after saving work.',
'Provide app version, operating system and whether the problem also occurs in a test call. Do not record coworkers without permission.','meeting'),
('Meeting screen sharing unavailable','Software','The screen-share control is disabled or shows a permission error.',
'Check whether the meeting policy permits sharing. Grant only the required screen-recording permission to the approved app. Restart the app if the operating system requests it. Share a specific window to avoid exposing unrelated information.',
'Route policy restrictions to Collaboration Operations with the meeting type and the exact error.','meeting'),
('Cloud drive sync conflict','Software','A file shows a conflict copy or does not synchronize.',
'Pause editing the affected file. Check the cloud drive status and available storage. Compare file versions in the approved web interface. Preserve both copies before resolving differences. Resume sync after the conflict is resolved.',
'Escalate suspected data loss with the file identifier and version timestamps; do not upload business files into this public demo.','storage'),
('Restore a deleted work file','Software','A work document was accidentally deleted.',
'Check the managed cloud recycle bin and version history. Restore the intended version after confirming ownership. Avoid creating another file with the same name during recovery. If recovery is unavailable, stop changes and request storage support.',
'Provide the approximate deletion time and approved storage location. Retention and legal holds may affect recovery options.','storage'),
('Shared folder access denied','Identity','A known shared folder returns an access-denied error.',
'Confirm the approved work account and network connection. Check whether access was previously granted. Request access through the resource owner with a business justification. Never use another employee credentials to bypass the restriction.',
'The resource owner approves the access scope; Identity Operations provisions the approved group membership.','storage'),
('New employee onboarding','General','A new starter needs device setup and initial access.',
'Confirm the onboarding request has an approved start date and manager. Activate the work account through the verified welcome flow. Enroll MFA, sign into the assigned device and run Company Portal sync. Test email, meeting and VPN access.',
'Missing access goes to the relevant service owner with the onboarding request ID. No account or asset is provisioned automatically by this demo.','onboarding'),
('Employee offboarding request','Identity','A manager needs to schedule access removal and asset return.',
'Submit the approved offboarding request through HR operations. Confirm the effective time and asset-return instructions. Transfer work ownership using approved processes. Preserve required records and avoid sharing the departing employee password.',
'HR and Identity administrators coordinate revocation; sensitive departures follow the security incident process.','onboarding'),
('Suspicious phishing email','Identity','An email asks for credentials, urgent payment or an unexpected attachment.',
'Do not open links or attachments. Use the approved Report phishing action. If you already entered credentials, contact Security Operations immediately through a trusted channel. Preserve the original email for the security team.',
'Potential credential exposure is High priority. Do not forward malicious attachments to coworkers or upload them here.','security'),
('Unexpected MFA prompts','Identity','Authenticator approval requests arrive without a sign-in attempt.',
'Deny the prompts. Do not approve a request to make notifications stop. Contact Security Operations through a known channel. Review your account through the approved identity portal and follow their recovery instructions.',
'Treat repeated unsolicited prompts as a possible account compromise. Escalate with timestamps, never with the approval code.','security'),
('Developer repository access','Software','An engineer needs access to a project repository.',
'Request membership with the repository owner, team and required role. Use the managed single-sign-on account and enrolled MFA. Test read access after approval. Keep tokens in the approved secret manager and never paste them into chat.',
'Repository administrators grant the minimum approved role and review access periodically.','developer'),
('Internal portal unavailable','Network','The company portal returns an error or does not load.',
'Check the service snapshot. Confirm whether other sites work. Try a private browser window and the approved network. Record the error code and approximate time. Do not bypass certificate errors or use unverified mirror sites.',
'Application Operations needs the affected page path, error code and scope of impact. Avoid including query strings with private data.','intranet'),
('Business application access request','Software','A user needs a role in an internal business application.',
'Select the application from the service catalog. Specify the business role and duration required. Obtain resource-owner approval and any segregation-of-duties review. Test access only after provisioning is confirmed.',
'Application owners validate the role; privileged access requires a separate approved workflow.','business'),
]
def main():
    root = ROOT / 'knowledge_base'
    root.mkdir(exist_ok=True)
    for i, (title, category, symptoms, resolution, escalation, service) in enumerate(TOPICS, 1):
        for audience in ['employee', 'service-desk']:
            aid = f'NS-{i:03d}-' + ('E' if audience == 'employee' else 'S')
            heading = title if audience == 'employee' else title + ' — service desk runbook'
            steps = resolution if audience == 'employee' else (
                f'1. Confirm the reported symptom: {symptoms}\n'
                f'2. Establish scope: affected user count, managed asset, location and time of onset. Check the {service} service snapshot.\n'
                f'3. Guide the employee through the approved steps: {resolution}\n'
                f'4. Record which check changed the outcome. Do not mark resolved until the employee confirms the affected workflow works.\n'
                f'5. If unresolved: {escalation}')
            text = f"""# {heading}
Category: {category}
Article ID: {aid}
Owner: Northstar {category} Operations
Audience: {audience}
Version: 1.0
Reviewed: 2026-10-20
Review due: 2027-01-20
Service: {service}

> Fictional Northstar Systems policy for this public demonstration. Not instructions for a real employer.

## Symptoms
{symptoms}

## Prerequisites
Use a managed Northstar demo device and the approved work account. Check for an active service incident before changing local settings. Public demo actions never affect real accounts.

## Resolution
{steps}

## Validation
Repeat the original affected workflow once. Record whether it succeeds, the service involved and the time. If it still fails, keep the ticket open and document the exact remaining symptom.

## Escalation
{escalation}
Use High priority for multi-user disruption or suspected compromise, Medium for one blocked employee, and Low for a routine request with a workaround.

## Evidence and privacy
Record the asset identifier, error code and redacted diagnostic summary. Never collect passwords, recovery keys, MFA codes, private documents or full message contents.

## Related material
See the {service} service entry and the paired {'service-desk runbook' if audience == 'employee' else 'employee guide'} for {title.lower()}.
"""
            (root / f'{aid.lower()}.md').write_text(text, encoding='utf-8')
    rng = random.Random(20261020)
    base = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    depts = ['Engineering', 'Finance', 'People', 'Sales', 'Customer Success', 'Operations']
    offices = ['Bengaluru', 'Pune', 'London', 'Remote']
    first = ['Aarav','Maya','Ishan','Nora','Rohan','Leah','Arjun','Zoe','Kabir','Eva','Dev','Sara','Vihaan','Lina','Neil']
    last = ['Mehta','Shah','Rao','Kapoor','Sen','Patel','Malik','Das','Bose','Nair']
    employees = [{'id': f'E{1000+i}', 'name': f'{first[i%15]} {last[i//15]}', 'department': depts[i%6],
                  'office': offices[i%4], 'email': f'employee{i+1}@northstar.example', 'manager_id': f'E{1000+(i//10)*10}' if i%10 else None} for i in range(150)]
    assets = [{'id':f'AST-{i+1:04}', 'employee_id':employees[i%150]['id'], 'type': 'Laptop' if i < 150 else 'Dock' if i < 210 else 'Monitor',
               'model': ['ThinkPad T14', 'MacBook Pro 14', 'Latitude 5450'][i%3] if i < 150 else 'USB-C dock' if i < 210 else '27-inch display',
               'status':'In service', 'office':employees[i%150]['office']} for i in range(250)]
    service_names = [('vpn','Remote access VPN'),('wifi','Office Wi-Fi'),('email','Email & calendar'),('identity','Identity & MFA'),
        ('software','Software catalog'),('devices','Managed devices'),('printing','Office printing'),('meeting','Meetings & chat'),
        ('storage','Cloud drive'),('onboarding','Joiner / mover / leaver'),('security','Security response'),
        ('developer','Developer platform'),('intranet','Employee portal'),('business','Business applications'),
        ('hr','People platform'),('finance','Finance systems'),('crm','CRM'),('analytics','Analytics workspace'),
        ('backup','Backup & recovery'),('telephony','Voice services')]
    services = [{'id':key,'name':name,'status':'Degraded' if key=='wifi' else 'Operational','owner':name+' Operations',
                 'note':'Bengaluru floor 3 intermittent connections; use wired Ethernet.' if key=='wifi' else 'No active incident in this demo snapshot.',
                 'updated_at':base.isoformat()} for key,name in service_names]
    tickets = []
    for i in range(600):
        topic = TOPICS[i%len(TOPICS)]
        employee = employees[rng.randrange(150)]
        asset = assets[int(employee['id'][1:])-1000]
        created = base-timedelta(days=rng.randrange(3,90), hours=rng.randrange(24))
        status = rng.choices(['Resolved','In progress','Waiting for user','Open'],weights=[65,15,10,10])[0]
        priority = 'High' if i%17==0 else rng.choice(['Low','Medium','Medium'])
        scope = 'multiple employees at '+employee['office'] if priority=='High' else 'one employee'
        timeline = [{'at':created.isoformat(), 'event':'Request received', 'note':topic[2]},
                    {'at':(created+timedelta(minutes=rng.randrange(10,90))).isoformat(),'event':'Triage complete','note':f'Assigned to {topic[1]} Operations. Scope: {scope}.'}]
        if status=='Resolved':
            timeline.append({'at':(created+timedelta(hours=rng.randrange(2,48))).isoformat(),'event':'Resolution confirmed','note':topic[3]})
        elif status=='Waiting for user':
            timeline.append({'at':(created+timedelta(hours=2)).isoformat(),'event':'Awaiting validation','note':'Requested confirmation of the affected workflow after the suggested checks.'})
        tickets.append({'id':f'DEMO-{i+1:05}', 'summary':topic[0]+' - '+employee['office'], 'category':topic[1], 'service_id':topic[5],
            'employee_id':employee['id'],'requester':employee['name'],'department':employee['department'],'asset_id':asset['id'],
            'priority':priority,'status':status,
            'created_at':created.isoformat(),'article_id':f'ns-{i%30+1:03}-e','timeline':timeline})
    incidents = [{'id':f'SIM-{i+1:03}', 'service_id':'wifi' if i==0 else service_names[i%20][0],
        'title':'Bengaluru floor 3 wireless instability' if i==0 else f'{service_names[i%20][1]} scheduled maintenance',
        'status':'Investigating' if i==0 else 'Completed', 'impact':'Intermittent connectivity on floor 3; wired Ethernet is available.' if i==0 else 'Planned maintenance completed; service checks passed.',
        'updated_at':(base-timedelta(days=i)).isoformat()} for i in range(40)]
    data = {'company':{'name':'Northstar Systems','label':'Fictional organization','snapshot':'2026-10-20','description':'A distributed technology company with 150 synthetic employees across four locations.'},
            'employees':employees,'assets':assets,'tickets':tickets,'services':services,'incidents':incidents}
    (ROOT/'data'/'demo.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f'Generated 60 articles, {len(employees)} employees, {len(assets)} assets, {len(tickets)} tickets, {len(services)} services and {len(incidents)} incidents.')
if __name__=='__main__':
    main()
