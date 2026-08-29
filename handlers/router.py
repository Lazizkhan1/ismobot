from aiogram import Router

from handlers import admin_menu, admin_orders, common, orders, rating, referral
from middleware.LoggingMiddleware import LoggingMiddleware
from middleware.Middleware import Middleware


router = Router()
router.message.middleware.register(Middleware())
router.callback_query.middleware.register(Middleware())
router.message.middleware.register(LoggingMiddleware())
router.callback_query.middleware.register(LoggingMiddleware())

router.include_router(common.router)
router.include_router(orders.router)
router.include_router(referral.router)
router.include_router(admin_menu.router)
router.include_router(admin_orders.router)
router.include_router(rating.router)

