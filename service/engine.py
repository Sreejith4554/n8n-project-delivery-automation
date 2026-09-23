"""Pure, deterministic PMO rules. All input data in this repository is synthetic."""
import csv
import math
import re
from datetime import date, timedelta
from pathlib import Path

SCHEMAS = {
    'projects': ('project_id', 'project_name', 'project_manager', 'currency'),
    'tasks': ('task_id', 'project_id', 'title', 'owner', 'due_date', 'status'),
    'risks': ('risk_id', 'project_id', 'title', 'owner', 'severity', 'status', 'impact', 'action'),
    'milestones': ('milestone_id', 'project_id', 'title', 'baseline_date', 'forecast_date', 'status'),
    'dependencies': ('dependency_id', 'project_id', 'title', 'owner', 'critical', 'status', 'impact', 'action'),
    'budgets': ('project_id', 'baseline', 'forecast', 'actual'),
    'stakeholders': ('stakeholder_id', 'project_id', 'role', 'name', 'email'),
}
ENUMS = {
    'tasks': {'status': {'open', 'in_progress', 'done'}},
    'risks': {'status': {'open', 'mitigating', 'closed'}, 'severity': {'low', 'medium', 'high', 'critical'}},
    'milestones': {'status': {'open', 'done'}},
    'dependencies': {'critical': {'true', 'false'}, 'status': {'ready', 'blocked', 'resolved'}},
    'stakeholders': {'role': {'pm', 'pmo'}},
}


def load_data(folder):
    data = {}
    for table in SCHEMAS:
        with (Path(folder) / f'{table}.csv').open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            if not set(SCHEMAS[table]).issubset(reader.fieldnames or []):
                raise ValueError(f'{table}: missing columns')
            data[table] = [{k: (v or '').strip() for k, v in row.items() if k} for row in reader]
    validate(data)
    return data


def validate(data):
    """Reject the complete batch on bad data; never report missing data as healthy."""
    for table, fields in SCHEMAS.items():
        if table not in data:
            raise ValueError(f'{table}: missing table')
        seen = set()
        for row in data[table]:
            if any(not isinstance(row.get(f), str) or not row[f].strip() for f in fields):
                raise ValueError(f'{table}: missing required value')
            key = row[fields[0]]
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', key):
                raise ValueError(f'{table}: ID must use only letters, numbers, underscores or hyphens')
            if key in seen:
                raise ValueError(f'{table}: duplicate ID {key}')
            seen.add(key)
            for field, allowed in ENUMS.get(table, {}).items():
                if row[field] not in allowed:
                    raise ValueError(f'{table}: invalid {field}')
            for field in fields:
                if field.endswith('_date'):
                    try:
                        parsed = date.fromisoformat(row[field])
                        if parsed.isoformat() != row[field]:
                            raise ValueError()
                    except ValueError:
                        raise ValueError(f'{table}: invalid ISO date') from None
    ids = {p['project_id'] for p in data['projects']}
    for table, rows in data.items():
        if table != 'projects' and any(r['project_id'] not in ids for r in rows):
            raise ValueError(f'{table}: orphan project reference')
    for budget in data['budgets']:
        for field in ('baseline', 'forecast', 'actual'):
            value = float(budget[field])
            if not math.isfinite(value) or value < 0 or (field == 'baseline' and value == 0):
                raise ValueError('budgets: baseline must be positive; amounts finite and nonnegative')
        if float(budget['forecast']) < float(budget['actual']):
            raise ValueError('budgets: forecast must include actual spend')
    for p in data['projects']:
        pid = p['project_id']
        if not any(t['project_id'] == pid for t in data['tasks']):
            raise ValueError(f'{pid}: tasks missing')
        if sum(b['project_id'] == pid for b in data['budgets']) != 1:
            raise ValueError(f'{pid}: exactly one budget required')
        for role in ('pm', 'pmo'):
            if not any(s['project_id'] == pid and s['role'] == role for s in data['stakeholders']):
                raise ValueError(f'{pid}: {role} stakeholder missing')


def score_all(data, as_of):
    validate(data)
    day = date.fromisoformat(as_of)
    if day.isoformat() != as_of:
        raise ValueError('As-of date must be YYYY-MM-DD')
    results = []
    for project in data['projects']:
        pid = project['project_id']
        group = {table: [r for r in data[table] if r['project_id'] == pid] for table in SCHEMAS if table != 'projects'}
        tasks = group['tasks']
        overdue = [t for t in tasks if t['status'] != 'done' and date.fromisoformat(t['due_date']) < day]
        risks = [r for r in group['risks'] if r['status'] != 'closed' and r['severity'] in ('high', 'critical')]
        blocked = [d for d in group['dependencies'] if d['status'] == 'blocked']
        milestones = []
        for m in group['milestones']:
            if m['status'] != 'done':
                variance = max(0, (max(date.fromisoformat(m['forecast_date']), day) - date.fromisoformat(m['baseline_date'])).days)
                milestones.append({**m, 'variance_days': variance, 'overdue': m['baseline_date'] < as_of})
        max_slip = max((m['variance_days'] for m in milestones), default=0)
        b = group['budgets'][0]
        variance = round((float(b['forecast']) - float(b['baseline'])) / float(b['baseline']) * 100, 2)
        overdue_pct = 100 * len(overdue) / len(tasks)
        penalties = {
            'overdue_work': round(min(30, overdue_pct * .6), 2),
            'milestones': min(20, max_slip * 2),
            'risks': min(20, sum(15 if r['severity'] == 'critical' else 8 for r in risks)),
            'dependencies': min(15, sum(15 if d['critical'] == 'true' else 5 for d in blocked)),
            'budget': round(min(15, max(0, variance) * .75), 2),
        }
        score = max(0, round(100 - sum(penalties.values())))
        overrides = []
        if any(r['severity'] == 'critical' for r in risks): overrides.append('Unresolved critical risk')
        if any(d['critical'] == 'true' for d in blocked): overrides.append('Blocked critical dependency')
        if variance > 20: overrides.append('Forecast budget overrun >20%')
        if max_slip > 10: overrides.append('Milestone slippage >10 days')
        if overrides: score = min(score, 59)
        elif risks or max_slip > 5 or variance > 10: score = min(score, 79)
        status = 'HEALTHY' if score >= 80 else 'AT RISK' if score >= 60 else 'CRITICAL'
        results.append({
            **project, 'snapshot_date': as_of, 'project_status': status, 'health_score': score,
            'progress_percentage': round(100 * sum(t['status'] == 'done' for t in tasks) / len(tasks), 2),
            'overdue_tasks': len(overdue), 'total_tasks': len(tasks), 'overdue_task_percentage': round(overdue_pct, 2),
            'high_risks': len(risks), 'blocked_dependencies': len(blocked),
            'milestone_variance_days': max_slip, 'budget_variance_percentage': variance,
            'overdue_milestones': sum(m['overdue'] for m in milestones),
            'penalties': penalties, 'overrides': overrides, 'overdue_work': overdue,
            'top_risks': risks, 'blocked': blocked, 'milestones': milestones,
            'accomplishments': [t['title'] for t in tasks if t['status'] == 'done'],
            'budget': b, 'stakeholders': group['stakeholders'],
        })
    return results


def issues(s):
    """Stable issue identities, independent of daily report dates."""
    out = []
    def add(key, title, owner, impact, action, severe=False):
        out.append({'issue_key': f"{s['project_id']}:{key}", 'project_id': s['project_id'],
                    'project': s['project_name'], 'issue': title, 'severity': 'CRITICAL' if severe else 'HIGH',
                    'owner': owner, 'impact': impact, 'required_action': action,
                    'due_date': (date.fromisoformat(s['snapshot_date']) + timedelta(days=1 if severe else 2)).isoformat(),
                    'escalation_level': 'L2-PMO' if severe else 'L1-PM'})
    if s['project_status'] == 'CRITICAL':
        add('health', 'Project health is critical', s['project_manager'], 'Delivery confidence reduced', 'Agree a recovery plan and accountable owners', True)
    for m in s['milestones']:
        if m['variance_days'] > 5:
            add(m['milestone_id'], m['title'], s['project_manager'], f"{m['variance_days']} days beyond baseline", 'Confirm recovery or request baseline change', m['variance_days'] > 10)
    for r in s['top_risks']:
        add(r['risk_id'], r['title'], r['owner'], r['impact'], r['action'], r['severity'] == 'critical')
    for d in s['blocked']:
        if d['critical'] == 'true': add(d['dependency_id'], d['title'], d['owner'], d['impact'], d['action'], True)
    if s['budget_variance_percentage'] > 10:
        add('budget', 'Forecast budget overrun', s['project_manager'], f"{s['budget_variance_percentage']}% forecast variance", 'Approve cost containment or a funding decision', s['budget_variance_percentage'] > 20)
    return out


def facts(s):
    """Every report line is trusted deterministic text, addressable by fact ID."""
    return {
        'status': f"Overall status: {s['project_status']}; health score {s['health_score']}/100.",
        'progress': f"Progress: {s['progress_percentage']}% of tasks completed (unweighted task count).",
        'milestones': f"Milestones: {s['overdue_milestones']} overdue; maximum open milestone variance {s['milestone_variance_days']} days.",
        'accomplishments': 'Completed work to date: ' + ('; '.join(s['accomplishments'][:3]) or 'None recorded.'),
        'overdue': f"Overdue work: {s['overdue_tasks']}/{s['total_tasks']} tasks. " + '; '.join(t['title'] for t in s['overdue_work'][:3]),
        'risks': 'Top unresolved risks: ' + ('; '.join(r['title'] for r in s['top_risks']) or 'None recorded.'),
        'dependencies': 'Blocked dependencies: ' + ('; '.join(d['title'] for d in s['blocked']) or 'None recorded.'),
        'budget': f"Budget: baseline {s['budget']['baseline']} {s['currency']}; forecast {s['budget']['forecast']} {s['currency']}; actual {s['budget']['actual']} {s['currency']}; forecast variance {s['budget_variance_percentage']}%.",
        'decisions': 'Required decisions (rule-derived): ' + ('; '.join(dict.fromkeys(i['required_action'] for i in issues(s))) or 'No threshold-triggered decision.'),
        'actions': 'Recommended next actions (rule-derived): ' + ('Confirm owners and recovery dates for outstanding work.' if s['project_status'] != 'HEALTHY' else 'Maintain the delivery cadence and review new exceptions.'),
    }


def render_report(s, order=None):
    f = facts(s)
    keys = order or list(f)
    # LLM can reorder facts, but cannot add, omit, duplicate, or rewrite them.
    if len(keys) != len(f) or set(keys) != set(f):
        raise ValueError('AI output must be an exact permutation of fact IDs')
    return f"# {s['project_name']}\n\nSynthetic portfolio demonstration · {s['snapshot_date']}\n\n" + '\n\n'.join(f[k] for k in keys) + '\n'
