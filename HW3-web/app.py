# app.py
from flask import Flask
import os
from extensions import db, login_manager
from models import load_user
from update_prices import update_stock_prices # 保持引入，因為 gunicorn_config.py 需要它

def create_app():
    """應用程式工廠函式"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "a-default-secret-key")

    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(user_id):
        return load_user(user_id)

    from main import bp as main_bp
    app.register_blueprint(main_bp)
    from auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    print("Flask app created.")
    return app

app = create_app()

# --- 這是一個重要的輔助函式，供 gunicorn_config.py 調用 ---
def scheduled_update():
    """Wrapper function to run the update within the app context."""
    with app.app_context():
        print("--- [Scheduler] Running Scheduled Price Update ---")
        update_stock_prices()
        print("--- [Scheduler] Scheduled Price Update Finished ---")

# 本地開發時，直接運行此檔案
if __name__ == '__main__':
    print("Running in local development mode. Scheduler is NOT started.")
    # use_reloader=True 在開發時非常方便，現在我們可以安全地重新啟用它
    app.run(debug=True, use_reloader=True)