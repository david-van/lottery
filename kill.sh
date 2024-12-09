#!/bin/bash

ps aux | grep gunicorn | awk 'NR==1 {print $2}' | xargs kill
