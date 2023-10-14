#!/bin/bash
set -e
set -o pipefail

if test "x${PORT}" = 'x'; then
  export PORT=8080
fi
if test "x${HOST}" = 'x'; then
  export HOST=0.0.0.0
fi
if test "x${ENV}" = 'x'; then
  export ENV=dev
fi

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

# Control number of workers for uvicorn
if test "x${WEB_CONCURRENCY}" = 'x'; then
  echo 'WEB_CONCURRENCY is not set, setting it to number of cores'
  if [ "$machine" == "Mac" ]; then
    export WEB_CONCURRENCY=1
  else
    export WEB_CONCURRENCY=`nproc --all`
  fi
fi
echo 'WEB_CONCURRENCY is: '${WEB_CONCURRENCY}

if test "x${ENV}" = 'xdev'; then
  uvicorn dnsdig.appdnsdigapi.web:app --host $HOST --port $PORT --workers "$WEB_CONCURRENCY" --log-level info --reload
else
  uvicorn dnsdig.appdnsdigapi.web:app --host $HOST --port $PORT --workers "$WEB_CONCURRENCY" --log-level info
fi
