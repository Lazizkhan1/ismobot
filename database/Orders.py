import database.Database


class OrderStatus:
    PENDING = 0
    ACCEPTED = 1
    PAID = 2
    COMPLETED = 3
    CANCELED = -1


class OrdersService:
    def __init__(self):
        self.db = database.Database.db

    def getAll(self):
        self.db.cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        return self.db.cursor.fetchall()

    def getById(self, id):
        self.db.cursor.execute("SELECT * FROM orders WHERE id = %s", (id,))
        return self.db.cursor.fetchone()

    def getByStatus(self, status):
        self.db.cursor.execute('SELECT * FROM orders WHERE "status" = %s ORDER BY id DESC', [status])
        return self.db.cursor.fetchall()

    def getByCategoryId(self, category_id):
        self.db.cursor.execute("SELECT * FROM orders WHERE category_id = %s ORDER BY id DESC", (category_id,))
        return self.db.cursor.fetchall()

    def create(self, user_id, category_id, ceremony_date, video_note_id, cheque_id):
        self.db.cursor.execute(
            "INSERT INTO orders (user_id, category_id, ceremony_date, video_note_id, cheque_id) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (user_id, category_id, ceremony_date, video_note_id, cheque_id)
        )
        return self.db.cursor.fetchone()

    def acceptOrder(self, order_id):
        self.db.cursor.execute("UPDATE orders SET status = %s WHERE id = %s RETURNING *", (OrderStatus.ACCEPTED, order_id))
        return self.db.cursor.fetchone()

    def completeOrder(self, order_id):
        self.db.cursor.execute("UPDATE orders SET status = %s WHERE id = %s RETURNING *", (OrderStatus.COMPLETED, order_id))
        return self.db.cursor.fetchone()

    def cancelOrder(self, order_id, reason):
        self.db.cursor.execute("UPDATE orders SET status = %s, cancel_reason = %s, canceled_at = NOW() WHERE id = %s RETURNING *", (OrderStatus.CANCELED, reason, order_id))
        return self.db.cursor.fetchone()