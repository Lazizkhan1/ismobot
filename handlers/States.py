from aiogram.fsm.state import StatesGroup, State


class OrderState(StatesGroup):
    category = State()
    delivery_type = State()
    ceremony_date = State()
    video_note_id = State()
    cheque_id = State()


class CategoryState(StatesGroup):
    name = State()


class OrderPhotos(StatesGroup):
    order_id = State()
    photos = State()


class CancelOrder(StatesGroup):
    order_id = State()
    reason = State()

