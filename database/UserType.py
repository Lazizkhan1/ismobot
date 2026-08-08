from enum import IntEnum


class UserTypeEnum(IntEnum):
    ADMIN = 1
    CUSTOMER = 2


class UserTypeService:
    """Service that maps role names to enum integer values.

    The database-backed user_type table was removed; code should use the
    enum values directly. Unknown types return None.
    """

    def __init__(self):
        self._cache = {}

    def get_user_type_id(self, type_name: str) -> int | None:
        type_name = type_name.upper()
        if type_name in self._cache:
            return self._cache[type_name]

        if type_name == 'ADMIN':
            val = int(UserTypeEnum.ADMIN)
        elif type_name == 'CUSTOMER':
            val = int(UserTypeEnum.CUSTOMER)
        else:
            # Unknown role; no DB lookup anymore since user_type table was removed
            return None

        self._cache[type_name] = val
        return val

    def getCustomerType(self) -> int:
        return int(UserTypeEnum.CUSTOMER)

    def getAdminType(self) -> int:
        return int(UserTypeEnum.ADMIN)
