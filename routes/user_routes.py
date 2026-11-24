import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, User, Transaction, generate_reference_id

user_bp = Blueprint('user', __name__)


@user_bp.route('/dashboard')
@user_bp.route('/user/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    recent_transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.desc())
        .limit(6)
        .all()
    )

    all_txns = Transaction.query.filter_by(user_id=current_user.id).all()
    total_deposited = sum(t.amount for t in all_txns if t.transaction_type in ('deposit', 'transfer_credit'))
    total_spent = sum(t.amount for t in all_txns if t.transaction_type in ('withdrawal', 'transfer_debit'))

    return render_template(
        'user/dashboard.html',
        recent_transactions=recent_transactions,
        total_deposited=total_deposited,
        total_spent=total_spent,
        total_txns=len(all_txns)
    )


@user_bp.route('/balance')
@user_bp.route('/user/balance')
@login_required
def balance():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    last_transaction = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.desc())
        .first()
    )

    return render_template(
        'user/balance.html',
        last_transaction=last_transaction
    )


@user_bp.route('/deposit', methods=['GET', 'POST'])
@user_bp.route('/user/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()

        try:
            amount = round(float(amount_str), 2)
        except (ValueError, TypeError):
            flash('Please enter a valid numeric amount.', 'danger')
            return render_template('user/deposit.html')

        if amount <= 0:
            flash('Deposit amount must be greater than $0.00.', 'danger')
            return render_template('user/deposit.html')

        if amount > 1_000_000:
            flash('Single deposit amount cannot exceed $1,000,000.', 'danger')
            return render_template('user/deposit.html')

        current_user.balance = round(current_user.balance + amount, 2)
        txn = Transaction(
            user_id=current_user.id,
            transaction_type='deposit',
            amount=amount,
            balance_after=current_user.balance,
            description=description or 'Electronic Fund Deposit'
        )
        db.session.add(txn)
        db.session.commit()

        flash(f'Successfully deposited ${amount:,.2f}. Your new balance is ${current_user.balance:,.2f}.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/deposit.html')


@user_bp.route('/withdraw', methods=['GET', 'POST'])
@user_bp.route('/user/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()

        try:
            amount = round(float(amount_str), 2)
        except (ValueError, TypeError):
            flash('Please enter a valid numeric amount.', 'danger')
            return render_template('user/withdraw.html')

        if amount <= 0:
            flash('Withdrawal amount must be greater than $0.00.', 'danger')
            return render_template('user/withdraw.html')

        if amount > current_user.balance:
            flash(f'Insufficient funds. Your current balance is ${current_user.balance:,.2f}.', 'danger')
            return render_template('user/withdraw.html')

        current_user.balance = round(current_user.balance - amount, 2)
        txn = Transaction(
            user_id=current_user.id,
            transaction_type='withdrawal',
            amount=amount,
            balance_after=current_user.balance,
            description=description or 'Cash / ATM Withdrawal'
        )
        db.session.add(txn)
        db.session.commit()

        flash(f'Successfully withdrew ${amount:,.2f}. Remaining balance: ${current_user.balance:,.2f}.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/withdraw.html')


@user_bp.route('/transfer', methods=['GET', 'POST'])
@user_bp.route('/user/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        recipient_account = request.form.get('recipient_account', '').strip()
        amount_str = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()

        if not recipient_account:
            flash('Recipient account number is required.', 'danger')
            return render_template('user/transfer.html')

        if recipient_account == current_user.account_number:
            flash('You cannot transfer funds to your own account number.', 'warning')
            return render_template('user/transfer.html')

        try:
            amount = round(float(amount_str), 2)
        except (ValueError, TypeError):
            flash('Please enter a valid numeric transfer amount.', 'danger')
            return render_template('user/transfer.html')

        if amount <= 0:
            flash('Transfer amount must be greater than $0.00.', 'danger')
            return render_template('user/transfer.html')

        if amount > current_user.balance:
            flash(f'Transfer failed: Insufficient balance (${current_user.balance:,.2f}).', 'danger')
            return render_template('user/transfer.html')

        recipient = User.query.filter_by(account_number=recipient_account).first()
        if not recipient:
            flash('Recipient account not found. Please verify the 12-digit account number.', 'danger')
            return render_template('user/transfer.html')

        if not recipient.is_active:
            flash('Recipient account is currently frozen or inactive. Transfer cancelled.', 'danger')
            return render_template('user/transfer.html')

        # Atomic Transfer
        current_user.balance = round(current_user.balance - amount, 2)
        recipient.balance = round(recipient.balance + amount, 2)

        transfer_ref = generate_reference_id()

        # Debit entry for sender
        debit_txn = Transaction(
            user_id=current_user.id,
            transaction_type='transfer_debit',
            amount=amount,
            balance_after=current_user.balance,
            description=description or f'Transfer to {recipient.full_name}',
            recipient_name=recipient.full_name,
            recipient_account=recipient.account_number,
            reference_id=transfer_ref
        )

        # Credit entry for recipient
        credit_txn = Transaction(
            user_id=recipient.id,
            transaction_type='transfer_credit',
            amount=amount,
            balance_after=recipient.balance,
            description=description or f'Transfer from {current_user.full_name}',
            recipient_name=current_user.full_name,
            recipient_account=current_user.account_number,
            reference_id=f'{transfer_ref}-CR'
        )

        db.session.add(debit_txn)
        db.session.add(credit_txn)
        db.session.commit()

        flash(
            f'Successfully transferred ${amount:,.2f} to {recipient.full_name} ({recipient.account_number}). Ref: {transfer_ref}',
            'success'
        )
        return redirect(url_for('user.dashboard'))

    return render_template('user/transfer.html')


@user_bp.route('/transactions')
@user_bp.route('/user/transactions')
@login_required
def transactions():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    txn_type = request.args.get('type', 'all').strip()
    search = request.args.get('q', '').strip()

    query = Transaction.query.filter_by(user_id=current_user.id)

    if txn_type and txn_type != 'all':
        query = query.filter_by(transaction_type=txn_type)

    if search:
        query = query.filter(
            (Transaction.description.ilike(f'%{search}%')) |
            (Transaction.reference_id.ilike(f'%{search}%')) |
            (Transaction.recipient_name.ilike(f'%{search}%')) |
            (Transaction.recipient_account.ilike(f'%{search}%'))
        )

    pagination = query.order_by(Transaction.timestamp.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template(
        'user/transactions.html',
        transactions=pagination.items,
        pagination=pagination,
        selected_type=txn_type,
        search_query=search
    )


@user_bp.route('/transactions/export')
@login_required
def export_transactions():
    """Export transactions to CSV."""
    txns = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Reference ID', 'Date & Time', 'Type', 'Amount',
        'Balance After', 'Recipient Name', 'Recipient Account', 'Description'
    ])

    for t in txns:
        writer.writerow([
            t.reference_id,
            t.timestamp.strftime('%Y-%m-%d %H:%M:%S') if t.timestamp else '',
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
        headers={"Content-Disposition": f"attachment;filename=transactions_{current_user.account_number}.csv"}
    )


@user_bp.route('/profile', methods=['GET', 'POST'])
@user_bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone_number = request.form.get('phone_number', '').strip()

            if not full_name or not email:
                flash('Full name and email address are required.', 'danger')
            else:
                existing = User.query.filter_by(email=email).first()
                if existing and existing.id != current_user.id:
                    flash('That email address is already registered to another account.', 'danger')
                else:
                    current_user.full_name = full_name
                    current_user.email = email
                    current_user.phone_number = phone_number or None
                    db.session.commit()
                    flash('Personal profile information updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_new_password', '')

            if not current_user.check_password(current_pw):
                flash('Current password verification failed.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Password has been updated securely.', 'success')

        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')
