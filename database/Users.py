import database.Database


class UsersService:
    def __init__(self):
        self.db = database.Database.db

    def getAll(self):
        self.db.cursor.execute("SELECT * FROM users")
        return self.db.cursor.fetchall()

    def getAllUsersByType(self, user_type_id):
        self.db.cursor.execute("SELECT * FROM users WHERE user_type = %s", (user_type_id,))
        return self.db.cursor.fetchall()

    def getById(self, user_id: int) -> dict | None:
        self.db.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return self.db.cursor.fetchone()

    def getLanguageById(self, user_id):
        self.db.cursor.execute("SELECT lang FROM users WHERE id = %s", (user_id,))
        return self.db.cursor.fetchone()

    def create(self, id: int, username: str, lang: str, typeId: int):
        self.db.cursor.execute("INSERT INTO users (id, username, lang, user_type) VALUES (%s, %s, %s, %s) RETURNING *",
                               (id, username, lang, typeId))
        return self.db.cursor.fetchone()

    def updateUserType(self, user_id, type_id):
        self.db.cursor.execute("UPDATE users SET user_type = %s WHERE id = %s", (type_id, user_id))

    def getAllByUserType(self, user_type):
        self.db.cursor.execute("SELECT * FROM users WHERE user_type = %s", (user_type,))
        return self.db.cursor.fetchall()

    def setLanguage(self, user_id, lang):
        self.db.cursor.execute("UPDATE users SET lang = %s WHERE id = %s", (lang, user_id))
