#!/bin/bash

virtualenv --python=/usr/bin/python3 ~/lfucg-deploy
source ~/lfucg-deploy/bin/activate
pip install boto3
rvm use 2.2.2
gem install berkshelf -v 5.6.3 --no-ri --no-rdoc

./deploy.py "$@"