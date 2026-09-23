"""Run the same service logic without n8n or Docker; write reproducible demo artifacts."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service.store import Hub
ROOT = Path(__file__).resolve().parents[1]

def run(output):
    with tempfile.TemporaryDirectory() as state:
        h = Hub(ROOT/'data', state, output)
        h.monitor('2026-09-22', ROOT/'data'/'baseline')
        h.monitor('2026-09-23')
        h.escalate(); h.report(); h.analytics(); digest=h.digest()
        while batch := h.claim():
            item=batch[0]
            h.ack(item['notification_id'], item['lease_token'], True, True)
        with h.connect() as c:
            report=c.execute("SELECT body FROM reports WHERE snapshot='2026-09-23:P06'").fetchone()[0]
            escalation=json.loads(c.execute("SELECT payload FROM escalations WHERE id='P06:P06-R1:1'").fetchone()[0])
        (output/'weekly-status-report.md').write_text(report, encoding='utf-8')
        (output/'critical-escalation.md').write_text('# Synthetic critical escalation\n\n'+'\n'.join(f'- **{k}**: {v}' for k,v in escalation.items())+'\n',encoding='utf-8')
        (output/'critical-escalation.json').write_text(json.dumps(escalation,indent=2)+'\n',encoding='utf-8')
        (output/'demo-result.json').write_text(json.dumps(h.status(),indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in digest.items() if k not in ('actions','markdown')},indent=2))

if __name__ == '__main__':
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'output'
    out.mkdir(parents=True,exist_ok=True); run(out)
