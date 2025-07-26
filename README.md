# assignments.md-solved

Bank Loan System API - Agetware Assignment
This repository contains the solution for the Bank Loan System Design (assignment.md) part of the Agetware technical assignment. It features a RESTful API built with Python and Flask that provides core banking functionalities for managing loans.

1. Problem Statement
The objective was to design and implement a system for a bank to lend money and receive payments. The system must expose its functionality via RESTful APIs and should include functions to:

LEND: Create a new loan for a customer.

PAYMENT: Process payments (EMI or lump sum) against a loan.

LEDGER: View the detailed transaction history and status of a specific loan.

ACCOUNT OVERVIEW: Get a summary of all loans taken by a customer.

2. System Design & Technology Stack
The system was designed with simplicity and efficiency in mind, using the following technologies:

Web Framework: Flask (Python) - Chosen for its lightweight nature and flexibility, making it ideal for rapid API development.

Database: SQLite - A simple, file-based database was selected for its ease of use and zero-configuration setup.

ORM: SQLAlchemy - Used to abstract database operations, leading to cleaner, more maintainable, and secure Python code.

3. How to Run the System
Prerequisites
Python 3

pip (Python package installer)

Step 1: Clone the Repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

Step 2: Install Dependencies
Install the required Python packages from your terminal.

pip install Flask Flask-SQLAlchemy

Step 3: Run the Server
Execute the main application file to start the API server.

python app.py

The server will start and be accessible at http://127.0.0.1:5001.

4. API Endpoints & Usage Examples
The following endpoints are available. You can use tools like Postman, Insomnia, or command-line utilities like curl to interact with them.

a. POST /lend
Creates a new loan.

Request Body:

{
    "customer_id": "cust123",
    "loan_amount": 10000,
    "loan_period": 2,
    "rate_of_interest": 8
}

Example (PowerShell):

Invoke-WebRequest -Uri http://127.0.0.1:5001/lend -Method POST -Body '{"customer_id": "cust123", "loan_amount": 10000, "loan_period": 2, "rate_of_interest": 8}' -ContentType 'application/json'

Success Response:

{
  "loan_id": 1,
  "monthly_emi": 483.33,
  "total_amount": 11600.0
}

b. POST /payment
Records a payment against a loan.

Request Body:

{
    "loan_id": 1,
    "amount": 5000
}

Example (PowerShell):

Invoke-WebRequest -Uri http://127.0.0.1:5001/payment -Method POST -Body '{"loan_id": 1, "amount": 5000}' -ContentType 'application/json'

Success Response:

{
  "message": "Payment successful",
  "remaining_amount": 6600.0
}

c. GET /ledger/<loan_id>
Retrieves the full history and status of a specific loan.

Example (Browser or PowerShell):

Invoke-WebRequest -Uri http://127.0.0.1:5001/ledger/1

d. GET /overview/<customer_id>
Lists all loans for a given customer.

Example (Browser or PowerShell):

Invoke-WebRequest -Uri http://127.0.0.1:5001/overview/cust123

5. Full Source Code (app.py)
import os
import math
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- Basic Flask App and Database Setup ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bank.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(80), nullable=False, index=True)
    principal = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    period_years = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    emi = db.Column(db.Float, nullable=False)
    transactions = db.relationship('Transaction', backref='loan', lazy=True, cascade="all, delete-orphan")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helper Functions ---
def get_loan_status(loan):
    total_paid = sum(t.amount for t in loan.transactions)
    balance_amount = loan.total_amount - total_paid
    emis_left = math.ceil(balance_amount / loan.emi) if loan.emi > 0 else 0
    return total_paid, balance_amount, max(0, emis_left)

# --- API Endpoints ---
@app.route('/lend', methods=['POST'])
def lend_money():
    data = request.get_json()
    p, n, r = data['loan_amount'], data['loan_period'], data['rate_of_interest']
    interest = (p * n * r) / 100
    total_amount = p + interest
    emi = total_amount / (n * 12) if n > 0 else total_amount
    new_loan = Loan(customer_id=data['customer_id'], principal=p, rate=r, period_years=n, total_amount=total_amount, emi=emi)
    db.session.add(new_loan)
    db.session.commit()
    return jsonify({"loan_id": new_loan.id, "total_amount": round(total_amount, 2), "monthly_emi": round(emi, 2)}), 201

@app.route('/payment', methods=['POST'])
def make_payment():
    data = request.get_json()
    loan = Loan.query.get(data['loan_id'])
    if not loan: return jsonify({"error": "Loan not found"}), 404
    db.session.add(Transaction(loan_id=loan.id, amount=data['amount']))
    db.session.commit()
    _, remaining_amount, _ = get_loan_status(loan)
    return jsonify({"message": "Payment successful", "remaining_amount": round(remaining_amount, 2)}), 200

@app.route('/ledger/<int:loan_id>', methods=['GET'])
def get_ledger(loan_id):
    loan = Loan.query.get(loan_id)
    if not loan: return jsonify({"error": "Loan not found"}), 404
    total_paid, balance, emis_left = get_loan_status(loan)
    return jsonify({
        "principal": loan.principal, "total_amount": loan.total_amount, "monthly_emi": round(loan.emi, 2),
        "transactions": [{"date": t.payment_date.isoformat(), "amount": t.amount} for t in loan.transactions],
        "total_paid": round(total_paid, 2), "balance_amount": round(balance, 2), "emis_left": emis_left
    })

@app.route('/overview/<string:customer_id>', methods=['GET'])
def get_account_overview(customer_id):
    loans = Loan.query.filter_by(customer_id=customer_id).all()
    if not loans: return jsonify({"error": "No loans found"}), 404
    overview = []
    for loan in loans:
        total_paid, _, emis_left = get_loan_status(loan)
        overview.append({
            "loan_id": loan.id, "principal": loan.principal, "total_amount": loan.total_amount,
            "emi_amount": round(loan.emi, 2), "amount_paid": round(total_paid, 2), "emis_left": emis_left
        })
    return jsonify({"customer_id": customer_id, "loans": overview})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
