# DNS Dig API

A project to learn about DNS in Python while investigating what it's like to build an API in 2023 with [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://pydantic-docs.helpmanual.io/) and [DNSPython](https://www.dnspython.org/). Authentication and authorization is handled by [Kinde](https://kinde.com).

## Getting Started

Python 3.11 is required to run this project. If you don't have it installed, you can use [pyenv](https://github.com/pyenv/pyenv).

Dependencies are managed by [Poetry](https://python-poetry.org/). Install Poetry and then install the dependencies.

```bash
$ curl -sSL https://install.python-poetry.org | python3.11 -
```

Now let's get the API up and running.

```bash
$ git clone git@github.com:tistaharahap/dnsdig.git
$ cd dnsdig
$ poetry install
```

Go to [Kinde](https://kinde.com) and create an account. Then create a new project and add a new API. You'll need the Client ID, Client Secret and Kinde's host for your project to run. Included with this repo is an example `.env` file.

In Kinde, add `http://localhost:8080/v1/callbacks/kinde` as a callback URL for your API.

Edit the `.env.example` file to include your Kinde credentials and rename it to `.env`.

```bash
$ vim .env.example
$ cp .env.example .env
```

The API will not run if any of the required environment variables are missing, make sure you have them all.

When everything is set, run the API.

```bash
$ chmod +x run.sh
$ ./run.sh
```

The API will be available at `http://localhost:8080` and the docs will be available at `http://localhost:8080/docs`.

Before you can make requests to the API, you'll need to create a user. Assuming that the API is running, use the API docs and go to the link below:

[http://localhost:8080/docs#/Me/get_login_url_v1_me_login_url_post](http://localhost:8080/docs#/Me/get_login_url_v1_me_login_url_post)

Click the `Try it out` button, use an empty body in `Request Body` by entering `{}` and then click the `Execute` button.

Note: If you're building a web frontend on top of this API, you can choose to use your own `state` parameter and the API provides a `store` parameter that you can use to store any data you want to be returned to your app after the user has logged in. 

In the response, you will find a `loginUrl` key, copy and paste the value to your browser. You will be redirected to Kinde's login page. After you've logged in, you will be redirected back to the API and your access token will be given in the response.

You can then use the access token to authorize yourself in the API docs. Click the `Authorize` button on the top right corner of the API docs and enter `<access_token>` in the `Value` field and click the `Authorize` button.

### Running With Docker

You can also run the API with Docker. Make sure you have Docker installed and then run the commands below.

```bash
$ docker build -t docker_username/docker_repo: latest .
$ docker run -d --name dnsdig -p 8080:8080 \
  -e WEB_CONCURRENCY=$WEB_CONCURRENCY \
  -e ENV=$ENV \
  -e MONGO_URL=$MONGO_URL \
  -e AUTH_JWKS_URL=$AUTH_JWKS_URL \
  -e AUTH_JWT_ALGO=$AUTH_JWT_ALGO \
  -e AUTH_PROVIDER_HOST=$AUTH_PROVIDER_HOST \
  -e AUTH_PROVIDER_CLIENT_ID=$AUTH_PROVIDER_CLIENT_ID \
  -e AUTH_PROVIDER_CLIENT_SECRET=$AUTH_PROVIDER_CLIENT_SECRET \
  -e AUTH_PROVIDER_REDIRECT_URI=$AUTH_PROVIDER_REDIRECT_URI \
  docker_username/docker_repo:latest
````

Or if you want to get a prebuilt image, you can do the below.

```bash
$ docker run -d --name dnsdig -p 8080:8080 \
  -e WEB_CONCURRENCY=$WEB_CONCURRENCY \
  -e ENV=$ENV \
  -e MONGO_URL=$MONGO_URL \
  -e AUTH_JWKS_URL=$AUTH_JWKS_URL \
  -e AUTH_JWT_ALGO=$AUTH_JWT_ALGO \
  -e AUTH_PROVIDER_HOST=$AUTH_PROVIDER_HOST \
  -e AUTH_PROVIDER_CLIENT_ID=$AUTH_PROVIDER_CLIENT_ID \
  -e AUTH_PROVIDER_CLIENT_SECRET=$AUTH_PROVIDER_CLIENT_SECRET \
  -e AUTH_PROVIDER_REDIRECT_URI=$AUTH_PROVIDER_REDIRECT_URI \
  tistaharahap/dnsdig:latest
```

### Environment Variables

| Name                          | Description                             |
|:------------------------------|:----------------------------------------|
| `WEB_CONCURRENCY`             | Optional string, defaults to 1 on macOS |
| `ENV`                         | Required string                         |
| `MONGO_URL`                   | Required string                         |
| `AUTH_JWKS_URL`               | Required string                         |
| `AUTH_JWT_ALGO`               | Required string                         |
| `AUTH_PROVIDER_HOST`          | Required string                         |
| `AUTH_PROVIDER_CLIENT_ID`     | Required string                         |
| `AUTH_PROVIDER_CLIENT_SECRET` | Required string                         |
| `AUTH_PROVIDER_REDIRECT_URI`  | Required string                         |
| `REDIS_URL`                   | Required string                         |
| `THROTTLER_TIMES`             | Required string                         |
| `THROTTLER_SECONDS`           | Required string                         |

### Bonus

Resolved IP addresses can be geolocated by using the IP database [here](https://github.com/sapics/ip-location-db).

The specific database is below:

[https://github.com/sapics/ip-location-db/raw/master/dbip-city/dbip-city-ipv4.csv.gz](https://github.com/sapics/ip-location-db/raw/master/dbip-city/dbip-city-ipv4.csv.gz)

### Importing IP Database

Download the IP database, extract it and run the commands below.

```
$ python dnsdig/appclis/dbip-importer.py \
  --mongodb-url=<your_mongo_url> \
  --db-name=dnsdig-<your_env> \
  --dbip-city-csv=<path_to_dbip_city_csv>
```

## Why Build This?

More about it in [this blog post](https://bango29.com/building-an-api-in-2023/).
