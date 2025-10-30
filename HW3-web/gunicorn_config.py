# gunicorn_config.py
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app import create_app, scheduled_update

# 獲取 Gunicorn 的進程 ID，確保排程器只在一個工作進程中啟動
# 這可以防止在有多個 worker 時，排程任務被重複執行
worker_pid = None

def when_ready(server):
    """
    當 Gunicorn 主進程準備好時執行。
    我們在這裡不做任何事，只是為了展示鉤子的存在。
    """
    print("Gunicorn master process is ready.")

def post_fork(server, worker):
    """
    當一個工作進程被分叉出來後執行。
    這是啟動我們背景排程器的最佳位置。
    """
    global worker_pid
    # 確保只在第一個 worker 中啟動 scheduler
    if worker_pid is None:
        worker_pid = worker.pid
        
        # 建立一個 app context 以便排程器可以存取 Flask 的功能
        app = create_app()
        with app.app_context():
            # 在啟動時立即運行一次更新
            print(f"--- [Worker PID: {worker.pid}] Running initial price update... ---")
            scheduled_update()
            print(f"--- [Worker PID: {worker.pid}] Initial price update finished. ---")

            # 設定並啟動排程器
            scheduler = BackgroundScheduler(daemon=True)
            # 在 Render 上，免費方案的 Background Worker 更適合定時任務
            # 但如果要在 Web Service 中運行，可以設定較長的間隔
            scheduler.add_job(scheduled_update, 'interval', hours=1)
            scheduler.start()
            
            print(f"Scheduler started in worker with PID: {worker.pid}")