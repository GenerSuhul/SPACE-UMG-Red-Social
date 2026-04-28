from pydantic import ValidationError

class UserService:

    @staticmethod
    def find_by_id(data: str) -> dict | None:
        print(data)
        return None