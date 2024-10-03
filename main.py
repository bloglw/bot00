from bot_starter import run_bot
import threading
from func import delete_invoice, trade_monitor, del_complete_trade

# 删除汇率更新线程，因为不再需要 BTC 汇率更新
# thread = threading.Thread(target=update_exchange_rate)

# 保持以下线程逻辑不变
thread2 = threading.Thread(target=trade_monitor)
thread3 = threading.Thread(target=delete_invoice)
thread4 = threading.Thread(target=del_complete_trade)
# thread.start()  # 删除启动汇率更新线程
thread2.start()
thread3.start()
thread4.start()

run_bot()
