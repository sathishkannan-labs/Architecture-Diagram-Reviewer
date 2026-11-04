"""Run intentionally from a terminal with MODEL_API_KEY set. Never records images/keys."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
from archreview.meta import MetaClient,ExtractionError
from archreview.config import load_local_env
load_local_env(Path(__file__).resolve().parents[1] / ".env")
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('image',type=Path)
parser.add_argument('--output',type=Path,default=Path('acceptance'))
args=parser.parse_args()
client=MetaClient()
result={'run_at':datetime.now(timezone.utc).isoformat(),'text':'not_run','image':'not_run','model':client.model}
try:
    client.text_probe();result['text']='passed'
    graph=client.extract(args.image.read_bytes());result['image']='passed'
    args.output.mkdir(exist_ok=True,parents=True)
    (args.output/'live-graph.json').write_text(graph.model_dump_json(indent=2))
except (ExtractionError,OSError) as exc:
    # Error class only: no filesystem names, provider body or request data.
    result['error_type']=type(exc).__name__
finally:
    client.close()
    args.output.mkdir(exist_ok=True,parents=True)
    (args.output/'live-acceptance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['image']=='passed' else 1)
