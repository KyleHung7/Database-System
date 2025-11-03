# auth.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if db.users.find_one({'username': username}):
            flash('Username already exists.', 'warning')
        else:
            new_user_id = db.users.insert_one({
                'username': username,
                'password_hash': generate_password_hash(password, method='pbkdf2:sha256')
            }).inserted_id
            user_data = db.users.find_one({"_id": new_user_id})
            login_user(User(user_data))
            flash('Account created successfully! Welcome to Stockcord.', 'success')
            return redirect(url_for('main.index'))
    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username:
            flash('Username is required.', 'danger')
            return render_template('login.html')
        if not password:
            flash('Password is required.', 'danger')
            return render_template('login.html')

        user_data = db.users.find_one({'username': username})
        if user_data and check_password_hash(user_data['password_hash'], password):
            login_user(User(user_data))
            return redirect(url_for('main.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
