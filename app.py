import os
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from config import config_by_name
from models import db, User, Transaction
from routes import auth_bp, user_bp, admin_bp


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this secure banking area.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Auto-initialize database & seed data within app context
    with app.app_context():
        db.create_all()
        seed_initial_data()

    # Global Context Processors
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Apex National Bank',
            'current_year': datetime.now(timezone.utc).year,
            'now': datetime.now(timezone.utc)
        }

    # Root route - Landing page
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        return render_template('index.html')

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            'base.html',
            error_title="403 - Forbidden Access",
            error_message="You do not have administrative clearance to view this secure financial area."
        ), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template(
            'base.html',
            error_title="404 - Page Not Found",
            error_message="The requested financial page does not exist or has moved."
        ), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template(
            'base.html',
            error_title="500 - Server Error",
            error_message="An internal banking transaction error occurred. Our engineers have been notified."
        ), 500

    # CLI command: initialize database
    @app.cli.command('init-db')
    def init_db():
        """Create all database tables."""
        db.create_all()
        print("Database tables created successfully.")

    # CLI command: seed database
    @app.cli.command('seed-db')
    def seed_db():
        """Seed database with initial admin and customer data."""
        seed_initial_data()
        print("Database seeded successfully.")

    return app


def seed_initial_data():
    """Seed initial administrator and demo customer if not already present."""
    # 1. Admin User
    if not User.query.filter_by(username='admin').first():
        admin = User(
            full_name='System Administrator',
            email='admin@apexbank.com',
            username='admin',
            account_number='100000000001',
            balance=0.0,
            role='admin',
            is_active=True,
            phone_number='+1-800-555-0199'
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

    # 2. Demo User: Poorvi
    demo_user = User.query.filter_by(username='poorvi').first()
    if not demo_user:
        demo_user = User(
            full_name='Poornima Veeranagouda',
            email='poorvi@example.com',
            username='poorvi',
            account_number='984729104823',
            balance=5420.50,
            role='customer',
            is_active=True,
            phone_number='+1-555-0142'
        )
        demo_user.set_password('poorvi@123')
        db.session.add(demo_user)
        db.session.flush()

        # Initial demo transactions
        t1 = Transaction(
            user_id=demo_user.id,
            transaction_type='deposit',
            amount=5000.00,
            balance_after=5000.00,
            description='Initial Account Opening Deposit',
            reference_id='TXN-INIT001'
        )
        t2 = Transaction(
            user_id=demo_user.id,
            transaction_type='deposit',
            amount=1000.00,
            balance_after=6000.00,
            description='Payroll Direct Deposit',
            reference_id='TXN-DEP002'
        )
        t3 = Transaction(
            user_id=demo_user.id,
            transaction_type='withdrawal',
            amount=300.00,
            balance_after=5700.00,
            description='ATM Cash Withdrawal - Main St Branch',
            recipient_name='ATM Branch #102',
            recipient_account='ATM-102',
            reference_id='TXN-WTH003'
        )
        t4 = Transaction(
            user_id=demo_user.id,
            transaction_type='transfer_debit',
            amount=279.50,
            balance_after=5420.50,
            description='High-Speed Fiber Internet Bill',
            recipient_name='Utility Pay Corp',
            recipient_account='847291038291',
            reference_id='TXN-TRF004'
        )
        db.session.add_all([t1, t2, t3, t4])

    # 3. Secondary Demo User: Alex
    if not User.query.filter_by(username='alex_turner').first():
        alex = User(
            full_name='Alex Turner',
            email='alex.turner@example.com',
            username='alex_turner',
            account_number='847291038291',
            balance=12500.00,
            role='customer',
            is_active=True,
            phone_number='+1-555-0188'
        )
        alex.set_password('Alex@123')
        db.session.add(alex)

    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
