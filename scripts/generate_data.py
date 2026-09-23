"""Regenerate all synthetic fixtures. No real company or person data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['Cedar Workflow Rollout', 'Harbor Onboarding', 'Summit Data Migration', 'Orion Integration',
         'Meadow Service Expansion', 'Atlas Access Review', 'River Recovery', 'Beacon Platform Refresh',
         'Willow Knowledge Base', 'Juniper Reporting']


def build(baseline=False):
    tables = {k: [] for k in ('projects', 'tasks', 'risks', 'milestones', 'dependencies', 'budgets', 'stakeholders')}
    for n, name in enumerate(NAMES, 1):
        pid = f'P{n:02}'
        tables['projects'].append(dict(project_id=pid, project_name=name, project_manager=f'Demo PM {n:02}', currency='EUR'))
        # Branch fixtures: task count, milestone slip, risks, critical block, budget overrun.
        overdue = {1: 0, 2: 4, 3: 9, 4: 2, 5: 1, 6: 0, 7: 1, 8: 8, 9: 0, 10: 3}[n]
        slip = {1: 0, 2: 3, 3: 8, 4: 1, 5: 0, 6: 0, 7: 0, 8: 12, 9: 0, 10: 6}[n]
        if baseline and n == 7: overdue, slip = 9, 9
        if baseline and n == 8: overdue, slip = 0, 0
        for j in range(1, 13):
            done = j > max(overdue, 6)
            tables['tasks'].append(dict(task_id=f'{pid}-T{j:02}', project_id=pid,
                title=f'{name}: delivery item {j:02}', owner=f'Demo Workstream Owner {n:02}',
                due_date='2026-09-18' if j <= overdue else '2026-09-28', status='done' if done else 'in_progress'))
        for j in range(1, 4):
            severity = 'critical' if n == 6 and j == 1 else 'high' if n in (3, 8, 10) and j == 1 else 'medium'
            if baseline and n == 8: severity = 'medium'
            tables['risks'].append(dict(risk_id=f'{pid}-R{j}', project_id=pid,
                title=f'{name}: ' + ['supplier readiness uncertainty', 'review capacity constraint', 'handover knowledge gap'][j-1],
                owner=f'Demo Risk Owner {n:02}', severity=severity, status='closed' if j == 3 else 'open',
                impact='Acceptance or handover may be delayed', action='Confirm mitigation owner and response date'))
        for j in (1, 2):
            tables['milestones'].append(dict(milestone_id=f'{pid}-M{j}', project_id=pid,
                title=f'{name}: ' + ('release acceptance' if j == 1 else 'handover'),
                baseline_date='2026-09-20' if slip and j == 1 else '2026-09-28',
                forecast_date=f'2026-09-{20+slip:02}' if slip and j == 1 and 20+slip <= 30 else '2026-10-02' if slip and j == 1 else '2026-09-28',
                status='open'))
        for j in (1, 2):
            tables['dependencies'].append(dict(dependency_id=f'{pid}-D{j}', project_id=pid,
                title=f'{name}: ' + ('upstream interface approval' if j == 1 else 'training material'),
                owner=f'Demo Dependency Owner {n:02}', critical='true' if j == 1 else 'false',
                status='blocked' if (n == 4 and j == 1) or (n == 3 and j == 2) else 'ready',
                impact='Dependent delivery work cannot proceed', action='Agree an unblock date with the supplying team'))
        base = 100000 + n * 10000
        variance = 30 if n == 5 else 15 if n == 8 and not baseline else 0
        tables['budgets'].append(dict(project_id=pid, baseline=str(base), forecast=str(round(base * (1+variance/100))), actual=str(base//2)))
        for role in ('pm', 'pmo'):
            tables['stakeholders'].append(dict(stakeholder_id=f'{pid}-{role}', project_id=pid, role=role,
                name=f'Demo {role.upper()} {n:02}', email=f'{role}{n:02}@example.invalid'))
    return tables


def write(folder, tables):
    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with (folder / f'{name}.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
    write(ROOT/'data', build())
    write(ROOT/'data'/'baseline', build(True))
    print('Generated 10 projects, 120 tasks, 30 risks, 20 milestones, 20 dependencies, 10 budgets, 20 stakeholders per snapshot.')
