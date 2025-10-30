# main.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, session
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import io
import csv
from extensions import db
from pymongo import DESCENDING
from update_prices import update_stock_prices

bp = Blueprint('main', __name__)

def recalculate_holding(user_id, symbol):
    """Recalculates a single holding's state based on all its transactions."""
    pipeline = [
        {'$match': {'user_id': user_id, 'symbol': symbol}},
        {'$group': {'_id': '$symbol', 'total_quantity': {'$sum': '$quantity'}, 'total_cost': {'$sum': {'$multiply': ['$quantity', '$price']}}}}
    ]
    result = list(db.transactions.aggregate(pipeline))
    db.holdings.delete_one({'user_id': user_id, 'symbol': symbol})
    if result and result[0]['total_quantity'] > 0.000001:
        agg = result[0]
        db.holdings.insert_one({'user_id': user_id, 'symbol': symbol, 'quantity': agg['total_quantity'], 'cost_basis': agg['total_cost'], 'average_cost': agg['total_cost'] / agg['total_quantity']})

@bp.route('/')
@login_required
def index():
    """Main dashboard route, reads data only from the database."""
    user_id = ObjectId(current_user.id)
    holdings = list(db.holdings.find({'user_id': user_id}).sort('symbol', 1))
    
    price_data_cursor = db.prices.find({'symbol': {'$in': [h['symbol'] for h in holdings]}})
    price_map = {p['symbol']: p for p in price_data_cursor}
    
    latest_update_record = db.prices.find_one(sort=[("last_updated", DESCENDING)])
    last_updated_time = latest_update_record.get('last_updated') if latest_update_record else None

    total_market_value, total_cost_basis, total_day_change = 0, 0, 0
    
    for h in holdings:
        price_info = price_map.get(h['symbol'])
        
        if price_info:
            h.update({
                'name': price_info.get('name', h['symbol']),
                'current_price': price_info.get('current_price', h['average_cost']),
                'market_value': h['quantity'] * price_info.get('current_price', h['average_cost']),
                'day_change': (price_info.get('current_price', 0) - price_info.get('previous_close', 0)) * h['quantity'],
                'api_error': False
            })
        else:
            h.update({'name': h['symbol'], 'current_price': h['average_cost'], 'market_value': h['quantity'] * h['average_cost'], 'day_change': 0, 'api_error': True})
        
        h['total_gain_loss'] = h['market_value'] - h['cost_basis']
        total_market_value += h['market_value']
        total_cost_basis += h['cost_basis']
        if not h['api_error']:
            total_day_change += h['day_change']
            
    grand_total = {'market_value': total_market_value, 'cost_basis': total_cost_basis, 'total_gain_loss': total_market_value - total_cost_basis, 'day_change': total_day_change}
    
    return render_template('index.html', holdings=holdings, grand_total=grand_total, last_updated=last_updated_time)

@bp.route('/refresh_prices', methods=['POST'])
@login_required
def refresh_prices_route():
    """Manually triggers the price update script."""
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    last_refresh_str = session.get('last_refresh')
    if last_refresh_str:
        last_refresh = datetime.fromisoformat(last_refresh_str)
        if last_refresh > five_minutes_ago:
            flash("You can only refresh prices once every 5 minutes.", "warning")
            return redirect(url_for('main.index'))

    try:
        print("--- [Manual Trigger] Running Price Update ---")
        update_stock_prices()
        session['last_refresh'] = datetime.utcnow().isoformat()
        flash("Price data has been updated successfully!", "success")
    except Exception as e:
        flash(f"An error occurred during the update: {e}", "danger")
        print(f"Manual refresh failed: {e}")

    return redirect(url_for('main.index'))

@bp.route('/transactions')
@login_required
def list_transactions():
    user_id = ObjectId(current_user.id)
    transactions = list(db.transactions.find({'user_id': user_id}).sort('date', DESCENDING))
    return render_template('transactions.html', transactions=transactions)

@bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction_route():
    user_id = ObjectId(current_user.id)
    symbol = request.form['symbol'].strip().upper()
    if symbol.isdigit() and len(symbol) == 4: symbol += ".TW"
    try:
        db.transactions.insert_one({'user_id': user_id, 'symbol': symbol, 'quantity': float(request.form['quantity']), 'price': float(request.form['price']), 'date': datetime.utcnow()})
        recalculate_holding(user_id, symbol)
        flash(f"Added {symbol}. Click 'Refresh Prices' to fetch its latest data.", "info")
    except: flash("Error adding transaction", "danger")
    return redirect(url_for('main.index'))

@bp.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction_route(transaction_id):
    user_id = ObjectId(current_user.id)
    t = db.transactions.find_one({'_id': ObjectId(transaction_id), 'user_id': user_id})
    if not t: return redirect(url_for('main.list_transactions'))
    if request.method == 'POST':
        db.transactions.update_one({'_id': ObjectId(transaction_id)}, {'$set': {'quantity': float(request.form['quantity']), 'price': float(request.form['price'])}})
        recalculate_holding(user_id, t['symbol'])
        flash("Transaction updated successfully.", "success")
        return redirect(url_for('main.list_transactions'))
    return render_template('edit_transaction.html', transaction=t)

@bp.route('/delete_transaction/<transaction_id>', methods=['POST'])
@login_required
def delete_transaction_route(transaction_id):
    user_id = ObjectId(current_user.id)
    t = db.transactions.find_one({'_id': ObjectId(transaction_id), 'user_id': user_id})
    if t:
        db.transactions.delete_one({'_id': ObjectId(transaction_id)})
        recalculate_holding(user_id, t['symbol'])
        flash("Transaction deleted successfully.", "info")
    return redirect(url_for('main.list_transactions'))

@bp.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv_route():
    user_id = ObjectId(current_user.id)
    f = request.files.get('csv_file')
    if f:
        db.holdings.delete_many({'user_id': user_id})
        db.transactions.delete_many({'user_id': user_id})
        stream = io.StringIO(f.stream.read().decode("UTF-8"), newline=None)
        reader = csv.DictReader(stream)
        transactions = [{'user_id': user_id, 'symbol': row['Symbol'].strip().upper(), 'quantity': float(row['Quantity']), 'price': float(row['Price']), 'date': datetime.utcnow()} for row in reader if row.get('Symbol')]
        if transactions:
            db.transactions.insert_many(transactions)
            for sym in {t['symbol'] for t in transactions}: recalculate_holding(user_id, sym)
            flash("CSV Imported. Click 'Refresh Prices' to fetch the latest data.", "info")
    return redirect(url_for('main.index'))

@bp.route('/export_csv')
@login_required
def export_csv_route():
    user_id = ObjectId(current_user.id)
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=['Symbol', 'Quantity', 'Price', 'Date'])
    writer.writeheader()
    for t in db.transactions.find({'user_id': user_id}, {'_id': 0, 'user_id': 0}):
        t['Date'] = t.pop('date').strftime('%Y-%m-%d %H:%M:%S')
        t['Symbol'] = t.pop('symbol'); t['Quantity'] = t.pop('quantity'); t['Price'] = t.pop('price')
        writer.writerow(t)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=transactions.csv"})

@bp.route('/delete_all', methods=['POST'])
@login_required
def delete_all_route():
    user_id = ObjectId(current_user.id)
    db.holdings.delete_many({'user_id': user_id})
    db.transactions.delete_many({'user_id': user_id})
    flash("Portfolio cleared", "info")
    return redirect(url_for('main.index'))