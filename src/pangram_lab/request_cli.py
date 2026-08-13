from pathlib import Path
import json
from .closeout_request import process_request

def main() -> int:
    root=Path.cwd()
    folder=root/'state'/'lesson-closeout-requests'
    done=[]
    if folder.exists():
        for path in sorted(folder.glob('*.json')):
            obj=json.loads(path.read_text(encoding='utf-8'))
            if obj.get('status')=='processed':
                continue
            entry=process_request(root,path)
            done.append({'request':str(path.relative_to(root)),'ledger_entry_id':entry['id']})
    print(json.dumps({'processed':done},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
