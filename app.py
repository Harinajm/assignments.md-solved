import os
import math
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Basic Flask App and Database Setup ---
# Get the base directory of the script
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask App
app = Flask(__name__)

# Configure the database (SQLite)
# The database file will be created in the same directory as the script
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bank.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy ORM
db = SQLAlchemy(app)


# --- Database Models ---

class Loan(db.Model):
    """Represents a loan given to a customer."""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(80), nullable=False, index=True)
    principal = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    period_years = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    emi = db.Column(db.Float, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to transactions
    transactions = db.relationship('Transaction', backref='loan', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Loan {self.id} for Customer {self.customer_id}>'

class Transaction(db.Model):
    """Represents a payment transaction for a loan."""
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.id} of {self.amount} for Loan {self.loan_id}>'


# --- Helper Functions ---

def calculate_loan_details(principal, period_years, rate):
    """Calculates total amount and EMI based on simple interest."""
    interest = (principal * period_years * rate) / 100
    total_amount = principal + interest
    # Ensure total months is at least 1 to avoid division by zero
    total_months = period_years * 12
    if total_months == 0:
        emi = total_amount
    else:
        emi = total_amount / total_months
    return total_amount, emi

def get_loan_status(loan):
    """Calculates the current status of a loan (paid, balance, EMIs left)."""
    total_paid = sum(t.amount for t in loan.transactions)
    balance_amount = loan.total_amount - total_paid
    
    # Ensure EMI is not zero to avoid division by zero
    if loan.emi > 0:
        emis_left = math.ceil(balance_amount / loan.emi)
    else:
        emis_left = 0
        
    # Ensure emis_left is not negative
    return total_paid, balance_amount, max(0, emis_left)


# --- API Endpoints ---

@app.route('/lend', methods=['POST'])
def lend_money():
    """
    LEND function: Creates a new loan.
    """
    data = request.get_json()
    if not all(k in data for k in ['customer_id', 'loan_amount', 'loan_period', 'rate_of_interest']):
        return jsonify({"error": "Missing required fields"}), 400

    p = data['loan_amount']
    n = data['loan_period']
    r = data['rate_of_interest']

    total_amount, emi = calculate_loan_details(p, n, r)

    new_loan = Loan(
        customer_id=data['customer_id'],
        principal=p,
        rate=r,
        period_years=n,
        total_amount=total_amount,
        emi=emi
    )
    db.session.add(new_loan)
    db.session.commit()

    return jsonify({
        "loan_id": new_loan.id,
        "total_amount": round(total_amount, 2),
        "monthly_emi": round(emi, 2)
    }), 201

@app.route('/payment', methods=['POST'])
def make_payment():
    """
    PAYMENT function: Records a payment for a loan.
    """
    data = request.get_json()
    if not all(k in data for k in ['loan_id', 'amount']):
        return jsonify({"error": "Missing required fields"}), 400

    loan = Loan.query.get(data['loan_id'])
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    new_transaction = Transaction(
        loan_id=loan.id,
        amount=data['amount']
    )
    db.session.add(new_transaction)
    db.session.commit()
    
    _, remaining_amount, _ = get_loan_status(loan)

    return jsonify({
        "message": "Payment successful",
        "loan_id": loan.id,
        "remaining_amount": round(remaining_amount, 2)
    }), 200

@app.route('/ledger/<int:loan_id>', methods=['GET'])
def get_ledger(loan_id):
    """
    LEDGER function: Retrieves the transaction history and status of a loan.
    """
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404

    total_paid, balance_amount, emis_left = get_loan_status(loan)

    transaction_history = [
        {"date": t.payment_date.isoformat(), "amount": t.amount}
        for t in loan.transactions
    ]

    return jsonify({
        "loan_id": loan.id,
        "principal": loan.principal,
        "total_amount": loan.total_amount,
        "monthly_emi": round(loan.emi, 2),
        "transactions": transaction_history,
        "total_paid": round(total_paid, 2),
        "balance_amount": round(balance_amount, 2),
        "emis_left": emis_left
    })

@app.route('/overview/<string:customer_id>', methods=['GET'])
def get_account_overview(customer_id):
    """
    ACCOUNT OVERVIEW function: Lists all loans for a customer.
    """
    customer_loans = Loan.query.filter_by(customer_id=customer_id).all()
    if not customer_loans:
        return jsonify({"error": "No loans found for this customer"}), 404

    overview = []
    for loan in customer_loans:
        total_paid, _, emis_left = get_loan_status(loan)
        total_interest = loan.total_amount - loan.principal
        
        overview.append({
            "loan_id": loan.id,
            "principal": loan.principal,
            "total_amount": loan.total_amount,
            "total_interest": round(total_interest, 2),
            "emi_amount": round(loan.emi, 2),
            "amount_paid": round(total_paid, 2),
            "emis_left": emis_left
        })

    return jsonify({
        "customer_id": customer_id,
        "loans": overview
    })


# --- Main execution block ---
if __name__ == '__main__':
    # Create the database and tables if they don't exist
    with app.app_context():
        db.create_all()
    # Run the Flask app
    app.run(debug=True, port=5001)
