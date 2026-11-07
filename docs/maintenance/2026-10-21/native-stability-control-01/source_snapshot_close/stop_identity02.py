import json, sys
from pathlib import Path
from identity02 import stop
value = json.loads(Path(sys.argv[1]).read_text())
print(json.dumps(dict(signalled=stop(value, sys.argv[2]))))
