import database.Database


class CategoriesService:
    def __init__(self):
        self.db = database.Database.db

    def getAll(self):
        self.db.cursor.execute("SELECT * FROM categories WHERE deleted_at IS NULL ORDER BY id")
        return self.db.cursor.fetchall()

    def getById(self, id):
        self.db.cursor.execute("SELECT * FROM categories WHERE id = %s AND deleted_at IS NULL", (id,))
        return self.db.cursor.fetchone()

    def create(self, name):
        self.db.cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING *", (name,))
        return self.db.cursor.fetchone()

    def delete(self, id):
        self.db.cursor.execute("UPDATE categories SET deleted_at = NOW() WHERE id = %s RETURNING id", (id,))
        return self.db.cursor.fetchone()