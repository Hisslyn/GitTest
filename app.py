import os
from dotenv import load_dotenv
from typing import Dict
from flask import Flask, request, jsonify, render_template
import paypalrestsdk
from flask import redirect
import requests

load_dotenv()  # This loads the variables from .env

# Retrieve PayPal client ID and secret from environment variables
client_id = os.environ.get('PAYPAL_CLIENT_ID')
client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')

# Print client ID and secret for verification (not recommended for production)
print(client_id)
print(client_secret)
app = Flask(__name__)   # Initialize Flask app


# Route for the home page, displaying a basic HTML with a payment button
@app.route('/')
def home():
    return render_template('home_page.html')


# Configuration for PayPal SDK
paypalrestsdk.configure({
    'mode': 'sandbox',  # or 'live' for production
    'client_id': os.environ.get('PAYPAL_CLIENT_ID'),
    'client_secret': os.environ.get('PAYPAL_CLIENT_SECRET')
})


# Route for creating a payment
@app.route('/create-payment', methods=['GET', 'POST'])
def create_payment():
    # Handling POST request for payment creation
    if request.method == 'POST':
        total = request.form['total']
        currency = request.form['currency']
        description = request.form['description']

        # Create payment object
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": total, "currency": currency, },
                "description": description,
            }],
            "redirect_urls": {
                "return_url": "http://localhost:5000/payment/execute",
                "cancel_url": "http://localhost:5000/payment/cancel"
            }
        })
        if payment.create():
            print("Payment created successfully")
            for link in payment.links:
                if link.rel == "approval_url":
                    # Capture approval_url to redirect user
                    approval_url = str(link.href)
                    return redirect(approval_url)
            return 'No approval URL found', 400
        else:
            print(payment.error)
            return jsonify({'error': 'Error in creating payment'}), 500
    # Display payment creation form for GET request
    else:
        return render_template('create_payment_form.html')


# Placeholder for data processing function
def process_data(data: Dict) -> None:
    # Your processing logic
    pass


# Route for executing a payment
@app.route('/payment/execute', methods=['GET'])
def execute_payment():
    print("Execute payment endpoint hit.")
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    print(f"Payment ID: {payment_id}, Payer ID: {payer_id}")
    if payment_id and payer_id:
        # Function to execute the payment
        execute_response = execute_payment_function(payment_id, payer_id)  # Replace with your actual function call
        if execute_response:  # Check if the payment execution was successful
            return render_template('payment_success.html')
        else:
            return render_template('payment_failure.html')
    else:
        return render_template('payment_error.html')


# Function to execute the payment using PayPal API
def execute_payment_function(payment_id, payer_id):
    try:
        # PayPal execute payment URL
        execute_url = f'https://api.sandbox.paypal.com/v1/payments/payment/{payment_id}/execute'
        # Data containing the payer ID
        data = {'payer_id': payer_id}
        # Your PayPal credentials
        auth = (client_id, client_secret)  # You must replace these with your actual PayPal sandbox credentials
        # Headers with the content type
        headers = {'Content-Type': 'application/json'}
        # Make the POST request to PayPal to execute the payment
        response = requests.post(execute_url, json=data, headers=headers, auth=auth)
        # Check if the payment execution was successful
        if response.ok:
            return response.json()  # Return the response as JSON
        else:
            # Log the response from PayPal in case of error
            print(f"Failed to execute payment. Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None


# Run the Flask application on port 5000
if __name__ == '__main__':
    app.run(port=5000)
