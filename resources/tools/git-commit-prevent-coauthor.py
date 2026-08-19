import json
import os

settings_dir = os.path.expanduser('~/.claude')
os.makedirs(settings_dir, exist_ok=True)
settings_file = os.path.join(settings_dir, 'settings.json')

config = {'attribution': {'commit': '', 'pr': ''}}

with open(settings_file, 'w') as f:
    json.dump(config, f, indent=2)