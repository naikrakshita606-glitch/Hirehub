import uuid
from flask import current_app

from app.extensions import mongo


class BaseRepository:
    collection_name = 'items'

    @property
    def collection(self):
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            return mongo.get_db()[self.collection_name]
        current_app.config.setdefault('memory_store', {})
        current_app.config['memory_store'].setdefault(self.collection_name, [])
        return current_app.config['memory_store'][self.collection_name]

    def create(self, payload):
        payload = dict(payload)
        payload.setdefault('id', str(uuid.uuid4()))
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            self.collection.insert_one(payload)
            return payload
        self.collection.append(payload)
        return payload

    def get_all(self):
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            return list(self.collection.find({}))
        return list(self.collection)

    def get_by_id(self, item_id):
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            return self.collection.find_one({'id': str(item_id)}) or self.collection.find_one({'_id': item_id})
        for item in self.collection:
            if str(item.get('id')) == str(item_id):
                return item
        return None

    def update(self, item_id, updates):
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            result = self.collection.update_one({'id': str(item_id)}, {'$set': updates})
            return result.modified_count > 0
        for index, item in enumerate(self.collection):
            if str(item.get('id')) == str(item_id):
                self.collection[index].update(updates)
                return True
        return False

    def delete(self, item_id):
        if current_app.config.get('MONGO_AVAILABLE') and mongo.get_db() is not None:
            result = self.collection.delete_one({'id': str(item_id)})
            return result.deleted_count > 0
        for item in list(self.collection):
            if str(item.get('id')) == str(item_id):
                self.collection.remove(item)
                return True
        return False
