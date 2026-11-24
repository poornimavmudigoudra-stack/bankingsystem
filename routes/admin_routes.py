import io
import csv
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
from models import db, User, Transaction

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to enforce admin privileges."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Access denied. Administrator privileges are required.', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_customers = User.query.filter_by(role='customer').count()
    active_customers = User.query.filter_by(role='customer', is_active=True).count()
    frozen_customers = User.query.filter_by(role='customer', is_active=False).count()

    customer_users = User.query.filter_by(role='customer').all()
    total_holdings = sum(u.balance for u in customer_users)

    total_transactions_count = Transaction.query.count()

    recent_transactions = (
        Transaction.query
        .order_by(Transaction.timestamp.desc())
        .limit(8)
        .all()
    )

    recent_customers = (
        User.query
        .filter_by(role='customer')
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'admin/dashboard.html',
        total_customers=total_customers,
        active_customers=active_customers,
        frozen_customers=frozen_customers,
        total_holdings=total_holdings,
        total_transactions_count=total_transactions_count,
        recent_transactions=recent_transactions,
        recent_customers=recent_customers
    )


@admin_bp.route('/customers')
@admin_required
def customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    query = User.query.filter_by(role='customer')

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'frozen':
        query = query.filter_by(is_active=False)

    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.username.ilike(f'%{search}%')) |
            (User.account_number.ilike(f'%{search}%'))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        'admin/customers.html',
        customers=pagination.items,
        pagination=pagination,
        search_query=search,
        selected_status=status_filter
    )


@admin_bp.route('/customers/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_customer_status(user_id):
    target_user = db.get_or_404(User, user_id)

    if target_user.is_admin():
        flash('Cannot modify status of an administrator account.', 'danger')
        return redirect(url_for('admin.customers'))

    target_user.is_active = not target_user.is_active
    db.session.commit()

    status_str = 'activated' if target_user.is_active else 'frozen'
    flash(f"Customer {target_user.full_name}'s account has been {status_str}.", 'success')
    return redirect(request.referrer or url_for('admin.customers'))


@admin_bp.route('/accounts')
@admin_required
def accounts():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = User.query.filter_by(role='customer')

    if search:
        query = query.filter(
            (User.account_number.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )

    pagination = query.order_by(User.balance.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    customer_users = User.query.filter_by(role='customer').all()
    total_liquidity = sum(u.balance for u in customer_users)
    average_balance = (total_liquidity / len(customer_users)) if customer_users else 0.0

    return render_template(
        'admin/accounts.html',
        accounts=pagination.items,
        pagination=pagination,
        search_query=search,
        total_liquidity=total_liquidity,
        average_balance=average_balance
    )


@admin_bp.route('/transactions')
@admin_required
def transactions():
    page = request.args.get('page', 1, type=int)
    txn_type = request.args.get('type', 'all').strip()
    search = request.args.get('q', '').strip()

    query = Transaction.query

    if txn_type and txn_type != 'all':
        query = query.filter_by(transaction_type=txn_type)

    if search:
        query = query.filter(
            (Transaction.reference_id.ilike(f'%{search}%')) |
            (Transaction.description.ilike(f'%{search}%')) |
            (Transaction.recipient_name.ilike(f'%{search}%')) |
            (Transaction.recipient_account.ilike(f'%{search}%'))
        )

    pagination = query.order_by(Transaction.timestamp.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template(
        'admin/transactions.html',
        transactions=pagination.items,
        pagination=pagination,
        selected_type=txn_type,
        search_query=search
    )


@admin_bp.route('/transactions/export')
@admin_required
def export_transactions():
    txns = Transaction.query.order_by(Transaction.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Reference ID', 'Date & Time', 'Customer Name', 'Account Number',
        'Type', 'Amount', 'Balance After', 'Recipient Name', 'Recipient Account', 'Description'
    ])

    for t in txns:
        user_name = t.user.full_name if t.user else 'Unknown'
        acc_num = t.user.account_number if t.user else 'N/A'
        writer.writerow([
            t.reference_id,
            t.timestamp.strftime('%Y-%m-%d %H:%M:%S') if t.timestamp else '',
            user_name,
            acc_num,
            t.transaction_type,
            f"{t.amount:.2f}",
            f"{t.balance_after:.2f}",
            t.recipient_name or '',
            t.recipient_account or '',
            t.description
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=admin_all_transactions.csv"}
    )
