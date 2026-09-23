"""Generate core-node n8n exports; credentials deliberately omitted, never invented."""
import json
import uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def node(name, kind, version, parameters, x, y=0, **extra):
    return {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'pmo-demo/' + name)), 'name': name,
            'type': 'n8n-nodes-base.' + kind, 'typeVersion': version, 'position': [x,y],
            'parameters': parameters, **extra}

def http(name, route, x, y=0, body=None):
    p = {'method': 'POST', 'url': 'http://hub-api:8000' + route, 'options': {'timeout': 240000}}
    if body is not None: p.update(sendBody=True, specifyBody='json', jsonBody=body)
    return node(name, 'httpRequest', 4.2, p, x, y, retryOnFail=True, maxTries=3, waitBetweenTries=2000)

def edge(connections, source, target, branch=0):
    outputs = connections.setdefault(source, {'main': []})['main']
    while len(outputs) <= branch: outputs.append([])
    outputs[branch].append({'node': target, 'type': 'main', 'index': 0})

def condition(name, value, x,y=0):
    return node(name,'if',2.2,{'conditions':{'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict','version':2},
        'conditions':[{'id':str(uuid.uuid5(uuid.NAMESPACE_URL,name)), 'leftValue':'={{ $json.mode }}','rightValue':value,
                       'operator':{'type':'string','operation':'equals'}}], 'combinator':'and'}, 'options':{}},x,y)

SPECS = [
 ('01-project-health-monitor', '01 · Project Health Monitor', '/monitor', '0 0 8 * * *', 'Read all mounted CSVs through the local service; validate, score and commit immutable daily snapshots. Frozen demo seeds a previous day once.'),
 ('02-risk-escalation', '02 · Risk & Escalation Engine', '/escalate', '0 * * * * *', 'Consume unprocessed snapshots chronologically. Create stable issue episodes; retries cannot duplicate escalation records.'),
 ('03-ai-status-report', '03 · AI-assisted Status Report', '/report', '10 * * * * *', 'Consume escalated snapshots. Deterministic reports work offline. Optional Ollama may reorder verified facts only; failures fall back.'),
 ('04-stakeholder-notification', '04 · Stakeholder Notification', '/notifications/claim', '20 * * * * *', 'Claim one durable outbox item. Default is simulation. Live branches are disabled until configured; read setup-guide.md.'),
 ('05-weekly-pmo-digest', '05 · Weekly PMO Digest', '/digest', '0 0 9 * * 1', 'Monday 09:00 Europe/Berlin. Summarize latest available snapshot, showing its as-of date, with one updated record per ISO week.'),
 ('06-analytics-pipeline', '06 · Analytics Dataset', '/analytics', '30 * * * * *', 'Export all immutable snapshots to /output/portfolio-health.csv; atomic file replacement and stable columns.')]

for filename,title,route,cron,notes in SPECS:
    nodes = [node('Manual demo','manualTrigger',1,{},0,0),
             node('Schedule','scheduleTrigger',1.2,{'rule':{'interval':[{'field':'cronExpression','expression':cron}]}},0,180),
             node('Read me','stickyNote',1,{'content':notes,'height':150,'width':500},200,-250),
             http('Run stage' if route != '/notifications/claim' else 'Claim notification', route, 270)]
    con = {}
    start = nodes[-1]['name']
    edge(con,'Manual demo',start);edge(con,'Schedule',start)
    if filename.startswith('04'):
        nodes += [condition('Simulation?', 'dry-run', 510),
                  condition('Email?', 'email', 1040),
                  node('Live delivery gate','code',2,{'jsCode':
                    '// Keep false until credentials, recipients and the selected send node are configured.\nconst ENABLE_LIVE_DELIVERY = false;\nif (!ENABLE_LIVE_DELIVERY) throw new Error("Live delivery is not configured. See docs/setup-guide.md");\nreturn $input.all();'},780,160),
                  node('Send email','emailSend',2.1,{'fromEmail':'demo-sender@example.invalid','toEmail':'={{ $json.recipients.join(",") }}',
                    'subject':'={{ $json.subject }}','emailFormat':'text','text':'={{ $json.body }}','options':{}},1320,80,
                       disabled=True,onError='continueErrorOutput',notes='CONFIGURATION REQUIRED: select an SMTP credential, set sender and test recipients, then enable.'),
                  node('Send Slack','slack',2.3,{'resource':'message','operation':'post','select':'channel',
                    'channelId':{'__rl':True,'mode':'id','value':'={{ $json.severity === "CRITICAL" ? "REPLACE_PMO_CHANNEL_ID" : "REPLACE_PM_CHANNEL_ID" }}'},
                    'messageType':'text','text':'={{ $json.subject + "\\n" + $json.body }}','otherOptions':{}},1320,350,
                       disabled=True,onError='continueErrorOutput',notes='CONFIGURATION REQUIRED: select Slack credential and channels, then enable. PMO channel must include PM and PMO reviewers.')]
        def ack(name,success,simulated,x,y):
            expr='={{ JSON.stringify({ notification_id: $("Claim notification").first().json.notification_id, lease_token: $("Claim notification").first().json.lease_token, success: '+str(success).lower()+', simulated: '+str(simulated).lower()+' }) }}'
            return http(name,'/notifications/ack',x,y,expr)
        nodes += [ack('Record simulation',True,True,790,-80),ack('Record delivery',True,False,1600,50),ack('Record failure',False,False,1600,350)]
        edge(con,start,'Simulation?');edge(con,'Simulation?','Record simulation',0);edge(con,'Simulation?','Live delivery gate',1)
        edge(con,'Live delivery gate','Email?');edge(con,'Email?','Send email',0);edge(con,'Email?','Send Slack',1)
        for sender in ('Send email','Send Slack'):
            edge(con,sender,'Record delivery',0);edge(con,sender,'Record failure',1)
    out = {'name':title,'nodes':nodes,'connections':con,'active':False,'settings':{'executionOrder':'v1','timezone':'Europe/Berlin'},'pinData':{},'tags':[]}
    (ROOT/'workflows'/f'{filename}.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print('Generated six inactive workflow exports.')
