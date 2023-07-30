from __future__ import annotations

from typing import Any

import sqlalchemy as sql


def get_operation(op: str | Any):
    if isinstance(op, str):
        return get_operation_by_string(op)
    # assume it may be the operation itself, i.e. the sql.or_
    # and likewise
    return op


def get_operation_by_string(op_str: str):
    """Convenience helper function to get an SQL operator
    from a string, e.g. "and", "or", "not".
    """
    op_str = op_str.lower()
    operations = {"and": sql.and_, "or": sql.or_, "not": sql.not_}
    try:
        return operations[op_str]
    except KeyError:
        avail = ", ".join(operations)
        raise ValueError(
            f"Cannot convert {op_str} into operation. Available operations: {avail}"
        ) from None


def query_substrings(column, *substrings: str, exclude: bool = False):
    """Helper function to query a substring."""

    def _query_maker(substring):
        my_query = column.contains(substring)
        if exclude:
            my_query = sql.not_(my_query)
        return my_query

    queries = [_query_maker(substring) for substring in substrings]
    return queries
