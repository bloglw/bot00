from telegram.ext import Updater
from config import TOKEN

from start_route import start_handler
from goods import add_goods_handler, del_goods_handler, share_goods_handler, go_shop_handler, complain_handler
from goods import buy_goods_handler, buy_goods_comfirm_handler
from start_route import service_handler, search_goods_handler, admin_withdraw_handler
from buyer import buyer_handler
from seller import seller_handler
from wallet import wallet_handler
from trade import already_deliver_handler, cancel_trade_handler, comfirm_goods_handler, request_refund_handler
from trade import delay_time_handler, allow_refund_handler, deny_refund_handler
from admin import admin_handler


def run_bot():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(add_goods_handler)
    dispatcher.add_handler(del_goods_handler)
    dispatcher.add_handler(service_handler)
    dispatcher.add_handler(share_goods_handler)
    dispatcher.add_handler(buy_goods_handler)
    dispatcher.add_handler(buy_goods_comfirm_handler)
    dispatcher.add_handler(go_shop_handler)
    dispatcher.add_handler(complain_handler)
    dispatcher.add_handler(already_deliver_handler)
    dispatcher.add_handler(cancel_trade_handler)
    dispatcher.add_handler(comfirm_goods_handler)
    dispatcher.add_handler(request_refund_handler)
    dispatcher.add_handler(delay_time_handler)
    dispatcher.add_handler(allow_refund_handler)
    dispatcher.add_handler(deny_refund_handler)
    dispatcher.add_handler(buyer_handler)
    dispatcher.add_handler(seller_handler)
    dispatcher.add_handler(wallet_handler)
    dispatcher.add_handler(admin_handler)
    dispatcher.add_handler(admin_withdraw_handler)
    dispatcher.add_handler(search_goods_handler)

    updater.start_polling()
    updater.idle()
