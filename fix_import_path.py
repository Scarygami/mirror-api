"""Fixes import path so this submodule can be imported correctly.

This is because the actual library lives within the project as the
directory endpoints_proto_datastore.
"""

import os
import sys


ENDPOINTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'endpoints-proto-datastore')
sys.path.insert(0, ENDPOINTS_DIR)
