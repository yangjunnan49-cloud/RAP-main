import importlib.util
import os
from pathlib import Path
import sys

DOCX_PY = Path(r"C:/Users/AAA/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py")
NODE = os.environ["KIMI_DESKTOP_RUNTIME_NODE"]
spec = importlib.util.spec_from_file_location("kimi_word_docx", DOCX_PY)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original_run = module.run


def run_with_desktop_node(cmd, **kwargs):
    if cmd and cmd[0] == "node":
        cmd = [NODE, *cmd[1:]]
        env = dict(kwargs.get("env") or os.environ)
        env["ELECTRON_RUN_AS_NODE"] = "1"
        kwargs["env"] = env
    return original_run(cmd, **kwargs)


module.run = run_with_desktop_node
sys.argv = [str(DOCX_PY), *sys.argv[1:]]
module.main()
