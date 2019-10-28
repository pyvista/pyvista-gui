"""Options for saving user prefences, etc.
"""
import json
import os

import pyvista


class RcParams(dict):
    """Internally used class to manage the rcParams"""

    filename = os.path.join(pyvista.USER_DATA_PATH, 'rcParams.json')

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self, f)
        return

    def load(self):
        with open(self.filename, 'r') as f:
            data = json.load(f)
        self.update(data)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.save()

# The options
rcParams = RcParams(
    dark_mode=False,
)

# Load user prefences from last session if none exist, save defaults
try:
    rcParams.load()
except:
    rcParams.save()
