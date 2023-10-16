# Building an API in October 2023

In short, it's not as time consuming, from the first line of code until the first lines in this README, it took me ~24 hours. There are plenty of readings to help you build a secure, robust and documented API. The biggest factors I think are:

* FastAPI - I've always been a fan of micro frameworks that doesn't get in your way and FastAPI is just that. Their documentation is an example to follow. I salute you [Sebastián Ramírez](https://twitter.com/tiangolo).
* Pydantic - Modeling using regular Python helps readability and lessen cognitive load. Oh and it validates your data too. Like with FastAPI, Pydantic's documentation is also an example to follow.
* Kinde - Authentication and authorization is a pain to implement. Kinde makes it easy to implement OAuth2 and OpenID Connect. It's also free for up to 7500 MAU. I'm not affiliated with Kinde in any way, I'm just a fan.

If you're building a SaaS, I highly recommend to check out Kinde, their product is targeted for SaaS builders.

Above said, let's dig deeper into the findings.

### Testing

[Pytest](https://docs.pytest.org/en/7.4.x/) is the de facto standard for testing in Python. It's easy to use and has a lot of plugins to help you test your code. [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) makes writing async tests and fixtures a breeze, you can just use lib codes from your app out of the box.

However, testing authorizations when using a third party like Kinde is tricky. You don't generate your own access token, you get it from Kinde. You can't mock the response from Kinde because you need to use the actual access token to authorize yourself in the API. So far, I ended up mocking the authorization function which means it skips the authorization step and injected a user fixture into it. I'm not sure if this is the best way to do it, this makes it impossible to test for negative cases.

I'm not proud of these line of codes, I want to do better.

```python
class FakeContext:
    def __init__(
        self,
        access_token: str | None = None,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
        current_user: User | None = None,
    ):
        self.access_token = access_token
        self.permissions = permissions
        self.mongo_session = mongo_session
        self.current_user = current_user
        self.auth_provider_user_id = current_user.auth_provider_user_id

    @classmethod
    @asynccontextmanager
    async def protected(
        cls,
        authorization: HTTPAuthorizationCredentials,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
        **kwargs,
    ):
        current_user = kwargs.get("current_user")
        if current_user.is_blocked:
            raise HTTPException(status_code=403)

        yield cls(
            access_token=authorization.credentials,
            permissions=permissions,
            mongo_session=mongo_session,
            current_user=current_user,
        )
    
    @classmethod
    @asynccontextmanager
    async def public(cls, mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None):
        yield cls(mongo_session=mongo_session)

        
@pytest_asyncio.fixture(autouse=True)
async def nullify_auth(monkeypatch, user: User):
    monkeypatch.setattr(
        "dnsdig.libshared.context.Context.protected",
        lambda *args, **kwargs: FakeContext.protected(*args, **kwargs, current_user=user),
    )
    monkeypatch.setattr("dnsdig.libshared.context.Context.public", FakeContext.public)
```

The test coverage hovers around 70-ish% because of the monkeypatching. In my experience, I sleep better at night when coverage is more than 85%.

If anyone from Kinde is reading this, I'd love your thoughts about this, testing would be essential for any API. I did think about issuing my own JWT token but then why would I use Kinde in the first place?

### Documentation

It's a great time to be a software engineer. Consuming and producing documentations have never been simpler and easier. Especially with FastAPI, producing documentation means properly type hinting your codes which do not only help with documentation but also with readability and maintainability.

Not long ago, my work was put under a magnifying glass for due diligence. One of the shortcoming noted in the result was the lack of documentation while also noting that our codes are written to document itself 😳. The codes will document itself when these conditions are met:

* Type hinted
* Strong modeling, no `dict` or `list` as return types or parameters, no hardcode of values
* Be religious with naming, bug the hell out of your team mates if they don't follow the naming convention, including the product and business folks

Coming back to October 2023, documenting API endpoints at the very least is a minimum and FastAPI makes this accessible to everyone. I'm impartial of the OpenAPI spec but it is a standard and it's better than nothing.

### Asynchrony and MongoDB

I used to despise coroutines, especially if the word `Tornado` is associated with it. If just 1 person in your team doesn't understand coroutines, it's a recipe for disaster. I've seen it first hand, it's not pretty. But today, even though `asyncio` has its critics, it's still a better experience than the past.

In my pet projects and my day job, I use MongoDB almost every time unless an SQL mandate is imposed. MongoDB is designed to be hit with concurrent requests, it's a perfect match for FastAPI's async endpoints. This coupled with [Beanie ODM](https://beanie-odm.dev/) makes it a pleasant experience to work with.

I just have 1 bug with ODMs or ORMs, even though it's convenient to generate queries, don't do it. Always write your queries manually but profit from an ODM's or ORM's excellent feature to do writes. For MongoDB, this includes aggregations, write it manually.

In this project I wrote a simple MongoDB query wrapper to work with Beanie ODM and to make it easier to write queries. It's not perfect but it's good enough for my use case. Yes this will potentially use more memory, this is an accepted trade off.

```python
from typing import TypeVar, Any, Dict, List, Type, Tuple

from beanie import Document
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.collation import Collation

T = TypeVar("T", bound=BaseModel)
TD = TypeVar("TD", bound=Document)


async def monq_find_many(
    model: Type[TD],
    query: Dict[str, Any],
    *,
    project_to: Type[T] | None = None,
    skip: int = 0,
    limit: int = 0,
    sort: List[Tuple[str, int]] | None = None,
    collation: Dict[str, Any] | Collation = None,
) -> List[T] | List[Dict] | List:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    if not collation:
        _cursor = coll.find(query, skip=skip, limit=limit, sort=sort)
    else:
        _cursor = coll.find(query, skip=skip, limit=limit, sort=sort).collation(collation)

    results = []
    async for doc in _cursor:
        results.append(doc)

    if not results or len(results) == 0:
        return []

    if not project_to:
        return results

    return [project_to(**result) for result in results]


async def monq_find_one(
    model: Type[TD],
    query: Dict[str, Any],
    *,
    project_to: Type[T] | None = None,
    collation: Dict[str, Any] | Collation = None,
) -> T | Dict | None:
    results = await monq_find_many(model=model, query=query, project_to=project_to, limit=1, collation=collation)
    if len(results) == 0:
        return None
    return results[0]


async def monq_delete_one(model: Type[TD], where: Dict[str, Any]) -> int:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.delete_one(where)

    return result.deleted_count


async def monq_lock_document(model: Type[TD], where: Dict[str, Any], lock_field: str) -> bool:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.find_one_and_update(where, {'$set': {lock_field: True}}, return_document=ReturnDocument.AFTER)

    return result is not None


async def monq_delete_many(model: Type[TD], where: Dict[str, Any]) -> int:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.delete_many(where)

    return result.deleted_count
```

2023 brings a serious elevation towards asynchrony and concurrency. I'm excited to see what's coming, especially if and when [GIL is removed](https://peps.python.org/pep-0703/).

### Batteries (not) Included

Forgive the snarky title, I think if there's a debate if frameworks comes with batteries or not, it will be more towards philosophy than an actual debate. I'm not going to go into that, instead I'm going to talk about my use case and see if for my use case, the batteries are included.

#### Authorization

FastAPI kept its promise, batteries **ARE included**. I wanted to create a custom authorization flow like I discussed above and it's downright simple to execute. Annotating a view function with the right dependency and the API docs is updated. We can authorize from within the API docs to access protected endpoints.

This is possible because FastAPI don't get in your way, it's a micro framework, it will not try to solve everything for you. It's a good thing, it's a great thing. You still need to orchestrate the authorization flow, FastAPI takes the cognitive load (of documenting it) off of you by providing the tools to do it. Standards are the fundamental reason why, in this case [OAuth2](https://oauth.net/2/), [OpenID Connect](https://openid.net/connect/) and [JWT](https://jwt.io).

However, implementing an authorization flow is a double edged sword. It's easy to implement but it's also easy to implement it wrong. In this project, the focus is to be as minimal as possible by leveraging out of the box features.

This is also the first time I wrote a protected API without having to implement user registrations or logins. It decreases the surface area of the `Account` domain by a considerable amount. For this project Kinde helped a lot, you spend more time on your product rather than the formalities.

I enjoy Kinde's approach to authorization. Other auth providers implement user identities as part of [JWT Claims](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-token-claims) while Kinde gives you an `ID Token` where the essentials of a user is defined. This `ID Token` can then be compared to your database, you can register new users without prompting them. This comes with a condition that the fields included in the `ID Token` is sufficient to create a user from, which they are in my use case. Later down the user journey, we can always ask for more details with the right context.

```python
class Account:
    # ...
    @classmethod
    async def maybe_create_user(cls, id_token: str):
        payload = jwt.decode(id_token, options={"verify_signature": False})

        email = payload.get("email")
        auth_provider_user_id = payload.get("sub")
        if not email or not auth_provider_user_id:
            return

        query = {"auth_provider_user_id": auth_provider_user_id}
        user = await monq_find_one(model=User, query=query, project_to=User)
        if user:
            return

        query = {"email": email}
        user = await monq_find_one(model=User, query=query, project_to=User)
        if user and user.auth_provider_user_id != auth_provider_user_id:
            user.auth_provider_user_id.append(auth_provider_user_id)
            await user.save()
            return

        await cls.create_user(
            email=email,
            auth_provider_user_id=auth_provider_user_id,
            permissions=resolver_role.permissions,
            roles=[resolver_role.role],
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name"),
        )
    # ...
```

The above happened when an exchange from `authorization_code` to an `access_token` is successful. The `id_token` is included in the response. No registration or login endpoints, just trust the auth provider, in this case Kinde. To be using an auth provider the first place implies that there is a trust relationship between you and the auth provider. The trust extends into the codes. It's cool that all this happens during a standard OAuth flow, standards are always good.

### Dependencies

The cool term here is `Dependency Injection` and FastAPI nailed it. It was able to do so by leveraging Python's Type Hinting. Consider the following view handler:

```python
@router.get(
    "/resolve/{name}/{record_type}", summary="Resolve a DNS record", tags=["Resolver"], response_model=ResolverResult
)
async def resolve_dns_record(
    name: str,
    record_type: RecordTypes = RecordTypes.A,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    mongo_client: MongoClient = Depends(MongoClientDependency()),
):
    permissions = [Permissions.ReadResolver]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions):
            return await Resolver.resolve_record(hostname=name, record_type=record_type)
```

And its dependency:

```python
class MongoClient:
    def __init__(self):
        self.client = mongo_client

    @property
    def db_name(self) -> str:
        return settings.db_name

    @asynccontextmanager
    async def transaction(self) -> motor_asyncio.AsyncIOMotorClientSession:
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception as exc:
                    await session.abort_transaction()
                    raise exc


class MongoClientDependency:
    def __init__(self):
        self.client = MongoClient()

    async def __call__(self, request: Request) -> MongoClient:
        return self.client
```

For this project's use case this is a necessary dependency to inject rollbacks to the database whenever an exception is raised. I like to raise exceptions from wherever I want, I don't want to be limited by the framework. This is a good example of FastAPI not getting in your way. FastAPI provides the tools you need to govern your own codes, it doesn't try to enforce itself on you.

Reaffirming my first point, this is possible because of Python's Type Hinting and a little bit of metaprogramming. Python is not perfect, on the surface it looks simple but when you go deep, it's a beast of a language.

### Conclusion

I talked mostly about FastAPI because that's the basic building block to build this project. Without having to dig deep into the framework, I was able to build a secure, robust and documented API in 24 hours. What does this say about the batteries?

Yes, batteries are included, but there's still work to do. You still need to execute your ideas, FastAPI facilitates you to do it without imposing itself. It's a great framework, I'm a fan, a huge one.

Pydantic on the other hand I think is a catalyst for change for the better. Strong modeling is a given nowadays, it's a must for readability, maintainability and documentation. Pydantic makes it easy to do so. Other than Python, I sometime dabble with Typescript, it's impossible to achieve the level of trust you have for your models in Typescript as we do with Pydantic. Typescript is compiled to JavaScript and there's no safety at runtime, **BUT** getting scolded by TypeScript's compiler is better than having them errors at runtime.

My last paragraph will spark fanboys and or purists, let the roasting begin. I have tried many times to get myself comfortable with other languages but I keep coming back to Python, the ideology sticks. It even helped me when I do code in other languages. Although I categorically will never learn Golang, topic for another day.

## DNS

I didn't talk about DNS so far because I admit for this project, it's more of an excuse as oppose as the hero. I'm in no way knowledgeable enough to talk about DNS, but I want to understand what it is, not how it works. Ever since the dial up days, I needed to input DNS servers into the dial up configuration, it's a long standing topic for me.

The first version of this project as I said before focuses more on the what. I wanted to know about DNS records and the various types of records. Modeling DNS records sparked my curiosity, I still have notes I need to research about. But that won't stop me from actually doing something (writing codes).

On this project I use [DNSPython](https://www.dnspython.org/) as the DNS client. I haven't spent enough time to have an opinion about it. I'm just happy it exists for this project. That said, there are no knowledge to be had about DNS in this writing for now. Well there's 1 knowledge I learned unrelated to DNS but I stumbled upon because of DNS. Github's Ubuntu runners doesn't support IPv6, that's why IPv6 tests are commented for now.

Making IPv6 work on Github's Ubuntu runners is going to be my pet peeve for the next few days.

This project have 2 endpoints to resolve DNS:

* `GET /v1/resolve/{name}/{record_type}` - This endpoint will resolve a DNS record and return the result in JSON format.
* `GET /v1/resolve6/{name}/{record_type}` - This endpoint will resolve a DNS record using IPv6 resolvers and return the result in JSON format.

Why? Because I can and because DNSPython supports it.

---

My initial motivation to do this project is because of this guy's tweet.

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">I ❤️ DNS<br><br>I’ve spent 2 years full-time building <a href="https://t.co/LYem2r1Vyh">https://t.co/LYem2r1Vyh</a>.<br><br>Now, I’m teaching everything I know in this course.</p>&mdash; Ruurtjan Pul 🛠️ (@Ruurtjan) <a href="https://twitter.com/Ruurtjan/status/1709557984689582559?ref_src=twsrc%5Etfw">October 4, 2023</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

His work in [nslookup.io](https://www.nslookup.io/) sets an example for me. He likes it and then he quits his day job to do it. More about the conviction than anything else. I like people with convictions, at least they tried to follow their convictions if nothing else.

I still can't say if I ❤️ DNS yet, but I love the idea of it. It's the building block of our Internet, how can I not love the idea?
