from flask import Flask, request, jsonify
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

from config import DB_URL, STRIPE_API_KEY, STRIPE_ENDPOINT_SECRET, COINBASE_API_KEY, COINBASE_ENDPOINT_SECRET

import stripe

from coinbase_commerce.webhook import Webhook
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload

stripe.api_key=STRIPE_API_KEY

app = Flask(__name__)
app.secret_key="sdklwadlkmdkl"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    
    _id = db.Column("id", db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    payment_method = db.Column(db.Enum('stripe', 'coinbase', name="payment_method"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow().replace(microsecond=0), nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    generated_invite_link = db.Column(db.Boolean, default=False)


    def __init__(self, telegram_id, payment_method, valid_until):
        self.telegram_id = telegram_id
        self.payment_method = payment_method
        self.valid_until = valid_until

    def __repr__(self):
       return '<User %r>' % self.telegram_id



@app.route('/')
def index():
    return "Hello World"

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():

    # ? stripe stuff
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)

    if STRIPE_ENDPOINT_SECRET:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_ENDPOINT_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)
    
    if event and event['type'] == 'invoice.payment_succeeded':
        invoice_payment = event['data']['object']

        # ! get variables from invoice_payment
        telegram_id = int(invoice_payment['subscription_details']['metadata']['telegram_id'])
        subscription_duration = int(invoice_payment['subscription_details']['metadata']['duration'])
        subscription_id = str(invoice_payment['subscription'])
        user_email = invoice_payment['customer_email']
        payment_method = "stripe"
        valid_until = (datetime.utcnow() + timedelta(days=subscription_duration)).replace(microsecond=0)
        
        
        print (f"🔔  New payment from {user_email} for {str(subscription_duration)} months" + str(telegram_id) + subscription_id)
        
        found_user = Users.query.filter_by(telegram_id=telegram_id).first()
        if found_user:
            print("User already exists, updating his valid_until date" + str(found_user.telegram_id))
            # modify his valid_until date
            found_user.valid_until = valid_until
            db.session.commit()
            
        else:
            print("Creating new user" + str(telegram_id))
            usr = Users(telegram_id, payment_method, valid_until)
            db.session.add(usr)
            db.session.commit()
    
    return jsonify(success=True)


@app.route('/coinbase/webhook', methods=['POST'])
def coinbase_webhook():

    # coinbase stuff
    request_data = request.data.decode('utf-8')
    # webhook signature verification
    request_sig = request.headers.get('X-CC-Webhook-Signature', None)

    try:
        # signature verification and event object construction
        event = Webhook.construct_event(request_data, request_sig, COINBASE_ENDPOINT_SECRET)
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return str(e), 400

    print("Received event: id={id}, type={type}".format(id=event.id, type=event.type))
    # print(event["data"]["description"])

    if event.type == 'charge:confirmed':
        print(event["data"])
        telegram_id = event["data"]["description"]
        print(telegram_id, "telegram_id just bought a sub")
    
    return jsonify(success=True)


if __name__ == '__main__':
   with app.app_context():
       db.create_all()
   app.run(debug=True)