try:
    import ujson as json
except ImportError:
    import json

import os
import sqlite3
import time
from typing import Any, Dict, Mapping, Optional

from telegrambotclient.utils import pretty_format


class TelegramStorage:
    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        raise NotImplementedError()

    def get_field(self, key: str, field: str, expires: int) -> Any:
        raise NotImplementedError()

    def update_fields(self, key: str, field_mapping: Mapping,
                      expires: int) -> bool:
        raise NotImplementedError()

    def delete_field(self, key: str, field: str, expires: int) -> bool:
        raise NotImplementedError()

    def delete_key(self, key: str) -> bool:
        raise NotImplementedError()

    def dict(self, key: str) -> Dict:
        raise NotImplementedError()


class MemoryStorage(TelegramStorage):
    __slots__ = ("_data", )

    def __init__(self):
        self._data = {}

    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        if value is None:
            self.delete_field(key, field, expires)
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

    def get_field(self, key: str, field: str, expires: int) -> Any:
        current_time = int(time.time())
        if key not in self._data or self._data[key].get("expires",
                                                        0) < current_time:
            self.delete_key(key)
            return None
        data = self._data[key]
        data["expires"] = current_time + expires
        return data["data"].get(field, None)

    def update_fields(self,
                      key: str,
                      field_mapping: Mapping,
                      expires: int = 1800) -> bool:
        current_time = int(time.time())
        if self._data[key].get("expires", 0) < current_time:
            self.delete_key(key)
        data = self._data.get(key, {})
        if "data" in data:
            data["data"].update(field_mapping)
        else:
            data["data"] = field_mapping
        data["expires"] = int(time.time()) + expires
        self._data[key] = data
        return True

    def delete_field(self, key: str, field: str, expires: int) -> bool:
        current_time = int(time.time())
        if key not in self._data or self._data[key].get("expires",
                                                        0) < current_time:
            self.delete_key(key)
            return False
        data = self._data[key]
        data["expires"] = current_time + expires
        if field in data["data"]:
            del data["data"][field]
            self._data[key] = data
        return True

    def delete_key(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
        return True

    def dict(self, key: str) -> Dict:
        if key not in self._data or self._data[key].get("expires", 0) < int(
                time.time()):
            self.delete_key(key)
            return {}
        return self._data[key]["data"]


class SQLiteStorage(TelegramStorage):
    __slots__ = ("_db_conn", )

    def __init__(self, db_file: Optional[str] = None):
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

    def get_field(self, key: str, field: str, expires: int) -> Any:
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

    def update_fields(self, key: str, field_mapping: Mapping,
                      expires: int) -> bool:
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

    def delete_field(self, key: str, field: str, expires: int) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_storage WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data and row_data["expires"] >= current_time:
                data = json.loads(row_data["data"])
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

    def dict(self, key: str) -> Dict:
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

    def __init__(self, redis):
        self._redis = redis

    def set_field(self, key: str, field: str, value, expires: int) -> bool:
        self._redis.expire(key, expires)
        return bool(self._redis.hset(key, field, json.dumps(
            (value, )))) if value else bool(self._redis.hdel(key, field))

    def get_field(self, key: str, field: str, expires: int) -> Any:
        if self._redis.exists(key) != 1:
            return None
        self._redis.expire(key, expires)
        value = self._redis.hget(key, field)
        return json.loads(value)[0] if value else None

    def delete_field(self, key: str, field: str, expires: int) -> bool:
        if self._redis.exists(key) != 1:
            return True
        self._redis.expire(key, expires)
        return bool(self._redis.hdel(key, field))

    def update_fields(self, key: str, field_mapping: Mapping,
                      expires: int) -> bool:
        data = self._redis.hgetall(key)
        data.update({
            field: json.dumps((value, ))
            for field, value in field_mapping.items()
        })
        self._redis.expire(key, expires)
        return bool(self._redis.hset(key, mapping=data))

    def delete_key(self, key: str) -> bool:
        return bool(self._redis.delete(key))

    def dict(self, key: str) -> Dict:
        return {
            field: json.loads(value)[0]
            for field, value in self._redis.hgetall(key).items()
        }

    def __del__(self):
        self._redis.close()


class TelegramSession:
    __slots__ = ("_user_id", "_storage", "_session_id", "_expires",
                 "_local_data")
    _session_key_format = "bot:session:{0}:{1}"

    def __init__(self,
                 bot_id: int,
                 user_id: int,
                 storage: TelegramStorage,
                 expires: int = 1800) -> None:
        self._user_id = user_id
        self._storage = storage
        self._session_id = self._session_key_format.format(bot_id, user_id)
        self._expires = expires
        self._local_data = {}

    @property
    def id(self):
        return self._session_id

    def get(self, field: str, default=None) -> Any:
        try:
            return self.__getitem__(field)
        except KeyError:
            return default

    def __getitem__(self, field: str) -> Any:
        if field in self._local_data:
            return self._local_data[field]
        value = self._storage.get_field(self._session_id, field, self._expires)
        if value:
            self._local_data[field] = value
            return value
        raise KeyError("'{0}' is not found".format(field))

    def set(self, field: str, value) -> bool:
        self._local_data[field] = value

    def __setitem__(self, field: str, value):
        self.set(field, value)

    def delete(self, field: str) -> bool:
        if field in self._local_data:
            del self._local_data[field]
        return self._storage.delete_field(self._session_id, field,
                                          self._expires)

    def __delitem__(self, field: str):
        self.delete(field)

    def pop(self, field: str, default=None):
        value = self.get(field, default)
        del self[field]
        return value

    def __contains__(self, field: str):
        return self.get(field) is not None

    def save(self) -> bool:
        return self._storage.update_fields(self._session_id,
                                           self._local_data,
                                           expires=self._expires)

    def clear(self) -> bool:
        self._local_data = {}
        return self._storage.delete_key(self._session_id)

    @property
    def data(self) -> Dict:
        data = self._storage.dict(self._session_id)
        data.update(self._local_data)
        return data

    def __str__(self):
        return "Session(id={0}, data={1})".format(self._session_id,
                                                  pretty_format(self.data))
