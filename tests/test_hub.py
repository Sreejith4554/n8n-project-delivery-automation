import copy
import json
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from service.engine import load_data, score_all, issues, render_report, facts
from service.store import Hub, ollama_order
from service.server import make_handler

ROOT = Path(__file__).resolve().parents[1]
DAY = '2026-09-23'

class Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data(ROOT/'data')
        cls.scores = {s['project_id']: s for s in score_all(cls.data,DAY)}

    def test_healthy(self):
        self.assertEqual((self.scores['P01']['project_status'],self.scores['P01']['health_score']),('HEALTHY',100))
    def test_at_risk(self): self.assertEqual(self.scores['P02']['project_status'],'AT RISK')
    def test_critical_overdue_tasks(self):
        self.assertEqual(self.scores['P03']['project_status'],'CRITICAL')
        self.assertEqual(self.scores['P03']['overdue_tasks'],9)
    def test_overdue_milestone(self):
        s=self.scores['P10']; self.assertEqual(s['milestone_variance_days'],6)
        self.assertTrue(any(i['issue_key'].endswith('M1') for i in issues(s)))
    def test_critical_dependency_override(self):
        self.assertEqual(self.scores['P04']['health_score'],59)
        self.assertIn('Blocked critical dependency',self.scores['P04']['overrides'])
    def test_budget_forecast_overrun(self):
        self.assertEqual(self.scores['P05']['budget_variance_percentage'],30)
        self.assertEqual(self.scores['P05']['project_status'],'CRITICAL')
    def test_critical_risk_override(self):
        self.assertEqual(self.scores['P06']['health_score'],59)
        self.assertTrue(any(i['escalation_level']=='L2-PMO' for i in issues(self.scores['P06'])))
    def test_missing_required_field(self):
        data=copy.deepcopy(self.data);del data['tasks'][0]['due_date']
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_invalid_date(self):
        data=copy.deepcopy(self.data);data['tasks'][0]['due_date']='2026-02-30'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_zero_budget(self):
        data=copy.deepcopy(self.data);data['budgets'][0]['baseline']='0'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_nan_budget(self):
        data=copy.deepcopy(self.data);data['budgets'][0]['forecast']='NaN'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_orphan_reference(self):
        data=copy.deepcopy(self.data);data['tasks'][0]['project_id']='missing'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_duplicate_source_id(self):
        data=copy.deepcopy(self.data);data['tasks'].append(data['tasks'][0])
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_missing_tasks_not_healthy(self):
        data=copy.deepcopy(self.data);data['tasks']=[t for t in data['tasks'] if t['project_id']!='P01']
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_path_like_id_rejected(self):
        data=copy.deepcopy(self.data);data['projects'][0]['project_id']='../../escape'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_invalid_as_of(self):
        with self.assertRaises(ValueError):score_all(self.data,'20260923')
    def test_forecast_below_actual_rejected(self):
        data=copy.deepcopy(self.data);data['budgets'][0]['forecast']='1'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_missing_stakeholder_rejected(self):
        data=copy.deepcopy(self.data);data['stakeholders']=[]
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_empty_portfolio(self):
        self.assertEqual(score_all({k:[] for k in self.data},DAY),[])
    def test_due_today_not_overdue(self):
        data=copy.deepcopy(self.data)
        for t in data['tasks']:t['due_date']=DAY
        self.assertTrue(all(s['overdue_tasks']==0 for s in score_all(data,DAY)))
    def test_closed_critical_risk_not_escalated(self):
        data=copy.deepcopy(self.data)
        for r in data['risks']:r['status']='closed'
        self.assertEqual(score_all(data,DAY)[5]['high_risks'],0)
    def test_unknown_status_rejected(self):
        data=copy.deepcopy(self.data);data['tasks'][0]['status']='Done'
        with self.assertRaises(ValueError):score_all(data,DAY)
    def test_ai_fact_invention_rejected(self):
        with self.assertRaises(ValueError):render_report(self.scores['P01'],['invented'])
    def test_ai_duplicate_fact_rejected(self):
        keys=list(facts(self.scores['P01']));keys[0]=keys[1]
        with self.assertRaises(ValueError):render_report(self.scores['P01'],keys)
    def test_report_covers_every_required_section(self):
        report=render_report(self.scores['P01'])
        for section in ('Overall status','Progress','Milestones','Completed work','Overdue work','Top unresolved risks','Blocked dependencies','Budget','Required decisions','Recommended next actions'):
            self.assertIn(section,report)

class Persistence(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.hub=Hub(ROOT/'data',Path(self.temp.name)/'state',Path(self.temp.name)/'output')
    def tearDown(self):self.temp.cleanup()
    def prepare(self):
        self.hub.monitor(DAY);self.hub.escalate();self.hub.report()
    def test_duplicate_execution(self):
        self.prepare();before=self.hub.status()
        self.hub.monitor(DAY);self.hub.escalate();self.hub.report()
        self.assertEqual(before,self.hub.status())
    def test_changed_data_same_day_conflict(self):
        self.hub.monitor(DAY)
        with self.assertRaises(ValueError):self.hub.monitor(DAY,ROOT/'data'/'baseline')
    def test_out_of_order_rejected(self):
        self.hub.monitor(DAY)
        with self.assertRaises(ValueError):self.hub.monitor('2026-09-22')
    def test_trends_computed_from_real_prior_snapshot(self):
        self.hub.monitor('2026-09-22',ROOT/'data'/'baseline');self.hub.monitor(DAY)
        with self.hub.connect() as c:
            get=lambda p:json.loads(c.execute('SELECT payload FROM snapshots WHERE id=?',(DAY+':'+p,)).fetchone()[0])
            self.assertEqual(get('P07')['trend'],'IMPROVING');self.assertEqual(get('P08')['trend'],'DETERIORATING')
    def test_unresolved_issue_dedup_across_days(self):
        self.hub.monitor(DAY);self.hub.escalate();n=self.hub.status()['escalations']
        self.hub.monitor('2026-09-24');self.hub.escalate()
        self.assertEqual(n,self.hub.status()['escalations'])
    def test_resolved_then_reopened_issue(self):
        self.hub.monitor(DAY);self.hub.escalate()
        from scripts.generate_data import build, write
        folder=Path(self.temp.name)/'changed';data=build()
        for r in data['risks']:
            if r['project_id']=='P06':r['status']='closed'
        write(folder,data);self.hub.monitor('2026-09-24',folder);self.hub.escalate()
        self.hub.monitor('2026-09-25');self.hub.escalate()
        with self.hub.connect() as c:
            count=c.execute("SELECT COUNT(*) FROM escalations WHERE id LIKE 'P06:P06-R1:%'").fetchone()[0]
            self.assertEqual(count,2)
    def test_severity_change_new_episode(self):
        self.hub.monitor(DAY);self.hub.escalate()
        from scripts.generate_data import build, write
        data=build();folder=Path(self.temp.name)/'changed'
        for r in data['risks']:
            if r['risk_id']=='P10-R1':r['severity']='critical'
        write(folder,data);self.hub.monitor('2026-09-24',folder);self.hub.escalate()
        with self.hub.connect() as c:
            count=c.execute("SELECT COUNT(*) FROM escalations WHERE id LIKE 'P10:P10-R1:%'").fetchone()[0]
            self.assertEqual(count,2)
    def test_ai_unavailable(self):
        self.hub.monitor(DAY);self.hub.escalate()
        def fail(_):raise TimeoutError()
        self.assertEqual(self.hub.report(fail)['fallbacks'],10)
        self.assertEqual(self.hub.status()['reports'],10)
    def test_ai_invalid_response_fallback(self):
        self.hub.monitor(DAY);self.hub.escalate()
        self.assertEqual(self.hub.report(lambda _:['invented'])['fallbacks'],10)
    def test_ai_valid_permutation(self):
        self.hub.monitor(DAY);self.hub.escalate()
        self.assertEqual(self.hub.report(lambda f:list(reversed(f)))['fallbacks'],0)
        with self.hub.connect() as c:self.assertEqual(c.execute('SELECT mode FROM reports LIMIT 1').fetchone()[0],'ollama-fact-ordering')
    def test_notification_failure_retained(self):
        self.prepare();item=self.hub.claim()[0]
        self.hub.ack(item['notification_id'],item['lease_token'],False)
        with self.hub.connect() as c:
            row=c.execute('SELECT * FROM outbox WHERE id=?',(item['notification_id'],)).fetchone()
            self.assertEqual(row['state'],'pending');self.assertGreater(row['lease_until'],time.time())
    def test_duplicate_ack(self):
        self.prepare();item=self.hub.claim()[0]
        self.hub.ack(item['notification_id'],item['lease_token'],True,True)
        self.assertEqual(self.hub.ack(item['notification_id'],item['lease_token'],True,True),{'duplicate':True})
    def test_stale_ack_rejected(self):
        self.prepare();item=self.hub.claim()[0]
        with self.assertRaises(ValueError):self.hub.ack(item['notification_id'],'wrong',True)
    def test_concurrent_claims_unique(self):
        self.prepare()
        with ThreadPoolExecutor(6) as pool:
            values=[x[0]['notification_id'] for x in pool.map(lambda _:self.hub.claim(),range(6)) if x]
        self.assertEqual(len(values),len(set(values)))
    def test_lease_expiry_recovery(self):
        self.prepare();item=self.hub.claim()[0]
        with self.hub.connect() as c:c.execute('UPDATE outbox SET lease_until=0 WHERE id=?',(item['notification_id'],))
        next_item=self.hub.claim()[0]
        self.assertEqual(item['notification_id'],next_item['notification_id'])
        self.assertNotEqual(item['lease_token'],next_item['lease_token'])
    def test_fifth_failed_attempt_dead_letter(self):
        self.prepare();item=self.hub.claim()[0]
        with self.hub.connect() as c:c.execute('UPDATE outbox SET attempts=5 WHERE id=?',(item['notification_id'],))
        self.hub.ack(item['notification_id'],item['lease_token'],False)
        self.assertEqual(self.hub.status()['notifications']['dead'],1)
    def test_final_expired_lease_dead_letter(self):
        self.prepare();item=self.hub.claim()[0]
        with self.hub.connect() as c:c.execute('UPDATE outbox SET attempts=5,lease_until=0 WHERE id=?',(item['notification_id'],))
        self.hub.claim();self.assertEqual(self.hub.status()['notifications']['dead'],1)
    def test_healthy_has_no_notification(self):
        self.prepare()
        with self.hub.connect() as c:self.assertEqual(c.execute("SELECT COUNT(*) FROM outbox WHERE snapshot LIKE '%:P01'").fetchone()[0],0)
    def test_critical_recipients_include_pmo(self):
        self.prepare()
        with self.hub.connect() as c:
            p=json.loads(c.execute("SELECT payload FROM outbox WHERE snapshot LIKE '%:P06'").fetchone()[0])
            self.assertEqual(p['recipients'],['pm06@example.invalid','pmo06@example.invalid'])
    def test_at_risk_pm_only(self):
        self.prepare()
        with self.hub.connect() as c:
            p=json.loads(c.execute("SELECT payload FROM outbox WHERE snapshot LIKE '%:P02'").fetchone()[0])
            self.assertEqual(p['recipients'],['pm02@example.invalid'])
    def test_empty_queue(self):self.assertEqual(self.hub.claim(),[])
    def test_partial_stage_recovery(self):
        self.hub.monitor(DAY)
        self.assertEqual(self.hub.report()['created'],0)
        # New process/connection uses the durable checkpoint.
        restarted=Hub(ROOT/'data',Path(self.temp.name)/'state',Path(self.temp.name)/'output')
        restarted.escalate();self.assertEqual(restarted.report()['created'],10)
    def test_csv_export_idempotent(self):
        self.prepare();self.hub.analytics()
        p=Path(self.temp.name)/'output'/'portfolio-health.csv';before=p.read_bytes()
        self.hub.analytics();self.assertEqual(before,p.read_bytes())
    def test_digest_counts_and_upsert(self):
        self.prepare();d=self.hub.digest();self.hub.digest()
        self.assertEqual(d['total_projects'],10)
        self.assertEqual(d['healthy_projects']+d['at_risk_projects']+d['critical_projects'],10)
        with self.hub.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM digests').fetchone()[0],1)
    def test_empty_digest(self):self.assertEqual(self.hub.digest()['total_projects'],0)

class HTTPIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.hub=Hub(ROOT/'data',self.temp.name,Path(self.temp.name)/'output')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.hub))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def post(self,path,body=None):
        with urlopen(Request(self.base+path,json.dumps(body or {}).encode(),{'Content-Type':'application/json'}),timeout=5) as r:return json.load(r)
    def test_http_pipeline(self):
        with patch.dict(os.environ,{'DEMO_AS_OF':DAY,'OLLAMA_ENABLED':'false','NOTIFICATION_MODE':'dry-run'}):
            self.assertEqual(self.post('/monitor')['created'],10)
            self.post('/escalate');self.assertEqual(self.post('/report')['created'],20)
            while items:=self.post('/notifications/claim'):
                item=items[0];self.post('/notifications/ack',{**item,'success':True,'simulated':True})
            self.assertEqual(self.post('/analytics')['rows'],20)
            self.assertEqual(self.post('/digest')['total_projects'],10)
            with urlopen(self.base+'/health') as r:self.assertEqual(json.load(r)['snapshots'],20)
    def test_unknown_route(self):
        with self.assertRaises(HTTPError) as ctx:self.post('/missing')
        self.assertEqual(ctx.exception.code,404)
    def test_invalid_ack_returns_422(self):
        with self.assertRaises(HTTPError) as ctx:self.post('/notifications/ack',{'success':'true'})
        self.assertEqual(ctx.exception.code,422)
    def test_ollama_transport_failure(self):
        with patch('service.store.urlopen',side_effect=TimeoutError()):
            with self.assertRaises(TimeoutError):ollama_order({'status':'healthy'})

if __name__=='__main__':unittest.main()
