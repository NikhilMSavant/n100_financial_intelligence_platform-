import sys
sys.path.insert(0, "src/dashboard/utils")
sys.path.insert(0, "src/analytics")
from db import get_peers

peers = get_peers.__wrapped__("IT Services")
print(peers)