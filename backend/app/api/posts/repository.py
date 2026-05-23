from backend.app.extensions import mongo
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import ReturnDocument, DESCENDING


class PostRepository:

    @staticmethod
    def insert_post(post_doc: dict) -> str | None:
        try:
            result = mongo.db.posts.insert_one(post_doc)
            return str(result.inserted_id)
        except Exception as ex:
            print(f"Error inserting post: {ex}")
            return None

    @staticmethod
    def find_by_id(post_id: str) -> dict | None:
        try:
            return mongo.db.posts.find_one({"_id": ObjectId(post_id)})
        except Exception as ex:
            print(f"Error finding post by id: {ex}")
            return None

    @staticmethod
    def list_posts(skip: int = 0, limit: int = 20, query_filter: dict | None = None) -> list[dict]:
        try:
            q = query_filter if query_filter is not None else {}
            cursor = (
                mongo.db.posts
                .find(q)
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            return list(cursor)
        except Exception as ex:
            print(f"Error listing posts: {ex}")
            return []

    @staticmethod
    def count_posts(query_filter: dict | None = None) -> int:
        try:
            q = query_filter if query_filter is not None else {}
            return mongo.db.posts.count_documents(q)
        except Exception as ex:
            print(f"Error counting posts: {ex}")
            return 0

    @staticmethod
    def list_by_author(author_id: str, skip: int = 0, limit: int = 20) -> list[dict]:
        try:
            cursor = (
                mongo.db.posts
                .find({"author_id": ObjectId(author_id)})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            return list(cursor)
        except Exception as ex:
            print(f"Error listing posts by author: {ex}")
            return []

    @staticmethod
    def count_by_author(author_id: str) -> int:
        try:
            return mongo.db.posts.count_documents({"author_id": ObjectId(author_id)})
        except Exception as ex:
            print(f"Error counting posts by author: {ex}")
            return 0

    @staticmethod
    def update_by_id(post_id: str, update_fields: dict) -> dict | None:
        try:
            return mongo.db.posts.find_one_and_update(
                {"_id": ObjectId(post_id)},
                {"$set": update_fields},
                return_document=ReturnDocument.AFTER,
            )
        except Exception as ex:
            print(f"Error updating post: {ex}")
            return None

    @staticmethod
    def delete_by_id(post_id: str) -> bool:
        try:
            result = mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
            return result.deleted_count > 0
        except Exception as ex:
            print(f"Error deleting post: {ex}")
            return False

    @staticmethod
    def increment_reaction(post_id: str, reaction_type: str, delta: int) -> dict | None:
        try:
            return mongo.db.posts.find_one_and_update(
                {"_id": ObjectId(post_id)},
                {"$inc": {f"reactions_count.{reaction_type}": delta}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception as ex:
            print(f"Error incrementing post reaction: {ex}")
            return None

    @staticmethod
    def increment_comments(post_id: str, delta: int) -> dict | None:
        try:
            return mongo.db.posts.find_one_and_update(
                {"_id": ObjectId(post_id)},
                {"$inc": {"comments_count": delta}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception as ex:
            print(f"Error incrementing comments_count: {ex}")
            return None


class CommentRepository:

    @staticmethod
    def insert_comment(comment_doc: dict) -> str | None:
        try:
            result = mongo.db.comments.insert_one(comment_doc)
            return str(result.inserted_id)
        except Exception as ex:
            print(f"Error inserting comment: {ex}")
            return None

    @staticmethod
    def find_by_id(comment_id: str) -> dict | None:
        try:
            return mongo.db.comments.find_one({"_id": ObjectId(comment_id)})
        except Exception as ex:
            print(f"Error finding comment: {ex}")
            return None

    @staticmethod
    def list_by_post(post_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
        try:
            cursor = (
                mongo.db.comments
                .find({"post_id": ObjectId(post_id), "parent_comment_id": None})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            return list(cursor)
        except Exception as ex:
            print(f"Error listing comments: {ex}")
            return []

    @staticmethod
    def list_replies(parent_comment_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
        try:
            cursor = (
                mongo.db.comments
                .find({"parent_comment_id": ObjectId(parent_comment_id)})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            return list(cursor)
        except Exception as ex:
            print(f"Error listing replies: {ex}")
            return []

    @staticmethod
    def delete_replies_by_parent(parent_comment_id: str) -> int:
        try:
            result = mongo.db.comments.delete_many(
                {"parent_comment_id": ObjectId(parent_comment_id)}
            )
            return result.deleted_count
        except Exception as ex:
            print(f"Error deleting replies: {ex}")
            return 0

    @staticmethod
    def delete_by_id(comment_id: str) -> bool:
        try:
            result = mongo.db.comments.delete_one({"_id": ObjectId(comment_id)})
            return result.deleted_count > 0
        except Exception as ex:
            print(f"Error deleting comment: {ex}")
            return False

    @staticmethod
    def delete_by_post(post_id: str) -> int:
        try:
            result = mongo.db.comments.delete_many({"post_id": ObjectId(post_id)})
            return result.deleted_count
        except Exception as ex:
            print(f"Error deleting comments by post: {ex}")
            return 0

    @staticmethod
    def increment_reaction(comment_id: str, reaction_type: str, delta: int) -> dict | None:
        try:
            return mongo.db.comments.find_one_and_update(
                {"_id": ObjectId(comment_id)},
                {"$inc": {f"reactions_count.{reaction_type}": delta}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception as ex:
            print(f"Error incrementing comment reaction: {ex}")
            return None


class ReactionRepository:

    @staticmethod
    def find_user_reaction(user_id: str, target_id: str, target_type: str) -> dict | None:
        try:
            return mongo.db.reactions.find_one({
                "user_id":     ObjectId(user_id),
                "target_id":   ObjectId(target_id),
                "target_type": target_type,
            })
        except Exception as ex:
            print(f"Error finding user reaction: {ex}")
            return None

    @staticmethod
    def insert_reaction(reaction_doc: dict) -> str | None:
        try:
            reaction_doc["created_at"] = datetime.now(timezone.utc)
            result = mongo.db.reactions.insert_one(reaction_doc)
            return str(result.inserted_id)
        except Exception as ex:
            print(f"Error inserting reaction: {ex}")
            return None

    @staticmethod
    def update_reaction_type(reaction_id, reaction_type: str) -> dict | None:
        try:
            return mongo.db.reactions.find_one_and_update(
                {"_id": reaction_id},
                {"$set": {
                    "reaction_type": reaction_type,
                    "updated_at":    datetime.now(timezone.utc),
                }},
                return_document=ReturnDocument.AFTER,
            )
        except Exception as ex:
            print(f"Error updating reaction: {ex}")
            return None

    @staticmethod
    def delete_reaction(reaction_id) -> bool:
        try:
            result = mongo.db.reactions.delete_one({"_id": reaction_id})
            return result.deleted_count > 0
        except Exception as ex:
            print(f"Error deleting reaction: {ex}")
            return False

    @staticmethod
    def delete_by_target(target_id: str, target_type: str) -> int:
        try:
            result = mongo.db.reactions.delete_many({
                "target_id":   ObjectId(target_id),
                "target_type": target_type,
            })
            return result.deleted_count
        except Exception as ex:
            print(f"Error deleting reactions by target: {ex}")
            return 0
