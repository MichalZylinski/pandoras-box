#!/bin/bash
sudo apt-get update
sudo apt-get install python3-pip -y
pip3 install google-cloud
pip3 install google-cloud-spanner
pip3 install flask
python3 -m flask run
