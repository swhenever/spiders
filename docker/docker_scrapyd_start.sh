#!/bin/bash

deploy_after_delay() {
  sleep 30
  scrapyd-deploy
}

# make sure any existing twistd pid file is deleted
rm /var/spiders/twistd.pid

deploy_after_delay &
scrapyd
