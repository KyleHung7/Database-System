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
    symbol = request.form.get('symbol', '').strip().upper()

    if not symbol:
        flash("Symbol is required.", "danger")
        return redirect(url_for('main.index'))

    if symbol.isdigit() and len(symbol) == 4:
        symbol += ".TW"

    try:
        quantity = float(request.form['quantity'])
        price = float(request.form['price'])

        if quantity <= 0 or price <= 0:
            flash("Quantity and price must be positive values.", "danger")
            return redirect(url_for('main.index'))

        db.transactions.insert_one({
            'user_id': user_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'date': datetime.utcnow()
        })
        recalculate_holding(user_id, symbol)
        flash(f"Added {symbol}. Click 'Refresh Prices' to fetch its latest data.", "info")

    except (ValueError, TypeError):
        flash("Invalid input for quantity or price. Please enter valid numbers.", "danger")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")

    return redirect(url_for('main.index'))

@bp.route('/edit_transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction_route(transaction_id):
    try:
        user_id = ObjectId(current_user.id)
        transaction = db.transactions.find_one({'_id': ObjectId(transaction_id), 'user_id': user_id})
        if not transaction:
            flash("Transaction not found.", "danger")
            return redirect(url_for('main.list_transactions'))

        if request.method == 'POST':
            quantity = float(request.form['quantity'])
            price = float(request.form['price'])

            if quantity <= 0 or price <= 0:
                flash("Quantity and price must be positive values.", "danger")
                return render_template('edit_transaction.html', transaction=transaction)

            db.transactions.update_one(
                {'_id': ObjectId(transaction_id)},
                {'$set': {'quantity': quantity, 'price': price}}
            )
            recalculate_holding(user_id, transaction['symbol'])
            flash("Transaction updated successfully.", "success")
            return redirect(url_for('main.list_transactions'))

        return render_template('edit_transaction.html', transaction=transaction)

    except (ValueError, TypeError):
        flash("Invalid input for quantity or price. Please enter valid numbers.", "danger")
        return redirect(url_for('main.list_transactions'))
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        return redirect(url_for('main.list_transactions'))

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
    
    if not f:
        flash("No file uploaded.", "danger")
        return redirect(url_for('main.index'))

    try:
        db.holdings.delete_many({'user_id': user_id})
        db.transactions.delete_many({'user_id': user_id})
        
        stream = io.StringIO(f.stream.read().decode("UTF-8"), newline=None)
        reader = csv.DictReader(stream)
        
        transactions_to_insert = []
        for row in reader:
            symbol = row.get('Symbol', '').strip().upper()
            if not symbol:
                continue # Skip rows without a symbol

            try:
                quantity = float(row['Quantity'])
                price = float(row['Price'])

                if quantity <= 0 or price <= 0:
                    flash(f"Skipping row for {symbol}: Quantity and price must be positive.", "warning")
                    continue

                transactions_to_insert.append({
                    'user_id': user_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'date': datetime.utcnow() # Using current time for all imported transactions
                })
            except (ValueError, TypeError):
                flash(f"Skipping row for {symbol}: Invalid quantity or price format.", "warning")
            except KeyError as e:
                flash(f"Skipping row for {symbol}: Missing expected column - {e}.", "warning")

        if transactions_to_insert:
            db.transactions.insert_many(transactions_to_insert)
            # Recalculate holdings for all unique symbols imported
            for sym in {t['symbol'] for t in transactions_to_insert}:
                recalculate_holding(user_id, sym)
            flash(f"Successfully imported {len(transactions_to_insert)} transactions. Click 'Refresh Prices' to fetch the latest data.", "success")
        else:
            flash("No valid transactions found in the CSV file.", "info")

    except UnicodeDecodeError:
        flash("Error decoding file. Please ensure the CSV is UTF-8 encoded.", "danger")
    except csv.Error as e:
        flash(f"Error parsing CSV file: {e}", "danger")
    except Exception as e:
        flash(f"An unexpected error occurred during CSV import: {e}", "danger")

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

@bp.route('/bulk_edit_symbol', methods=['GET', 'POST'])
@login_required
def bulk_edit_symbol_route():
    if request.method == 'POST':
        user_id = ObjectId(current_user.id)
        old_symbol = request.form['old_symbol'].strip().upper()
        new_symbol = request.form['new_symbol'].strip().upper()

        if not old_symbol or not new_symbol:
            flash("Both old and new symbols are required.", "danger")
            return redirect(url_for('main.bulk_edit_symbol_route'))

        try:
            # Use update_many to change the symbol in all matching transactions
            result = db.transactions.update_many(
                {'user_id': user_id, 'symbol': old_symbol},
                {'$set': {'symbol': new_symbol}}
            )

            if result.modified_count > 0:
                # Recalculate holdings for both old and new symbols
                recalculate_holding(user_id, old_symbol)
                recalculate_holding(user_id, new_symbol)
                flash(f"Updated {result.modified_count} transactions from {old_symbol} to {new_symbol}.", "success")
            else:
                flash(f"No transactions found for symbol {old_symbol}.", "info")
            
            return redirect(url_for('main.list_transactions'))

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('main.bulk_edit_symbol_route'))

    return render_template('bulk_edit_symbol.html')
