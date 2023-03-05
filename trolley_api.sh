#!/bin/sh
/bin/sh ./aws_discovery.sh
/bin/sh ./eks_cache.sh
/bin/sh ./gke_cache.sh
python3 main.py