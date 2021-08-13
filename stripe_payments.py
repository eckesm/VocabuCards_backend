import stripe
import os
import json
from flask import jsonify
from stripe.api_resources import subscription
from models import User
from datetime import datetime, timedelta, timezone


stripe.api_key = API_KEY = os.environ.get('STRIPE_SECRET')
STRIPE_ENDPOINT_SIGNING_SECRET = os.environ.get(
    'STRIPE_ENDPOINT_SIGNING_SECRET')
STRIPE_DEFAULT_PRICE_ID = os.environ.get('STRIPE_DEFAULT_PRICE_ID')
STRIPE_WEEKLY_PLAN_PRICE_ID = os.environ.get('STRIPE_WEEKLY_PLAN_PRICE_ID')
STRIPE_MONTHLY_PLAN_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PLAN_PRICE_ID')
STRIPE_ANNUALLY_PLAN_PRICE_ID = os.environ.get('STRIPE_ANNUALLY_PLAN_PRICE_ID')


# def test_Stripe_PaymentIntent():
#     return stripe.PaymentIntent.create(
#         amount=1000,
#         currency='usd',
#         payment_method_types=['card'],
#         receipt_email='jenny.rosen@example.com',
#     )


def create_checkout_session(price_id, user_id, stripe_customer_id, react_app_url):
    session = stripe.checkout.Session.create(
        # success_url='https://example.com/success.html?session_id={CHECKOUT_SESSION_ID}',
        success_url=f"{react_app_url}/#/plans/success",

        # cancel_url='https://example.com/canceled.html',
        cancel_url=f"{react_app_url}/#/plans",

        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': price_id,
            # For metered billing, do not pass quantity
            'quantity': 1
        }],
        metadata={
            'user_id': user_id
        },
        customer=stripe_customer_id
    )
    return session


def create_billing_portal_session(stripe_customer_id, react_app_url):

    # This is the URL to which the customer will be redirected after they are
    # done managing their billing with the portal.

    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{react_app_url}/#/plans/updated",
    )
    return session

    # redirect to the URL for the session
    #   return redirect(session.url, code=303)


def create_customer_by_api(user_id, email_address, name):
    return stripe.Customer.create(
        email=email_address,
        name=name,
        description=f'VocabuCards ID: {user_id}'
    )


def create_trial_subscription_by_api(customer_id, trial_period_days):
    return stripe.Subscription.create(
        customer=customer_id,
        items=[
            {
                'price': STRIPE_DEFAULT_PRICE_ID
            }
        ],
        trial_period_days=trial_period_days
    )


def create_event(payload, sig_header):
    # https://stripe.com/docs/webhooks/build
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_ENDPOINT_SIGNING_SECRET)
        # event = json.loads(payload)

    except:
        print('Webhook Error')
        return jsonify(success=False)

    # Handle the event
    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"Payment Intent for {payment_intent['customer']} succeeded")
        handle_payment_intent_succeeded(payment_intent)

    elif event and event['type'] == 'setup_intent.succeeded':
        setup_intent = event['data']['object']
        print(f"Setup Payment Intent for {setup_intent['customer']} succeeded")
        handle_setup_intent_succeeded(setup_intent)

    elif event and event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        print(f"Invoice Paid for {invoice['customer']} succeeded")
        handle_invoice_paid(invoice)

    elif event and event['type'] == 'payment_method.attached':
        payment_method = event['data']['object']
        print(
            f"Payment Method Attached for {payment_method['customer']} succeeded")
        handle_payment_method_attached(payment_method)

    elif event and event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        print(f"Subscription updated for {subscription['customer']} succeeded")
        handle_customer_subscription_updated(subscription)

    elif event and event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        print(f"Subscription created for {subscription['customer']} succeeded")
        # handle_customer_subscription_created(subscription)

    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)


def handle_payment_intent_succeeded(payment_intent):
    user = User.get_by_stripe_customer_id(payment_intent['customer'])
    # user.set_stripe_payment_method("setup_intent")
    user.set_subscription_status("setup_intent")


def handle_setup_intent_succeeded(setup_intent):
    user = User.get_by_stripe_customer_id(setup_intent['customer'])
    # user.set_stripe_payment_method("payment_intent")
    user.set_subscription_status("payment_intent")


def handle_payment_method_attached(payment_method):
    user = User.get_by_stripe_customer_id(payment_method['customer'])
    user.set_stripe_payment_method("payment_method_attached")


def handle_customer_subscription_updated(subscription):
    customer_id = subscription['customer']

    place = len(subscription['items']['data'])-1

    # subscription_id = subscription['items']['data'][place]['subscription']
    subscription_id = subscription['id']
    price_id = subscription['items']['data'][place]['price']['id']
    product_id = subscription['items']['data'][place]['price']['product']
    period_start = subscription['current_period_start']
    period_end = subscription['current_period_end']
    cancel_at_period_end = subscription['cancel_at_period_end']
    default_payment_method = subscription['default_payment_method']

    user = User.get_by_stripe_customer_id(customer_id)
    user.update_stripe_subscription(
        subscription_id, price_id, product_id, period_start, period_end, get_plan_name(price_id))
    if cancel_at_period_end:
        user.set_subscription_status("expiring")
    else:
        user.set_subscription_status("renewing")
        if default_payment_method is None:
            user.set_stripe_payment_method(None)


# def handle_customer_subscription_created(subscription):
#     customer_id = subscription['customer']

#     place = len(subscription['items']['data'])-1

#     subscription_id = subscription['id']
#     price_id = subscription['items']['data'][place]['price']['id']
#     product_id = subscription['items']['data'][place]['price']['product']
#     period_start = subscription['current_period_start']
#     period_end = subscription['current_period_end']
#     cancel_at_period_end = subscription['cancel_at_period_end']
#     user = User.get_by_stripe_customer_id(customer_id)
#     print(period_end)
#     user.update_stripe_subscription(
#         subscription_id, price_id, product_id, period_start, period_end, get_plan_name(price_id))
#     if cancel_at_period_end:
#         user.set_subscription_status("expiring")
#     else:
#         user.set_subscription_status("renewing")


def handle_invoice_paid(invoice):
    customer_id = invoice['customer']
    subscription_id = invoice['subscription']

    place = len(invoice['lines']['data'])-1

    price_id = invoice['lines']['data'][place]['price']['id']
    product_id = invoice['lines']['data'][place]['price']['product']
    period_start = invoice['lines']['data'][place]['period']['start']
    period_end = invoice['lines']['data'][place]['period']['end']
    amount_paid = invoice['amount_paid']
    user = User.get_by_stripe_customer_id(customer_id)
    user.update_stripe_subscription(
        subscription_id, price_id, product_id, period_start, period_end, get_plan_name(price_id))
    if amount_paid != 0:
        user.set_stripe_payment_method("paid")


def get_plan_name(price_id):
    plan_name = None
    if price_id == STRIPE_WEEKLY_PLAN_PRICE_ID:
        plan_name = 'weekly'
    if price_id == STRIPE_MONTHLY_PLAN_PRICE_ID:
        plan_name = 'monthly'
    if price_id == STRIPE_ANNUALLY_PLAN_PRICE_ID:
        plan_name = 'annually'
    return plan_name
