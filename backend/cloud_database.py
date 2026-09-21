"""Small DB-API bridge for the official libSQL driver.

Keeps sqlite3.Row-style reads and sqlite3 error types used by the existing API.
Local development remains sqlite3; no embedded replica or temporary cloud DB.
"""
import sqlite3


def _call(method, *args):
    try:
        return method(*args)
    except ValueError as error:
        message = str(error)
        if 'constraint failed' in message.lower() or 'SQLITE_CONSTRAINT' in message:
            raise sqlite3.IntegrityError(message) from error
        raise sqlite3.OperationalError(message) from error


class Row:
    def __init__(self, columns, values):
        self._columns = columns
        self._values = values

    def keys(self):
        return list(self._columns)

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                key = self._columns.index(key)
            except ValueError as error:
                raise IndexError(key) from error
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class Cursor:
    def __init__(self, raw):
        self.raw = raw
        self.description = raw.description
        self._columns = tuple(c[0] for c in self.description or ())
        self.lastrowid = raw.lastrowid
        self.rowcount = raw.rowcount
        self._finished = False

    def fetchone(self):
        if self._finished:
            return None
        value = _call(self.raw.fetchone)
        if value is None:
            self._finished = True
            return None
        return Row(self._columns, value)

    def fetchall(self):
        if self._finished:
            return []
        values = _call(self.raw.fetchall) or []
        self._finished = True
        return [Row(self._columns, row) for row in values]

    def __iter__(self):
        while (row := self.fetchone()) is not None:
            yield row


class Connection:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, parameters=()):
        return Cursor(_call(self.raw.execute, sql, tuple(parameters)))

    def executemany(self, sql, parameters):
        return Cursor(_call(self.raw.executemany, sql, list(parameters)))

    def executescript(self, sql):
        # Match sqlite3's implicit commit before executescript.
        self.commit()
        return _call(self.raw.executescript, sql)

    def commit(self):
        return _call(self.raw.commit)

    def rollback(self):
        return _call(self.raw.rollback)

    def close(self):
        return self.raw.close()


def connect(path, auth_token=''):
    import libsql
    raw = libsql.connect(str(path), auth_token=auth_token, timeout=15)
    return Connection(raw)
