try:
    import ujson as json
except ImportError:
    import json

import time
from collections import UserDict
from typing import Any

from telegrambotclient.utils import pretty_format


class TelegramStorage:
    __slots__ = ("_data", )

    def __init__(self):
        self._data = {}

    def get_field(self, key: str, field: str, expires: int):
        session_data = self._data.get(key, {})
        session_data["_expires"] = int(time.time()) + expires
        return session_data.get(field, None)

    def update_fields(self, key: str, mapping, expires: int) -> bool:
        session_data = self._data.get(key, {})
        session_data["_expires"] = int(time.time()) + expires
        session_data.update(mapping)
        self._data[key] = session_data
        return True

    def delete_fields(self, key: str, *fields, expires: int) -> bool:
        session_data = self._data.get(key, {})
        current_time = int(time.time())
        if session_data.get("_expires", 0) < current_time:
            return self.delete_key(key)
        session_data["_expires"] = current_time + expires
        for field in fields:
            if field in session_data:
                del session_data[field]
        self._data[key] = session_data
        return True

    def delete_key(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def data(self, key: str, expires: int):
        session_data = self._data.get(key, {})
        current_time = int(time.time())
        if session_data.get("_expires", 0) >= current_time:
            session_data["_expires"] = current_time + expires
            self._data[key] = session_data
        return session_data


class SQLiteStorage(TelegramStorage):
    __slots__ = ("_db_conn", )

    def __init__(self, db_conn):
        db_conn.execute("""
            CREATE TABLE IF NOT EXISTS `t_session` (
                `key`        TEXT NOT NULL UNIQUE,
                `data`       TEXT NOT NULL,
                `expires`    INTEGER NOT NULL,
                PRIMARY KEY(`key`)
                )
            """)
        self._db_conn = db_conn

    def get_field(self, key: str, field: str, expires):
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_session WHERE key=?", (key, ))
            row_data = cur.fetchone()
            if row_data:
                current_time = int(time.time())
                if row_data[1] < current_time:
                    return None
                self._db_conn.execute(
                    "UPDATE t_session SET expires=? WHERE key=?",
                    (current_time + expires, key))
                return json.loads(row_data[0]).get(field, None)
            return None

    def update_fields(self, key: str, mapping, expires: int) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_session WHERE key=?", (key, ))
            row_data = cur.fetchone()
            current_time = int(time.time())
            if row_data:
                data = json.loads(row_data[0])
                if row_data[1] >= current_time:
                    data.update(mapping)
                else:
                    data = mapping
                cur = self._db_conn.execute(
                    "UPDATE t_session SET data=?, expires=? WHERE key=?",
                    (json.dumps(data), current_time + expires, key))
                return cur.rowcount > 0

            cur = self._db_conn.execute(
                """
                INSERT OR REPLACE INTO t_session (
                    key,
                    data,
                    expires
                ) VALUES (?, ?, ?)
                """, (key, json.dumps(mapping), current_time + expires))
            return cur.lastrowid >= 0

    def delete_fields(self, key: str, *fields, expires: int) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute(
                "SELECT data, expires from t_session WHERE key=?", (key, ))
            row_data = cur.fetchone()
            if row_data:
                current_time = int(time.time())
                if row_data[1] < current_time:
                    return False
                data = json.loads(row_data[0])
                for field in fields:
                    if field in data:
                        del data[field]
                cur = self._db_conn.execute(
                    "UPDATE t_session SET data=?, expires=? WHERE key=?",
                    (json.dumps(data), current_time + expires, key))
                return cur.rowcount > 0
            return False

    def delete_key(self, key: str) -> bool:
        with self._db_conn:
            cur = self._db_conn.execute("DELETE from t_session WHERE key=? ",
                                        (key, ))
            return cur.rowcount > 0

    def data(self, key: str, expires: int):
        cur = self._db_conn.execute(
            "SELECT data, expires from t_session WHERE key=?", (key, ))
        row_data = cur.fetchone()
        if row_data:
            current_time = int(time.time())
            if row_data[1] < current_time:
                return {}
            self._db_conn.execute("UPDATE t_session SET expires=? WHERE key=?",
                                  (current_time + expires, key))
            return json.loads(row_data[0])
        return {}

    def __del__(self):
        self._db_conn.close()


class RedisStorage(TelegramStorage):
    __slots__ = ("_redis", )

    def __init__(self, redis_client):
        self._redis = redis_client

    def get_field(self, key: str, field: str, expires: int):
        if self._redis.exists(key) != 1:
            return None
        self._redis.expire(key, expires)
        value = self._redis.hget(key, field)
        return json.loads(value)[0] if value else None

    def delete_fields(self, key: str, *fields, expires: int) -> bool:
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

    def data(self, key: str, expires: int):
        if self._redis.exists(key) != 1:
            return {}
        self._redis.expire(key, expires)
        return {
            field: json.loads(value)[0]
            for field, value in self._redis.hgetall(key).items()
        }

    def __del__(self):
        self._redis.close()


class MongoDBStorage(TelegramStorage):
    __slots__ = ("_session")

    def __init__(self, collection):
        self._session = collection

    def get_field(self, key: str, field: str, expires: int):
        result = None
        current_time = int(time.time())
        result = self._session.find_one_and_update(
            {
                "_id": key,
                "_expires": {
                    "$gte": current_time
                }
            }, {"$set": {
                "_expires": current_time + expires
            }},
            projection=(field, ))
        if result is None:
            self._session.delete_one({"_id": key})
        return result[field] if result and field in result else None

    def update_fields(self, key: str, mapping, expires: int) -> bool:
        current_time = int(time.time())
        mapping.update({"_expires": current_time + expires, "_id": key})
        result = self._session.update_one(
            {
                "_id": key,
                "_expires": {
                    "$gte": current_time
                }
            }, {"$set": mapping})
        if result.matched_count == 0:
            result = self._session.replace_one({"_id": key},
                                               mapping,
                                               upsert=True)

        return result.modified_count > 0 or result.upserted_id is not None

    def delete_fields(self, key: str, *fields, expires: int) -> bool:
        current_time = int(time.time())
        query = {"_id": key, "_expires": {"$gte": current_time}}
        update = {"_expires": current_time + expires}
        result = self._session.update_one(query, {
            "$unset": {field: None
                       for field in fields},
            "$set": update
        })
        count = result.modified_count
        if count == 0:
            result = self._session.delete_one({"_id": key})
            count = result.deleted_count
        return count > 0

    def delete_key(self, key: str) -> bool:
        result = self._session.delete_one({"_id": key})
        return result.deleted_count > 0

    def data(self, key: str, expires: int):
        current_time = int(time.time())
        return self._session.find_one_and_update(
            {
                "_id": key,
                "_expires": {
                    "$gte": current_time
                }
            }, {"$set": {
                "_expires": current_time + expires
            }}) or {}


class TelegramSession(UserDict):
    __slots__ = ("_storage", "id", "expires")

    def __init__(self,
                 session_id: str,
                 storage: TelegramStorage,
                 expires: int = 1800) -> None:
        super().__init__({})
        self._storage = storage
        self.id = session_id
        self.expires = expires if expires > 0 else 1800

    def __getitem__(self, field: str) -> Any:
        value = self.data.get(field, None)
        if value is None:
            value = self._storage.get_field(self.id, field, self.expires)
            self.data[field] = value
        return value

    def get(self, field: str, default=None) -> Any:
        return self[field] or default

    def delete(self, *fields) -> bool:
        for field in fields:
            if field in self.data:
                super().__delitem__(field)
        return self._storage.delete_fields(self.id,
                                           *fields,
                                           expires=self.expires)

    def __delitem__(self, field):
        self.delete(field)

    def __contains__(self, field: str) -> bool:
        return super().__contains__(field) or bool(self[field])

    def __repr__(self):
        return pretty_format(self._data)

    def pop(self, field: str, default=None) -> Any:
        value = self[field] or default
        del self[field]
        return value

    def save(self) -> bool:
        return self._storage.update_fields(self.id,
                                           self.data,
                                           expires=self.expires)

    def clear(self) -> bool:
        self.data = {}
        return self._storage.delete_key(self.id)

    @property
    def _data(self):
        return self._storage.data(self.id, self.expires)
