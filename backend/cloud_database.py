"""Small DB-API bridge for the official libSQL driver.

Keeps sqlite3.Row-style reads and sqlite3 error types used by the existing API.
Local development remains sqlite3; no embedded replica or temporary cloud DB.
"""
from collections.abc import Mapping
import sqlite3
from typing import Any, Iterator, Sequence


def _call(method: Any, *args: Any) -> Any:
    try:
        return method(*args)
    except ValueError as error:
        message = str(error)
        if 'constraint failed' in message.lower() or 'SQLITE_CONSTRAINT' in message:
            raise sqlite3.IntegrityError(message) from error
        raise sqlite3.OperationalError(message) from error


class Row(Mapping[str, Any]):
    def __init__(self, columns: Sequence[str], values: Sequence[Any]):
        self._columns = tuple(columns)
        self._values = tuple(values)
        self._map: dict[str, Any] = dict(zip(self._columns, self._values))

    def keys(self) -> Any:
        return list(self._columns)

    def values(self) -> Any:
        return list(self._values)

    def items(self) -> Any:
        return list(zip(self._columns, self._values))

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, str):
            try:
                return self._map[key]
            except KeyError:
                raise IndexError(key) from None
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._columns)

    def __len__(self) -> int:
        return len(self._values)


class Cursor:
    def __init__(self, raw: Any):
        self.raw = raw
        self.description = raw.description
        self._columns = tuple(c[0] for c in self.description or ())
        self.lastrowid = raw.lastrowid
        self.rowcount = raw.rowcount
        self._finished = False

    def fetchone(self) -> Row | None:
        if self._finished:
            return None
        value = _call(self.raw.fetchone)
        if value is None:
            self._finished = True
            return None
        return Row(self._columns, value)

    def fetchall(self) -> list[Row]:
        if self._finished:
            return []
        values = _call(self.raw.fetchall) or []
        self._finished = True
        return [Row(self._columns, row) for row in values]

    def __iter__(self) -> Iterator[Row]:
        while (row := self.fetchone()) is not None:
            yield row


class Connection:
    def __init__(self, raw: Any):
        self.raw = raw

    def execute(self, sql: str, parameters: Sequence[Any] = ()) -> Cursor:
        return Cursor(_call(self.raw.execute, sql, tuple(parameters)))

    def executemany(self, sql: str, parameters: Sequence[Any]) -> Cursor:
        return Cursor(_call(self.raw.executemany, sql, list(parameters)))

    def executescript(self, sql: str) -> Any:
        # Match sqlite3's implicit commit before executescript.
        self.commit()
        return _call(self.raw.executescript, sql)

    def commit(self) -> Any:
        return _call(self.raw.commit)

    def rollback(self) -> Any:
        return _call(self.raw.rollback)

    def close(self) -> Any:
        return self.raw.close()


def connect(path: Any, auth_token: str = '') -> Connection:
    try:
        import libsql  # type: ignore[import-untyped,import-not-found]
        raw = libsql.connect(str(path), auth_token=auth_token, timeout=15)
        return Connection(raw)
    except ImportError as error:
        raise sqlite3.OperationalError("libsql driver is not installed") from error
