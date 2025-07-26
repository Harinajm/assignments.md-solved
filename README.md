# assignments.md-solved
2. Part 1: Bank Loan System Design (assignment.md)
2.1. Problem Statement
Design and implement a system for a bank to lend money and receive payments. The system must expose its functionality via RESTful APIs and should include functions to LEND money, process a PAYMENT, view a loan LEDGER, and get an ACCOUNT OVERVIEW.
2.2. System Design & Technology Stack
Web Framework: Flask (Python) - Chosen for its lightweight nature and flexibility, making it ideal for rapid API development.
Database: SQLite - A simple, file-based database was selected for its ease of use and zero-configuration setup, aligning with the project's goal of simplicity.
ORM: SQLAlchemy - Used to abstract database operations, leading to cleaner, more maintainable, and secure Python code.
2.3. Data Models
Loan Table: Stores the core details of each loan, including customer_id, principal, rate, period_years, total_amount, and emi.
Transaction Table: Records every payment made against a loan, linked via a loan_id.
2.4. RESTful API Endpoints
POST /lend: Creates a new loan.
POST /payment: Records a payment for a loan.
GET /ledger/<int:loan_id>: Retrieves the full history and status of a specific loan.
GET /overview/<string:customer_id>: Lists all loans for a given customer.
2.5. Testing and API Usage Examples
The API can be tested using a command-line tool like curl or PowerShell's Invoke-WebRequest. The server must be running before sending requests.
Example 1: Create a Loan
Request:
Invoke-WebRequest -Uri http://127.0.0.1:5001/lend -Method POST -Body '{"customer_id": "cust123", "loan_amount": 10000, "loan_period": 2, "rate_of_interest": 8}' -ContentType 'application/json'


Expected Response:
{
  "loan_id": 1,
  "monthly_emi": 483.33,
  "total_amount": 11600.0
}


Example 2: Make a Payment
Request:
Invoke-WebRequest -Uri http://127.0.0.1:5001/payment -Method POST -Body '{"loan_id": 1, "amount": 5000}' -ContentType 'application/json'


Expected Response:
{
  "message": "Payment successful",
  "remaining_amount": 6600.0
}
