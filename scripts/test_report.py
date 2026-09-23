"""Run real assertions and save machine-readable plus Markdown test evidence."""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class Evidence(unittest.TextTestResult):
    def startTestRun(self):self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.records.append({'test':test.id(),'expected':'Assertions pass','actual':'PASS'})
    def addFailure(self,test,err):
        super().addFailure(test,err);self.records.append({'test':test.id(),'expected':'Assertions pass','actual':'FAIL','detail':self._exc_info_to_string(err,test)})
    def addError(self,test,err):
        super().addError(test,err);self.records.append({'test':test.id(),'expected':'Assertions pass','actual':'ERROR','detail':self._exc_info_to_string(err,test)})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2,resultclass=Evidence).run(suite)
    evidence={'executed_at':datetime.now(timezone.utc).isoformat(),'scope':'Python business rules and local HTTP service; NOT an n8n execution',
        'python':sys.version.split()[0],'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'results':result.records}
    (ROOT/'docs'/'test-results.json').write_text(json.dumps(evidence,indent=2)+'\n')
    text='# Executed test evidence\n\n'+evidence['scope']+'\n\nExecuted: '+evidence['executed_at']+'\n\n| Test | Expected | Actual |\n|---|---|---|\n'
    text+='\n'.join(f'| `{r["test"]}` | {r["expected"]} | {r["actual"]} |' for r in result.records)+'\n'
    (ROOT/'docs'/'test-results.md').write_text(text)
    sys.exit(not result.wasSuccessful())
