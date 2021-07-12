
from flask import Flask, render_template, redirect, session, flash, g, request, jsonify, url_for, make_response
# from functools import wraps
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message
from models import db, connect_db, Language, User, VocabWord, VocabWordComponent
from forms import LoginForm, AddUserForm, VocabWordForm, VocabComponentForm, VocabWordAndComponentForm
from word import TranslationWord, DictionaryWord
from articles import getArticleFromRSS, RSS_NEWS_SOURCES
# import requests
import sys
import json
import os
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required, JWTManager, set_access_cookies, unset_jwt_cookies
from flask_cors import CORS, cross_origin
from secrets import token_urlsafe
from datetime import datetime, timedelta, timezone


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# app.config["JWT_COOKIE_SECURE"] = False
# app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

app.config['GOOGLE_LANGUAGE_KEY'] = os.environ.get(
    'GOOGLE_LANGUAGE_KEY')
app.config['WORDS_API_KEY'] = os.environ.get('WORDS_API_KEY')

app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS')

app.config['REACT_PRODUCTION_DOMAIN'] = os.environ.get(
    'REACT_PRODUCTION_DOMAIN')

react_app_url = app.config["REACT_PRODUCTION_DOMAIN"]

cors = CORS(app)
mail = Mail(app)
jwt = JWTManager(app)
toolbar = DebugToolbarExtension(app)
connect_db(app)


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
    print('-----> @jwt.expired_token_loader')

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
            'status': 'fail',
            'message': f"The email address {email_address} is not associated with an account.",
            'email_address': email_address
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
        msg.body = f"Go to this link to confirm your email address: {react_app_url}/#/confirm-email/{token}"
        msg.html = f"<b>Almost done!</b>  Click <a href='{react_app_url}/#/confirm-email/{token}'>THIS LINK</a> to confirm your email address."
        mail.send(msg)
        # flash('Please check your email for a link to confirm your email address.', 'info')

        return {
            'status': 'success',
            'message': 'Please check your email for a link to confirm your email address.',
            'email_address': email_address
        }


#####################################################################
# ----------------------- Reset Password -------------------------- #
#####################################################################

def send_password_reset_link(email_address):
    user = User.get_by_email(email_address)

    if user == None:
        return {
            'status': 'fail',
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

        msg = Message('Please reset your password.',
                      sender='eckesm@gmail.com',
                      recipients=[email_address])
        msg.body = f"Go to this link to confirm your email address: {react_app_url}/#/new-password/{token}"
        msg.html = f"<b>Almost done!</b>  Click <a href='{react_app_url}/#/new-password/{token}'>THIS LINK</a> to reset your password."
        mail.send(msg)

        return {
            'status': 'success',
            'message': 'Please check your email for a link to reset your password.',
            'email_address': email_address
        }


#####################################################################
# -------------------- Create Starter Words ----------------------- #
#####################################################################

STARTER_WORDS = {
    'sv': [
        {
            'root': 'hund',
            'translation': 'dog',
            'notes': 'mannens bästa vän.',
            'variations': [
                {
                    'part_of_speech': 'noun',
                    'variation': 'en hund',
                    'translation': 'a dog',
                    'description': 'singular, indefinite',
                    'definition': 'a domestic mammal that is related to the wolves and foxes.',
                    'synonyms': 'canine, doggy (or doggie), hound, pooch, tyke (also tike)',
                    'examples': 'a dog who needs a loving home',
                    'notes': 'en noun'
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'hunden',
                    'translation': 'the dog',
                    'description': 'singular, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': '',
                    'notes': 'en noun'
                }
            ]
        }
    ]
}


def create_starter_word(owner_id, source_code, root, translation, notes):
    new_vocab_word = VocabWord.add_vocab_word(
        owner_id, source_code, root, translation, notes)
    return new_vocab_word


def create_starter_component(root_id, owner_id, part_of_speech, variation, translation, description, definition, synonyms, examples, notes):
    new_variation = VocabWordComponent.add_variation(
        root_id, owner_id, part_of_speech, variation, translation, description, definition, synonyms, examples, notes)
    return new_variation


def create_all_starters(owner_id):
    for source_code, words in STARTER_WORDS.items():
        for word in words:
            new_word = create_starter_word(
                owner_id, source_code, word['root'], word['translation'], word['notes'])
            for variation in word['variations']:
                create_starter_component(new_word.id, owner_id, variation['part_of_speech'], variation['variation'], variation['translation'],
                                         variation['description'], variation['definition'], variation['synonyms'], variation['examples'], variation['notes'])
    return {
        'status': 'success',
        'message': 'Successfully created starter vocabulary words.'
    }


#####################################################################
# ------------------------- API Routes -----------------------------#
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

@app.route('/refresh', methods=['GET'])
@cross_origin()
@jwt_required(refresh=True)
def refresh_access_token():

    refresh_user = get_jwt_identity()
    user = User.get_by_id(refresh_user)
    access_token = create_access_token(identity=user)

    now = datetime.now(timezone.utc)
    response = {
        'status': 'success',
        'access_token': access_token,
        'access_token_exp': datetime.timestamp(now+timedelta(hours=1)),
        'message': "New access token created successfully."
    }
    return jsonify(response)

# -------------------------------------------------------------------


# @app.route('/test-access-token', methods=['GET'])
# @cross_origin()
# @jwt_required
# def refresh_access_token():

#     response = {
#         'status': 'success', }
#     return jsonify(response)

# -------------------------------------------------------------------


# @app.route('/news/<source_code>', methods=['GET'])
# @cross_origin()
# def getArticleUnprotected(source_code):
#     article = getArticleFromRSS(source_code)
#     return(jsonify(article))


@app.route('/get-news-article/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def getArticle(source_code):
    article = getArticleFromRSS(source_code)
    return(jsonify(article))


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
                'status': 'no_user',
                'message': f'There is no user with the email address {email_address}.  Please make sure you are entering the correct email address with the correct spelling.'}
            return jsonify(response)

        if user == False:
            response = {
                'status': 'fail',
                'message': 'Credentials entered were incorrect.  Please try again.'}
            return jsonify(response)

        if user:
            access_token = create_access_token(identity=user)
            refresh_token = create_refresh_token(identity=user)
            user.update_last_login()
            if user.first_login == True:
                user.update_first_login()

            now = datetime.now(timezone.utc)

            response = {
                'status': 'success',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'access_token_exp': datetime.timestamp(now+timedelta(hours=1)),
                'refresh_token_exp': datetime.timestamp(now+timedelta(days=30)),
                'message': f"Credentials for {email_address} were authenticated."
                # 'last_login': user.last_login
            }
            return jsonify(response)

    else:

        response = {
            'status': 'error',
            'message': 'Inputs did not validate!',
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
            'message': 'There is no user associated with the provided web token.'}
        return jsonify(response)

    if user:
        user.update_last_login()

        if user.first_login == True:
            user.update_first_login()

        response = {
            'status': 'success',
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
        source_code = request.json['source_code']

        if password != password_check:

            response = {
                'status': 'fail',
                'message': 'Passwords do not match.'}
            return jsonify(response)

        new_user = User.register(name, email_address, password, source_code)

        if new_user:
            send_confirm_email_link(email_address)
            create_all_starters(new_user.id)
            access_token = create_access_token(identity=new_user)
            response = {
                'status': 'success',
                'access_token': access_token,
                'message': f"Welcome, {name}!  Credentials for {email_address} were created successfully."}
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
            'status': 'fail',
            'message': 'There is no user with a matching email confirmation token.'}
        return jsonify(response)

    else:

        authenticated_user = user.authenticate(user.email_address, password)

        if authenticated_user:

            authenticated_user.confirm_email_address()

            response = {
                'status': 'success',
                'message': f"Thank you for confirming your email address, {authenticated_user.name}!  You can now use this email address to reset your password."}
            return jsonify(response)

        else:
            response = {
                'status': 'fail',
                'message': f"The password entered is incorrect for the account associatied the email confirmation token {token}."}
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
            'message': 'There is no user with a matching password reset token.'}
        return jsonify(response)

    else:

        if password != password_check:
            response = {
                'status': 'fail',
                'message': 'The passwords do not match.'}
            return jsonify(response)

        else:

            user.change_password(password)
            user.confirm_email_address()

            response = {
                'status': 'success',
                'message': "Your password has been updated successfully!"}
            return jsonify(response)


# -------------------------------------------------------------------


@app.route('/send-password-reset', methods=['POST'])
@cross_origin()
def send_password_reset_via_API():
    email_address = request.json['email_address']
    response = send_password_reset_link(email_address)
    return jsonify(response)

# -------------------------------------------------------------------


@app.route('/translate/<word>/<source_code>/<translate_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def translate(word, source_code, translate_code):

    word = TranslationWord(word, source_code, translate_code)
    translation = word.translated_word

    return jsonify(translation)


# -------------------------------------------------------------------

@app.route('/dictionary/<word>', methods=['GET'])
@jwt_required()
def search_dictionary(word):

    word = DictionaryWord(word)
    data = json.loads(word.definitions)
    return jsonify(data)

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

    response = {
        'current_text': user.current_text,
        'first_login': user.first_login,
        'is_email_confirmed': user.is_email_confirmed,
        'languages': languages,
        'last_login': user.last_login,
        'last_source_code': last_language,
        'name': user.name,
        'news_sources': RSS_NEWS_SOURCES,
        'user': user.email_address,
        'words_array': [word.serialize_and_components() for word in words]
    }

    return jsonify(response)

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


@app.route('/last/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def update_users_last_language(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    if user.last_language != source_code:
        user.update_current_text(None)

    user.update_last_language(source_code)

    return jsonify(user.last_language)

# -------------------------------------------------------------------


# @app.route('/last', methods=['GET'])
# @cross_origin()
# @jwt_required()
# def get_users_last_language():

#     current_user = get_jwt_identity()
#     user = User.get_by_id(current_user)

#     return jsonify(user.last_language)

# -------------------------------------------------------------------


@app.route('/languages', methods=['GET'])
@cross_origin()
# @jwt_required()
def get_all_languages():

    languages = Language.get_all_options()

    return jsonify(languages)

    # -------------------------------------------------------------------


@app.route('/renderedtext', methods=['PUT'])
@cross_origin()
@jwt_required()
def save_input_text_by_api():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    # user_id = user.id
    # source_code = request.json['source_code']
    text = request.json['text']

    current_text = user.update_current_text(text)

    response = {
        'text': current_text,
        'status': 'success'
    }
    return jsonify(response)

# -------------------------------------------------------------------


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

        print(f"ROOT_ID: {new_word.id}", file=sys.stderr)

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

# -------------------------------------------------------------------


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
        notes = request.json['notes']

        new_component = VocabWordComponent.add_variation(
            root_id, user_id, part_of_speech, word, translation, description, definition, synonyms, examples, notes)

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

        # id = request.json['id']
        user_id = user.id
        part_of_speech = request.json['part_of_speech']
        word = request.json['word']
        translation = request.json['translation']
        description = request.json['description']
        definition = request.json['definition']
        synonyms = request.json['synonyms']
        examples = request.json['examples']
        notes = request.json['notes']

        edit_component = VocabWordComponent.get_by_id(id)

        if edit_component.owner_id != user_id:
            response = {
                'restriction': 'User is not authorized to edit this component.',
                'status': 'restricted'
            }
            return jsonify(response)

        edit_component.update(
            part_of_speech, word, translation, description, definition, synonyms, examples, notes)

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
