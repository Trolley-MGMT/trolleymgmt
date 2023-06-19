#!/bin/sh
/bin/sh ./aws_discovery.sh
/bin/sh ./gcp_discovery.sh
/bin/sh ./aws_cache.sh
/bin/sh ./gcp_cache.sh
python3 deployment.py
python3 web/main.py