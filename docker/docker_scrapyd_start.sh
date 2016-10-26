#!/bin/bash

deploy_after_delay() {
  sleep 30
  scrapyd-deploy
}

deploy_after_delay &
scrapyd