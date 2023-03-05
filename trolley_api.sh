#!/bin/sh
/bin/sh ./aws_discovery.sh
/bin/sh ./eks_cache.sh
/bin/sh ./gke_cache.sh
ENTRYPOINT ["tail", "-f", "/dev/null"]
#python3 main.py