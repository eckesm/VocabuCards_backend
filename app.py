
from datetime import datetime
from flask import Flask, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message
from sqlalchemy.sql.elements import Null
from sqlalchemy.sql.expression import null
from stripe.api_resources import subscription
# from stripe.api_resources import price
from models import db, connect_db, Language, User, VocabWord, VocabWordComponent, Article
from starter_cards import create_all_language_starters
from forms import LoginForm, AddUserForm, VocabWordForm, VocabComponentForm, VocabWordAndComponentForm
from word import TranslationWord, DictionaryWord
import stripe_payments
from articles import getArticleFromRSS, RSS_NEWS_SOURCES
# import sys
import json
import os
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS, cross_origin
from secrets import token_urlsafe
import time


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

app.config['GOOGLE_LANGUAGE_KEY'] = os.environ.get(
    'GOOGLE_LANGUAGE_KEY')
app.config['WORDS_API_KEY'] = os.environ.get('WORDS_API_KEY')
app.config['STRIPE_SECRET'] = os.environ.get('STRIPE_SECRET')

# app.config['STRIPE_ENDPOINT_SIGNING_SECRET'] = os.environ.get(
#     'STRIPE_ENDPOINT_SIGNING_SECRET')
# app.config['STRIPE_DEFAULT_PRICE_ID'] = os.environ.get(
#     'STRIPE_DEFAULT_PRICE_ID')
# app.config['STRIPE_WEEKLY_PLAN_PRICE_ID'] = os.environ.get(
#     'STRIPE_WEEKLY_PLAN_PRICE_ID')
# app.config['STRIPE_MONTHLY_PLAN_PRICE_ID'] = os.environ.get(
#     'STRIPE_MONTHLY_PLAN_PRICE_ID')
# app.config['STRIPE_ANNUALLY_PLAN_PRICE_ID'] = os.environ.get(
#     'STRIPE_ANNUALLY_PLAN_PRICE_ID')
# app.config['STRIPE_TRIAL_SUBSCRIPTION_DAYS'] = os.environ.get(
#     'STRIPE_TRIAL_SUBSCRIPTION_DAYS')

app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS')

app.config['REACT_PRODUCTION_DOMAIN'] = os.environ.get(
    'REACT_PRODUCTION_DOMAIN')

react_app_url = app.config["REACT_PRODUCTION_DOMAIN"]
# STRIPE_TRIAL_PERIOD = app.config["STRIPE_TRIAL_SUBSCRIPTION_DAYS"]

cors = CORS(app)
mail = Mail(app)
jwt = JWTManager(app)
toolbar = DebugToolbarExtension(app)
connect_db(app)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FUNCTIONS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

#####################################################################
# ------------------------- JWT Tokens -----------------------------#
#####################################################################

# @app.after_request
# def refresh_expiring_jwts(response):
#     print('-----> @app.after_request')
#     try:
#         exp_timestamp = get_jwt()["exp"]
#         now = datetime.now(timezone.utc)
#         target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
#         if target_timestamp > exp_timestamp:
#             access_token = create_access_token(identity=get_jwt_identity())
#             set_access_cookies(response, access_token)
#         return response
#     except (RuntimeError, KeyError):
#         # Case where there is not a valid JWT. Just return the original respone
#         return response

# -------------------------------------------------------------------


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    # print('-----> @jwt.expired_token_loader')

    response = {
        'status': "expired_token",
        'message': "The provided access token is expired."
    }
    return jsonify(response), 401

# -------------------------------------------------------------------


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

# -------------------------------------------------------------------


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.get_by_id(identity)


#####################################################################
# ------------------ Confirming Email Address --------------------- #
#####################################################################

def send_confirm_email_link(email_address):
    user = User.get_by_email(email_address)

    if user == None:
        return {
            'email_address': email_address,
            'message': f"The email address {email_address} is not associated with an account.",
            'status': 'fail'
        }

    else:

        if user.email_confirm_token == None:
            token = token_urlsafe(16)
            user.email_confirm_token = token
            db.session.commit()

        else:
            token = user.email_confirm_token

        msg = Message('Please confirm your email address.',
                      sender='eckesm@gmail.com',
                      recipients=[email_address])
        msg.body = f"{user.name}, you are almost finsished setting up your VocabuCards account!  Please go to this link to confirm your email address: {react_app_url}/#/confirm-email/{token}"
        msg.html = f"{user.name}, you are <i>ALMOST</i> finished setting up your VocabuCards account!  Click <a href='{react_app_url}/#/confirm-email/{token}'>THIS LINK</a> to confirm your email address."
        mail.send(msg)

        return {
            'email_address': email_address,
            'message': 'Please check your email for a link to confirm your email address.',
            'status': 'success'
        }


#####################################################################
# ----------------------- Reset Password -------------------------- #
#####################################################################

def send_password_reset_link(email_address):
    user = User.get_by_email(email_address)

    if user == None:
        return {
            'status': 'error',
            'title': 'Error!',
            'message': f"The email address {email_address} is not associated with an account.",
            'email_address': email_address
        }

    else:

        if user.password_reset_token == None:
            token = token_urlsafe(16)
            user.password_reset_token = token
            db.session.commit()

        else:
            token = user.password_reset_token

        msg = Message('Reset your password.',
                      sender='eckesm@gmail.com',
                      recipients=[email_address])
        msg.body = f"Go to this link to reset your password: {react_app_url}/#/new-password/{token}"
        msg.html = f"Click <a href='{react_app_url}/#/new-password/{token}'>THIS LINK</a> to reset your password."
        mail.send(msg)

        return {
            'status': 'success',
            'title': 'Email Sent!',
            'message': 'Please check your email for a link to reset your password.',
            'email_address': email_address
        }


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> API ROUTES <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< #

#####################################################################
# ----------------------- JWT API Routes ---------------------------#
#####################################################################

@app.route('/refresh', methods=['GET'])
@cross_origin()
@jwt_required(refresh=True)
def refresh_access_token():

    refresh_user = get_jwt_identity()
    user = User.get_by_id(refresh_user)
    access_token = create_access_token(identity=user)

    response = {
        'status': 'success',
        'access_token': access_token,
        'message': "New access token created successfully."
    }
    return jsonify(response)

# -------------------------------------------------------------------


@app.route('/test', methods=['GET'])
@cross_origin()
@jwt_required()
def test_access_token():

    response = {
        'status': 'success'
    }
    return jsonify(response)


#####################################################################
# ---------------------- Stripe API Routes ------------------------ #
#####################################################################

# @app.route('/test-stripe', methods=['GET'])
# @cross_origin()
# def test_stripe():
#     test = stripe_payments.test_Stripe_PaymentIntent()
#     return jsonify(test)

# -------------------------------------------------------------------


# @app.route('/create-checkout-session', methods=['POST'])
# @cross_origin()
# @jwt_required()
# def create_checkout_session_route():

#     current_user = get_jwt_identity()
#     user = User.get_by_id(current_user)
#     price_id = request.json['price_id']
#     stripe_customer_id = request.json['stripe_customer_id']

#     session = stripe_payments.create_checkout_session(
#         price_id, user.id, stripe_customer_id, react_app_url)

#     return jsonify({'url': session.url})

# -------------------------------------------------------------------


# @app.route('/stripe-webhook', methods=['POST'])
# @cross_origin()
# def stripe_webhook_received():
#     payload = request.data
#     sig_header = request.headers['Stripe-Signature']

#     event = stripe_payments.create_event(payload, sig_header)
#     return event

# -------------------------------------------------------------------


# @app.route('/create-billing-portal-session', methods=['POST'])
# @cross_origin()
# @jwt_required()
# def create_billing_portal_session_route():

#     stripe_customer_id = request.json['stripe_customer_id']

#     session = stripe_payments.create_billing_portal_session(
#         stripe_customer_id, react_app_url)

#     return jsonify({'url': session.url})

# -------------------------------------------------------------------


# @app.route('/stripe-customer-id', methods=['GET'])
# @cross_origin()
# @jwt_required()
# def get_stripe_customer_id():

#     current_user = get_jwt_identity()
#     user = User.get_by_id(current_user)

#     response = {
#         'stripe_customer_id': user.stripe_customer_id
#     }

#     return jsonify(response)


#####################################################################
# ---------------------- User & Authentication -------------------- #
#####################################################################


# @app.route('/starters', methods=['GET'])
# @cross_origin()
# @jwt_required()
# def create_starter_words_via_API():

#     current_user = get_jwt_identity()
#     user = User.get_by_id(current_user)
#     response = create_all_starters(user.id)
#     return jsonify(response)

# -------------------------------------------------------------------

@app.route('/login', methods=['POST'])
@cross_origin()
def login_user_via_API():

    form = LoginForm()
    if form.validate_on_submit():

        email_address = request.json['email_address']
        password = request.json['password']
        user = User.authenticate(email_address, password)

        if user == None:
            response = {
                'status': 'error',
                'message': f'There is no user with the email address {email_address}.  Please make sure you are entering the correct email address with the correct spelling.'}
            return jsonify(response)

        if user == False:
            response = {
                'status': 'warning',
                'title': 'Incorrect Credentials!',
                'message': 'The email address and/or password were entered incorrectly.  Please try again.'}
            return jsonify(response)

        if user:
            access_token = create_access_token(identity=user)
            refresh_token = create_refresh_token(identity=user)
            user.update_last_login()
            if user.first_login == True:
                user.first_login = False
                db.session.add(user)
                db.session.commit()

            # # UPGRADING EARLIER ACCOUNT SETTINGS

            # if user.stripe_customer_id is None:
            #     new_customer = stripe_payments.create_customer_by_api(
            #         user.id, user.email_address, user.name)
            #     user.stripe_customer_id = new_customer.id
            #     db.session.add(user)
            #     db.session.commit()

            # if user.stripe_subscription_id is None:
            #     # Create Stripe trial subscription
            #     new_subscription = stripe_payments.create_trial_subscription_by_api(
            #         user.stripe_customer_id, STRIPE_TRIAL_PERIOD)
            #     user.stripe_subscription_id = new_subscription.id
            #     db.session.add(user)
            #     db.session.commit()

            response = {
                'status': 'success',
                'title': 'Successfully Logged In!',
                'message': f"Welcome back, {user.name}.",
                'access_token': access_token,
                'refresh_token': refresh_token,
            }
            return jsonify(response)

    else:

        response = {
            'status': 'validation_errors',
            'errors': form.errors
        }
        return jsonify(response)
# -------------------------------------------------------------------


@app.route('/logout', methods=['GET'])
@cross_origin()
@jwt_required()
def logout_user_via_API():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    if user == None:
        response = {
            'status': 'error',
            'title': 'Error!',
            'message': 'There is no user associated with the provided web token.'}
        return jsonify(response)

    if user:
        user.update_last_login()

        if user.first_login == True:
            user.first_login = False
            db.session.add(user)
            db.session.commit()

        response = {
            'status': 'success',
            'title': 'Successfully Logged Out!',
            'message': f"{user.email_address} has been logged out successfully.",
            'last_login': user.last_login}
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/register', methods=['POST'])
@cross_origin()
def register_user_via_API():

    form = AddUserForm()
    if form.validate():

        name = request.json['name']
        email_address = request.json['email_address']
        password = request.json['password']
        password_check = request.json['password_check']
        source_code = (request.json['source_code'] or 'sv')

        if password != password_check:

            response = {
                'status': 'warning',
                'title': 'Password Error!',
                'message': 'The entered passwords do not match.'}
            return jsonify(response)

        # current_time = datetime.now()

        new_user = User.register(
            name, email_address, password, source_code)

        if new_user:
            # Create Stripe customer ID
            # new_customer = stripe_payments.create_customer_by_api(
            #     new_user.id, email_address, name)
            # new_user.stripe_customer_id = new_customer.id

            # # Create Stripe trial subscription
            # new_subscription = stripe_payments.create_trial_subscription_by_api(
            #     new_customer.id, STRIPE_TRIAL_PERIOD)
            # new_user.stripe_subscription_id = new_subscription.id

            db.session.add(new_user)
            db.session.commit()

            # Send email address confirmation link
            confirmation_email = send_confirm_email_link(email_address)

            # Create first language starter words
            starter_words = create_all_language_starters(
                new_user.id, source_code)

            # create access token
            access_token = create_access_token(identity=new_user)
            refresh_token = create_refresh_token(identity=new_user)

            # return data
            response = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'confirmation_email': confirmation_email,
                'message': f"Welcome, {name}!  Credentials for {email_address} were created successfully.",
                'starter_words': starter_words,
                'status': 'success'
            }
            return jsonify(response)

    else:

        response = {
            'status': 'error',
            'message': 'Inputs did not validate.',
            'errors': form.errors
        }
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/confirm-email', methods=['POST'])
@cross_origin()
def confirm_email_address_via_API():
    token = request.json['token']
    password = request.json['password']

    user = User.get_by_email_confirm_token(token)

    if user == None:
        response = {
            'status': 'error',
            'title': 'Error!',
            'message': 'There is no user with a matching email confirmation token.'}
        return jsonify(response)

    else:

        authenticated_user = user.authenticate(user.email_address, password)

        if authenticated_user:

            authenticated_user.confirm_email_address()

            response = {
                'status': 'success',
                'title': 'Confirmed!',
                'message': f"Thank you for confirming your email address, {authenticated_user.name}!  You can now use this email address to reset your password."}
            return jsonify(response)

        else:
            response = {
                'status': 'warning',
                'title': 'Incorrect Password!',
                'message': f"The password entered is incorrect for the account associatied with the provided email confirmation token ({token}).  Please try again."}
            return jsonify(response)

# -------------------------------------------------------------------


@app.route('/send-confirm-email', methods=['POST'])
@cross_origin()
def send_confirm_email_via_API():
    email_address = request.json['email_address']
    response = send_confirm_email_link(email_address)
    return jsonify(response)

# -------------------------------------------------------------------


@app.route('/password-reset', methods=['POST'])
@cross_origin()
def password_reset_via_API():
    token = request.json['token']
    password = request.json['password']
    password_check = request.json['password_check']

    user = User.get_by_password_reset_token(token)

    if user == None:
        response = {
            'status': 'error',
            'title': 'Token Error!',
            'message': 'There is no user with a matching password reset token.'}
        return jsonify(response)

    else:

        if password != password_check:
            response = {
                'status': 'warning',
                'title': 'Password Error!',
                'message': 'The entered passwords do not match.'}
            return jsonify(response)

        else:

            user.change_password(password)
            user.confirm_email_address()

            response = {
                'status': 'success',
                'title': 'Success!',
                'message': "Your password has been updated successfully!"}
            return jsonify(response)

# -------------------------------------------------------------------


@app.route('/send-password-reset', methods=['POST'])
@cross_origin()
def send_password_reset_via_API():
    email_address = request.json['email_address']
    response = send_password_reset_link(email_address)
    return jsonify(response)


#####################################################################
# -------------------- Load User Settings & Data ------------------ #
#####################################################################

@app.route('/start', methods=['GET'])
@cross_origin()
@jwt_required()
def get_user_start_information():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    languages = Language.get_all_options()
    last_language = user.last_language
    words = db.session.query(VocabWord).filter(
        VocabWord.owner_id == user.id, VocabWord.source_code == last_language).order_by(VocabWord.root).all()

    # current_time = datetime.now()
    # unix_timestamp = current_time.timestamp()

    # subscription_status = subscription.status
    # payment_method = subscription.default_payment_method
    # cancel_at_period_end = subscription.cancel_at_period_end
    # canceled_at = subscription.canceled_at
    # period_start = subscription.current_period_start
    # period_end = subscription.current_period_end
    # trial_start = subscription.trial_start
    # trial_end = subscription.trial_end
    # price_id = subscription.plan.id
    # product_id = subscription.plan.product
    # current_plan = stripe_payments.get_plan_name(price_id)


    # user.update_retrieved_stripe_subscription_information(
    #     subscription_status, payment_method, period_start, period_end, trial_start, trial_end, price_id, product_id, current_plan)

    # if (subscription_status != 'active' and subscription_status != 'trialing') and user.account_override is None:

    #     response = {
    #         'account_override': user.account_override,
    #         'current_plan': user.current_plan,
    #         'first_login': user.first_login,
    #         'is_email_confirmed': user.is_email_confirmed,
    #         'languages': languages,
    #         'last_login': user.last_login,
    #         'last_source_code': last_language,
    #         'name': user.name,
    #         'stripe_cancel_at_period_end': cancel_at_period_end,
    #         'stripe_canceled_at': canceled_at,
    #         'stripe_customer_id': user.stripe_customer_id,
    #         'stripe_payment_method': payment_method,
    #         'stripe_period_end': period_end,
    #         'stripe_period_start': period_start,
    #         'subscription_status': subscription_status,
    #         'trial_end': trial_end,
    #         'trial_start': trial_start,
    #         'user': user.email_address,
    #     }

    # else:

    response = {
        'account_override': user.account_override,
        # 'current_plan': user.current_plan,
        'current_article': user.current_article,
        'current_text': user.current_text,
        'first_login': user.first_login,
        'is_email_confirmed': user.is_email_confirmed,
        'languages': languages,
        'last_login': user.last_login,
        'last_source_code': last_language,
        'name': user.name,
        'news_sources': RSS_NEWS_SOURCES,
        # 'stripe_cancel_at_period_end': cancel_at_period_end,
        # 'stripe_canceled_at': canceled_at,
        # 'stripe_customer_id': user.stripe_customer_id,
        # 'stripe_payment_method': payment_method,
        # 'stripe_period_end': period_end,
        # 'stripe_period_start': period_start,
        # 'subscription_status': subscription_status,
        # 'trial_end': trial_end,
        # 'trial_start': trial_start,
        'user': user.email_address,
        'words_array': [word.serialize_and_components() for word in words]
    }

    return jsonify(response)

# -------------------------------------------------------------------


@app.route('/variations/<component_id>', methods=['GET'])
@jwt_required()
def get_variation_data_by_api(component_id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    component = VocabWordComponent.get_by_id(component_id)

    if component.owner_id == user.id:
        return jsonify(component.serialize())

# -------------------------------------------------------------------


@app.route('/words/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_users_language_words(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    words = db.session.query(VocabWord).filter(
        VocabWord.owner_id == user.id, VocabWord.source_code == source_code).order_by(VocabWord.root).all()

    return jsonify([word.serialize_and_components() for word in words])

# -------------------------------------------------------------------


@app.route('/renderedtext', methods=['PUT'])
@cross_origin()
@jwt_required()
def save_input_text_by_api():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    text = request.json['text']
    article_id = request.json['articleId']
    user.current_text = text
    user.current_article = article_id
    db.session.add(user)
    db.session.commit()

    response = {
        'text': user.current_text,
        'article_id': user.current_article,
        'status': 'success'
    }
    return jsonify(response)


#####################################################################
# -------------------------- Languages ---------------------------- #
#####################################################################

@app.route('/languages', methods=['GET'])
@cross_origin()
def get_all_languages():

    languages = Language.get_all_options()

    return jsonify({'languages': languages, 'news_sources': RSS_NEWS_SOURCES})

# -------------------------------------------------------------------


@app.route('/last/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def update_users_last_language(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    accessed_languages = json.loads(user.accessed_languages)

    if user.last_language != source_code:
        user.current_text = None
        db.session.add(user)
        db.session.commit()

    if source_code not in accessed_languages:
        accessed_languages.append(source_code)
        user.accessed_languages = json.dumps(accessed_languages)
        db.session.commit()
        create_all_language_starters(
            user.id, source_code)

    user.last_language = source_code
    user.current_article = ''
    db.session.add(user)
    db.session.commit()

    return jsonify(user.last_language)


#####################################################################
# ------------------- Translate & Dictionary ---------------------- #
#####################################################################

@app.route('/translate/<word>/<source_code>/<translate_code>', methods=['GET'])
@cross_origin()
# @jwt_required()
def translate(word, source_code, translate_code):

    if len(word) > 150:

        return(jsonify('ERROR: text cannot exceed 150 characters.'))

    word = TranslationWord(word, source_code, translate_code)
    translation = word.translated_word
    return jsonify(translation)

# -------------------------------------------------------------------


@app.route('/dictionary/<word>', methods=['GET'])
# @jwt_required()
def search_dictionary(word):

    word = DictionaryWord(word)
    data = json.loads(word.definitions)
    return jsonify(data)


#####################################################################
# --------------------------- Word CRUD --------------------------- #
#####################################################################

@app.route('/words/new', methods=['POST'])
@cross_origin()
@jwt_required()
def add_new_word_by_api():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    form = VocabWordAndComponentForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate():

        user_id = user.id
        source_code = request.json['source_code']
        word = request.json['word']
        translation = request.json['translation']
        notes = request.json['notes']

        new_word = VocabWord.add_vocab_word(
            user_id, source_code, word, translation, notes)

        # print(f"ROOT_ID: {new_word.id}", file=sys.stderr)

        response = {
            'word': new_word.serialize(),
            'status': 'success'
        }
        return jsonify(response)

    else:
        response = {
            'errors': form.errors,
            'status': 'errors'
        }
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/words/<id>', methods=['PUT'])
@cross_origin()
@jwt_required()
def edit_word_by_api(id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    form = VocabWordForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate():

        user_id = user.id
        source_code = request.json['source_code']
        word = request.json['word']
        translation = request.json['translation']
        notes = request.json['notes']

        edit_word = VocabWord.get_by_id(id)

        if edit_word.owner_id != user_id:
            response = {
                'restriction': 'User is not authorized to edit this word.',
                'status': 'restricted'
            }
            return jsonify(response)

        edit_word.update(
            source_code, word, translation, notes)

        response = {
            'word': edit_word.serialize_and_components(),
            'status': 'success'
        }
        return jsonify(response)

    else:
        response = {
            'errors': form.errors,
            'status': 'errors'
        }
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/words/<id>', methods=['DELETE'])
@cross_origin()
@jwt_required()
def delete_word_by_api(id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    user_id = user.id

    delete_word = VocabWord.get_by_id(id)

    if delete_word.owner_id != user_id:
        response = {
            'restriction': 'User is not authorized to delete this word.',
            'status': 'restricted'
        }
        return jsonify(response)

    db.session.delete(delete_word)
    db.session.commit()

    response = {
        'word': id,
        'status': 'deleted'
    }
    return jsonify(response)

#####################################################################
# ------------------------- Variation CRUD ------------------------ #
#####################################################################


@app.route('/variations/new', methods=['POST'])
@jwt_required()
def add_new_variation_by_api():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    form = VocabWordAndComponentForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate():

        root_id = request.json['root_id']
        user_id = user.id
        part_of_speech = request.json['part_of_speech']
        word = request.json['word']
        translation = request.json['translation']
        description = request.json['description']
        definition = request.json['definition']
        synonyms = request.json['synonyms']
        examples = request.json['examples']
        examples_translation = request.json['examples_translation']
        notes = request.json['notes']

        new_component = VocabWordComponent.add_variation(
            root_id, user_id, part_of_speech, word, translation, description, definition, synonyms, examples, examples_translation, notes)

        response = {
            'component': new_component.serialize(),
            'status': 'success'
        }
        return jsonify(response)

    else:
        response = {
            'errors': form.errors,
            'status': 'errors'
        }
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/variations/<id>', methods=['PUT'])
@jwt_required()
def edit_variation_by_api(id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    form = VocabComponentForm()
    if form.validate():

        user_id = user.id
        part_of_speech = request.json['part_of_speech']
        word = request.json['word']
        translation = request.json['translation']
        description = request.json['description']
        definition = request.json['definition']
        synonyms = request.json['synonyms']
        examples = request.json['examples']
        examples_translation = request.json['examples_translation']
        notes = request.json['notes']

        edit_component = VocabWordComponent.get_by_id(id)

        if edit_component.owner_id != user_id:
            response = {
                'restriction': 'User is not authorized to edit this component.',
                'status': 'restricted'
            }
            return jsonify(response)

        edit_component.update(
            part_of_speech, word, translation, description, definition, synonyms, examples, examples_translation, notes)

        response = {
            'component': edit_component.serialize(),
            'status': 'success'
        }
        return jsonify(response)

    else:
        response = {
            'errors': form.errors,
            'status': 'errors'
        }
        return jsonify(response)

# -------------------------------------------------------------------


@app.route('/variations/<id>', methods=['DELETE'])
@jwt_required()
def delete_variation_by_api(id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    user_id = user.id

    delete_component = VocabWordComponent.get_by_id(id)

    if delete_component.owner_id != user_id:
        response = {
            'restriction': 'User is not authorized to delete this component.',
            'status': 'restricted'
        }
        return jsonify(response)

    db.session.delete(delete_component)
    db.session.commit()

    response = {
        'component': id,
        'status': 'deleted'
    }
    return jsonify(response)


#####################################################################
# ------------------------- News Article -------------------------- #
#####################################################################


@app.route('/news/<source_code>', methods=['GET'])
@cross_origin()
def getArticleUnprotected(source_code):
    article = getArticleFromRSS(source_code)
    return(jsonify(article))

# -------------------------------------------------------------------


@app.route('/articles/new/<source_code>', methods=['GET'])
@cross_origin()
# @jwt_required()
def get_news_article(source_code):
    article = getArticleFromRSS(source_code)
    return(jsonify(article))

# -------------------------------------------------------------------


@app.route('/articles/saved/random/<source_code>', methods=['GET'])
@cross_origin()
def get_random_saved_news_article(source_code):
    article = Article.get_random_by_language(source_code).serialize()
    return(jsonify(article))
# -------------------------------------------------------------------


@app.route('/articles/saved/id/<id>', methods=['GET'])
@cross_origin()
def get_saved_news_article_by_id(id):
    article = Article.get_by_id(id).serialize()
    return(jsonify(article))


# -------------------------------------------------------------------


@app.route('/articles/saved/all/<source_code>', methods=['GET'])
@cross_origin()
def get_all_saved_news_article(source_code):
    article = Article.get_all_by_language(source_code)
    return(jsonify(article))
