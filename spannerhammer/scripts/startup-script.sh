#!/bin/bash
export CONFIG_INSTANCE=sh-config
cd /tmp/
#waiting until all spanner instances are ready
sleep 30
python connect.py

