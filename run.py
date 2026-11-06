"""Opaque-request runner. Inputs, code and outputs are private. No task data is logged."""
import os,sys,json,base64,urllib.request,tempfile,subprocess

def main():
    token=os.environ['ACCESS_TOKEN'];repo=os.environ['PRIVATE_CODE_REPO'];state=os.environ['PRIVATE_STATE_REPO']
    event=json.load(open(os.environ['GITHUB_EVENT_PATH']))
    rid=event.get('client_payload',{}).get('request_id','')
    if len(rid)!=32 or not all(c in '0123456789abcdef' for c in rid):return 2
    def get(path):
        req=urllib.request.Request('https://api.github.com/repos/'+path,headers={'Authorization':'Bearer '+token,'User-Agent':'opaque-runner'})
        with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
    j=get(state+'/contents/requests/'+rid+'.json');job=json.loads(base64.b64decode(j['content']))
    j=get(repo+'/contents/bot.py');code=base64.b64decode(j['content'])
    env=dict(os.environ);env.update({'GITHUB_REPOSITORY':repo,'DISPATCH_PAT':token,'GITHUB_TOKEN':token})
    for key in ('kind','text','chat_id','msg_id','research_err'):env['JOB_'+key.upper()]=str(job.get(key,''))
    env['JOB_RESEARCH_HITS']=json.dumps(job.get('research_hits') or [])
    with tempfile.TemporaryDirectory() as d:
        path=os.path.join(d,'job.py');open(path,'wb').write(code)
        with open(os.devnull,'wb') as sink:
            result=subprocess.run([sys.executable,path],cwd=d,env=env,stdout=sink,stderr=sink,timeout=450)
    # Never print subprocess output or exceptions. Status stays generic.
    print('Job completed.' if result.returncode==0 else 'Job failed. Details remain private.')
    return result.returncode
if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        print('Job could not complete. Details remain private.');sys.exit(1)
