try:
    import ujson as json
except ImportError:
    import json

import os
import sqlite3
import time
from collections import UserDict


class TelegramStorage:
    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        raise NotImplementedError()

    def get_field(self, key: str, field: str, expires: int):
        raise NotImplementedError()

    def update_fields(self, key: str, field_mapping, expires: int) -> bool:
        raise NotImplementedError()

    def delete_fields(self, key: str, expires: int, *field) -> bool:
        raise NotImplementedError()

    def delete_key(self, key: str) -> bool:
        raise NotImplementedError()

    def data(self, key: str):
        raise NotImplementedError()


class MemoryStorage(TelegramStorage):
    __slots__ = ("_data", )

    def __init__(self):
        self._data = {}

    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        if value is None:
            self.delete_fields(key, expires, field)
            return True
        current_time = int(time.time())
        if key not in self._data or self._data[key].get("expires",
                                                        0) < current_time:
            self._data[key] = {
                "expires": current_time + expires,
                "data": {
                    field: value
                },
            }
            return True
        data = self._data[key]
        data["expires"] = current_time + expires
        data["data"][field] = value
        return True

    def get_field(self, key: str, field: str, expires: int):
        current_time = int(time.time())
        if key in self._data:
            if self._data[key].get("expires", 0) < current_time:
                self.delete_key(key)
                return None
            data = self._data[key]
            data["expires"] = current_time + expires
            return data["data"].get(field, None)
        return None

    def update_fields(self,
                      key: str,
                      field_mapping,
                      expires: int = 1800) -> bool:
        current_time = int(time.time())
        if key in self._data and self._data[key].get("expires",
                                                     0) < current_time:
            self.delete_key(key)
        data = self._data.get(key, {})
        if "data" in data:
            data["data"].update(field_mapping)
        else:
            data["data"] = field_mapping
        data["expires"] = int(time.time()) + expires
        self._data[key] = data
        return True

    def delete_fields(self, key: str, expires: int, *fields) -> bool:
        current_time = int(time.time())
        if key in self._data:
            if self._data[key].get("expires", 0) < current_time:
                self.delete_key(key)
                return True
            data = self._data[key]
            data["expires"] = current_time + expires
            for field in fields:
                if field in data["data"]:
                    del data["data"][field]
            self._data[key] = data
            return True
        return False

    def delete_key(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
        return True

    def data(self, key: str):
        if key not in self._data or self._data[key].get("expires", 0) < int(
                time.time()):
            self.delete_key(key)
            return {}
        return self._data[key]["data"]


class SQLiteStorage(TelegramStorage):
    __slots__ = ("_db_conn", )

    def __init__(self, db_file: str = None):
        if db_file is None:
            self._db_conn = sqlite3.connect(
                "file:memory?cache=shared&mode=memory", uri=True)
        else:
            db_path = os.path.dirname(db_file)
            if not os.path.exists(db_path):
                os.mkdir(db_path)
            self._db_conn = sqlite3.connect(db_file)
        self._db_conn.row_factory = sqlite3.Row
        with self._db_conn:
            self._db_conn.execute("""
                CREATE TABLE IF NOT EXISTS `t_storage` (
                    `key`        TEXT NOT NULL UNIQUE,
                    `data`       TEXT NOT NULL,
                    `expires`    INTEGER NOT NULL,
                    PRIMARY KEY(`key`)
                    )
                """)

    def __del__(self):
        self._db_conn.close()

    def set_field(self, key: str, field: str, value: str,
                  expires: int) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_storage WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data and row_data["expires"] >= current_time:
                data = json.loads(row_data["data"])
                data[field] = value
                cur = self._db_conn.execute(
                    "UPDATE t_storage SET data=?, expires=? WHERE key=?",
                    (json.dumps(data), current_time + expires, key),
                )
                return bool(cur.rowcount)

            cur = self._db_conn.execute(
                """
                INSERT OR REPLACE INTO t_storage (
                    key,
                    data,
                    expires
                ) VALUES (?, ?, ?)
                """,
                (key, json.dumps({field: value}), current_time + expires),
            )
            return bool(cur.lastrowid)

    def get_field(self, key: str, field: str, expires: int):
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_storage WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data and row_data["expires"] >= current_time:
                self._db_conn.execute(
                    "UPDATE t_storage SET expires=? WHERE key=?",
                    (current_time + expires, key),
                )
                return json.loads(row_data["data"]).get(field, None)
            return None

    def update_fields(self, key: str, field_mapping, expires: int) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_storage WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data and row_data["expires"] >= current_time:
                data = json.loads(row_data["data"])
                data.update(field_mapping)
                cur = self._db_conn.execute(
                    "UPDATE t_storage SET data=?, expires=? WHERE key=?",
                    (json.dumps(data), current_time + expires, key),
                )
                return bool(cur.rowcount)

            cur = self._db_conn.execute(
                """
                INSERT OR REPLACE INTO t_storage (
                    key,
                    data,
                    expires
                ) VALUES (?, ?, ?)
                """,
                (key, json.dumps(field_mapping), current_time + expires),
            )
            return bool(cur.lastrowid)

    def delete_fields(self, key: str, expires: int, *fields) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_storage WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data and row_data["expires"] >= current_time:
                data = json.loads(row_data["data"])
                for field in fields:
                    if field in data:
                        del data[field]
                cur = self._db_conn.execute(
                    "UPDATE t_storage SET data=?, expires=? WHERE key=?",
                    (json.dumps(data), current_time + expires, key),
                )
                return bool(cur.rowcount)
            return False

    def delete_key(self, key: str):
        with self._db_conn:
            self._db_conn.execute("DELETE from t_storage WHERE key=? ",
                                  (key, ))

    def data(self, key: str):
        cur = self._db_conn.execute(
            "SELECT data, expires from t_storage WHERE key=?", (key, ))
        row_data = cur.fetchone()
        if row_data and row_data.get("expires", 0) >= int(time.time()):
            return json.loads(row_data["data"])
        else:
            self.delete_key(key)
            return {}


class RedisStorage(TelegramStorage):
    __slots__ = ("_redis", )

    def __init__(self, redis_client):
        self._redis = redis_client

    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        self._redis.expire(key, expires)
        return bool(self._redis.hset(key, field, json.dumps(
            (value, )))) if value else bool(self._redis.hdel(key, field))

    def get_field(self, key: str, field: str, expires: int):
        if self._redis.exists(key) != 1:
            return None
        self._redis.expire(key, expires)
        value = self._redis.hget(key, field)
        return json.loads(value)[0] if value else None

    def delete_fields(self, key: str, expires: int, *fields) -> bool:
        if self._redis.exists(key) != 1:
            return True
        self._redis.expire(key, expires)
        return bool(self._redis.hdel(key, *fields))

    def update_fields(self, key: str, field_mapping, expires: int) -> bool:
        data = self._redis.hgetall(key)
        data.update({
            field: json.dumps((value, ))
            for field, value in field_mapping.items()
        })
        self._redis.expire(key, expires)
        return bool(self._redis.hset(key, mapping=data))

    def delete_key(self, key: str) -> bool:
        return bool(self._redis.delete(key))

    def data(self, key: str):
        return {
            field: json.loads(value)[0]
            for field, value in self._redis.hgetall(key).items()
        }

    def __del__(self):
        self._redis.close()


class TelegramSession(UserDict):
    __slots__ = ("_storage", "id", "expires")
    SESSION_ID_FORMAT = "bot:session:{0}:{1}"

    def __init__(self,
                 bot_id: int,
                 user_id: int,
                 storage: TelegramStorage,
                 expires: int = 1800) -> None:
        self._storage = storage
        self.id = self.SESSION_ID_FORMAT.format(bot_id, user_id)
        self.expires = expires
        super().__init__({})

    def __getitem__(self, field: str):
        value = self.data.get(field, None)
        if value is None:
            value = self._storage.get_field(self.id, field, self.expires)
            if value:
                self.data[field] = value
                return value
            raise KeyError("'{0}' is not found".format(field))
        return value

    def get(self, field, default=None):
        try:
            return self[field]
        except KeyError:
            return default

    def delete(self, *fields) -> bool:
        for field in fields:
            if field in self.data:
                super().__delitem__(field)
        return self._storage.delete_fields(self.id, self.expires, *fields)

    def __delitem__(self, field):
        self.delete(field)

    def pop(self, field: str, default=None):
        value = self.get(field, default)
        del self[field]
        return value

    def save(self) -> bool:
        return self._storage.update_fields(self.id,
                                           self.data,
                                           expires=self.expires)

    def clear(self) -> bool:
        self.data = {}
        return self._storage.delete_key(self.id)

    def __repr__(self):
        return "Session(id={0}, expires={1}, data={2})".format(
            self.id, self.expires, self.data)
