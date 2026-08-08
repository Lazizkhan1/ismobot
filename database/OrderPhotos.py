import database.Database


class OrderPhotosService:
    def __init__(self):
        self.db = database.Database.db

    def get_order_photos(self, order_id):
        self.db.cursor.execute("SELECT photo_id FROM order_photos WHERE order_id = %s", (order_id,))
        return self.db.cursor.fetchall()

    def add_order_photo(self, order_id, photo_id):
        self.db.cursor.execute("INSERT INTO order_photos (order_id, photo_id) VALUES (%s, %s) RETURNING *", (order_id, photo_id))
        return self.db.cursor.fetchone()

    def delete_order_photo(self, order_id, photo_id):
        self.db.cursor.execute("DELETE FROM order_photos WHERE order_id = %s AND photo_id = %s RETURNING *", (order_id, photo_id))
        return self.db.cursor.fetchone()