import os
import sys


ENDPOINTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'endpoints-proto-datastore')
sys.path.insert(0, ENDPOINTS_DIR)
