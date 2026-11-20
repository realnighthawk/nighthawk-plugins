import sys
from pathlib import Path

# A skill's scripts import their siblings by name; the skill directory is the working directory when the agent runs them.
for scripts in Path(__file__).resolve().parent.parent.glob("skills/*/scripts"):
    sys.path.insert(0, str(scripts))
