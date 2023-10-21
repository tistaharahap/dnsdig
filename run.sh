#!/bin/bash
set -e
set -o pipefail

if test "x${APP}" = 'x'; then
  export APP=dnsdigapi
fi

unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

if test "x${APP}" = 'xdnsdigapi'; then
  # API Defaults
  if test "x${PORT}" = 'x'; then
    export PORT=8080
  fi
  if test "x${HOST}" = 'x'; then
    export HOST=0.0.0.0
  fi
  if test "x${ENV}" = 'x'; then
    export ENV=dev
  fi

  # Control number of workers for uvicorn
  if test "x${WEB_CONCURRENCY}" = 'x'; then
    echo 'WEB_CONCURRENCY is not set, setting it to number of cores'
    if [ "$machine" == "Mac" ]; then
      export WEB_CONCURRENCY=1
    else
      num_of_cores=$(nproc --all)
      export WEB_CONCURRENCY=$num_of_cores
    fi
  fi
  echo 'WEB_CONCURRENCY is: '"${WEB_CONCURRENCY}"

  if test "x${ENV}" = 'xdev'; then
    uvicorn dnsdig.appdnsdigapi.web:app --host $HOST --port $PORT --workers "$WEB_CONCURRENCY" --log-level info --reload
  else
    uvicorn dnsdig.appdnsdigapi.web:app --host $HOST --port $PORT --workers "$WEB_CONCURRENCY" --log-level info
  fi
elif test "x${APP}" = 'xdnsdigd'; then
  if test "x${PORT}" = 'x'; then
    export PORT=5053
  fi
  if test "x${HOST}" = 'x'; then
    export HOST=127.0.0.1
  fi
  python3 dnsdig/appdnsdigd/dnsdigd.py --host $HOST --port $PORT
fi
