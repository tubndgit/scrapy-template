#!/usr/bin/env bash
sudo apt-get --yes update
sudo apt-get --yes install python2.7 python-pip
sudo apt-get install python-mysqldb
sudo pip install -r requirements.txt
export PATH="${PATH}:${HOME}/.local/bin"