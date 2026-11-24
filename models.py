from datetime import datetime, timezone
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def generate_reference_id():
    """Generate a unique reference ID for transactions."""
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    role = db.Column(db.String(20), default="customer", nullable=False)  # 'customer' or 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = db.relationship(
        "Transaction",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="desc(Transaction.timestamp)"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "username": self.username,
            "account_number": self.account_number,
            "balance": round(self.balance, 2),
            "role": self.role,
            "is_active": self.is_active,
            "phone_number": self.phone_number,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }

    def __repr__(self):
        return f"<User {self.username} ({self.account_number})>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = db.Column(db.String(30), nullable=False)  # deposit, withdrawal, transfer_debit, transfer_credit
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), default="", nullable=False)
    recipient_name = db.Column(db.String(100), nullable=True)
    recipient_account = db.Column(db.String(50), nullable=True)
    reference_id = db.Column(db.String(50), unique=True, default=generate_reference_id, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "amount": round(self.amount, 2),
            "balance_after": round(self.balance_after, 2),
            "description": self.description,
            "recipient_name": self.recipient_name,
            "recipient_account": self.recipient_account,
            "reference_id": self.reference_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else ""
        }

    def __repr__(self):
        return f"<Transaction {self.reference_id} - {self.transaction_type} ${self.amount}>"
