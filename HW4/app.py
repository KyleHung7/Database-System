# app.py
from flask import Flask
import os
from extensions import db, login_manager
from models import load_user
from apscheduler.schedulers.background import BackgroundScheduler
from update_prices import update_stock_prices

def create_app():
    """Application Factory"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "a-default-secret-key")

    # Initialize extensions
    login_manager.init_app(app)

    @login_manager.user_loader
    def user_loader(user_id):
        return load_user(user_id)

    # Register blueprints
    from main import bp as main_bp
    app.register_blueprint(main_bp)
    from auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    print("Flask app created.")
    return app

app = create_app()

def scheduled_update():
    """Wrapper function to run the update within the app context."""
    with app.app_context():
        print("--- [Scheduler] Running Scheduled Price Update ---")
        update_stock_prices()
        print("--- [Scheduler] Scheduled Price Update Finished ---")

if __name__ == '__main__':
    # Run the update once on startup to ensure data is fresh
    print("--- [Startup] Running initial price update... ---")
    with app.app_context():
        update_stock_prices()
    print("--- [Startup] Initial price update finished. ---")

    # Then schedule it to run periodically
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(scheduled_update, 'interval', hours=1)
    scheduler.start()
    
    print("Scheduler started. Prices will be updated every hour.")
    
    # use_reloader=False is important to prevent the scheduler from running twice in debug mode
    app.run(debug=True, use_reloader=False)