import subprocess

callback = r'''
import re
return re.sub(rb'(?i)^.*Co-Authored-By:.*\n?', b'', message, flags=re.MULTILINE)
'''

subprocess.run(['git', 'filter-repo', '--force', '--message-callback', callback])