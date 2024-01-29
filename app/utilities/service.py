from typing import TypedDict

from flask import request


class Params(TypedDict):
    q: str | None
    page: int | None
    parent: str | None  # show children of this service or tree of services


def arg_params() -> Params:
    q: str = request.args.get("q", type=str, default="")
    page: int = request.args.get("page", type=int, default=1)
    parent: str = request.args.get("parent", type=str, default="")

    arg_params: Params = {
        "page": page,
        "q": q if q else None,
        "parent": parent if parent else None,
    }
    return arg_params
