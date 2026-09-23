"""Focused static export lint. Does NOT replace import/execution in n8n."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSIONS={'manualTrigger':1,'scheduleTrigger':1.2,'stickyNote':1,'httpRequest':4.2,'if':2.2,'code':2,'emailSend':2.1,'slack':2.3}

def main():
    files=sorted((ROOT/'workflows').glob('*.json'))
    assert len(files)==6
    for path in files:
        flow=json.loads(path.read_text(encoding='utf-8'))
        assert flow['active'] is False and flow['settings']['timezone']=='Europe/Berlin'
        names={n['name'] for n in flow['nodes']}
        assert len(names)==len(flow['nodes'])
        assert len({n['id'] for n in flow['nodes']})==len(flow['nodes'])
        for node in flow['nodes']:
            assert 'credentials' not in node, 'Exports must not contain credentials or fake credential IDs'
            kind=node['type'].removeprefix('n8n-nodes-base.')
            assert kind in VERSIONS and node['typeVersion']==VERSIONS[kind]
            assert len(node['position'])==2
            params=node['parameters']
            if kind=='httpRequest':
                assert params['method']=='POST'
                assert params['url'].startswith('http://hub-api:8000/')
                if params.get('sendBody'):
                    assert params['specifyBody']=='json'
                    expr=params['jsonBody'];assert expr.startswith('={{ ') and expr.endswith(' }}')
                    # Parse expression with a mock n8n item accessor and inspect actual acknowledgement JSON.
                    code='const $=()=>({first:()=>({json:{notification_id:"id",lease_token:"token"}})}); const result='+expr[3:-2]+'; const b=JSON.parse(result); if(typeof b.success!=="boolean" || b.notification_id!=="id")throw Error("Invalid acknowledgement");'
                    subprocess.run(['node','-e',code],check=True,capture_output=True)
            if kind=='code':
                subprocess.run(['node','-e','new Function('+json.dumps(params['jsCode'])+');'],check=True,capture_output=True)
            if kind in ('emailSend','slack'):assert node['disabled'] and node['onError']=='continueErrorOutput'
        for source,channels in flow['connections'].items():
            assert source in names
            for group in channels['main']:
                for e in group: assert e['node'] in names and e['type']=='main' and e['index']==0
        print(f'PASS {path.name}: {len(flow["nodes"])} nodes; connections, selected versions and expressions checked')
    print('Static inspection only. REQUIRES LOCAL N8N VALIDATION: import, node UI, credentials, scheduler and execution.')

if __name__=='__main__':main()
