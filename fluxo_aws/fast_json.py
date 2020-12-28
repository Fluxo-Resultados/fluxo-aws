from orjson import loads, dumps as orjson_dumps  # noqa F401


def dumps(*args, **kwargs):
    return orjson_dumps(*args, **kwargs).decode()
