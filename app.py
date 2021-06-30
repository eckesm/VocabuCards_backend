from flask import Flask, render_template, redirect, session, flash, g, request, jsonify, url_for, make_response
from functools import wraps
# from flask_cors.decorator import cross_origin
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, Language, Translation, User, VocabWord, VocabWordComponent
from forms import LoginForm, AddUserForm, VocabWordForm, VocabComponentForm, VocabWordAndComponentForm
from word import TranslationWord, DictionaryWord
import requests
import sys
import json
import os
# import jwt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS, cross_origin
from secret import SECRET_KEY, JWT_SECRET_KEY, SQLALCHEMY_DATABASE_URI, GOOGLE_LANGUAGE_KEY, WORDS_API_KEY

app = Flask(__name__)
cors = CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['GOOGLE_LANGUAGE_KEY'] = GOOGLE_LANGUAGE_KEY
app.config['WORDS_API_KEY'] = WORDS_API_KEY

jwt = JWTManager(app)

connect_db(app)
toolbar = DebugToolbarExtension(app)

CURR_USER_ID = "curr_user"
PARTS_OF_SPEECH = [('adjective', 'adjective'), ('noun', 'noun'),
                   ('verb', 'verb'), ('other', 'other')]

# -------------------------------------------------------------------


@app.before_request
def add_user_to_g():
    """If logged in, add current user to Flask global."""
    if CURR_USER_ID in session:
        g.user = User.get_by_id(session[CURR_USER_ID])
    else:
        g.user = None

# -------------------------------------------------------------------


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if CURR_USER_ID not in session:
            log_out_procedures()
            flash("You must be logged-in to access this resource.", 'danger')
            return redirect(url_for('login', next=request.url))
        return func(*args, **kwargs)
    return decorated_function


def log_out_procedures():
    if CURR_USER_ID in session:
        del session[CURR_USER_ID]
    g.user = None

# -------------------------------------------------------------------


@app.route('/')
def show_home_page():
    if CURR_USER_ID in session:
        return redirect('/study')
    else:
        return redirect('/login')

#####################################################################
# ---------------------------- Users -------------------------------#
#####################################################################


@app.route('/register', methods=['GET', 'POST'])
def show_new_user_registration_form():
    """Attempts to create a new user based on form submission."""

    if CURR_USER_ID in session:
        flash('You have been logged out', 'info')
    log_out_procedures()

    form = AddUserForm()
    if form.validate_on_submit():

        name = form.name.data
        email_address = form.email_address.data
        password = form.password.data

        new_user = User.register(name, email_address, password)

        # send_confirm_email_link(email_address)
        # flash('Welcome!', 'success')
        flash(
            f" Welcome, {new_user.name}!  You have successfully registered for an account.  Please log in to confirm your password.'", 'success')

        # session[CURR_USER_ID] = new_user.id
        # g.user = new_user

        # next_url = request.form.get("next")
        # if next_url:
        #     return redirect(next_url)
        # else:
        # return redirect('/')

        return redirect('/login')

    else:
        return render_template('register.html', form=form)

# -------------------------------------------------------------------


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

# -------------------------------------------------------------------


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.get_by_id(identity)

# -------------------------------------------------------------------


@app.route('/get-cookie', methods=['POST'])
def get_cookie():

    form = LoginForm()
    if form.validate():
        email_address = request.json.get("email_address", None)
        password = request.json.get("password", None)
        user = User.authenticate(email_address, password)

        if user == None:
            response = {
                "status": "fail",
                "message": f"There is no user with the email address {email_address}.  Please make sure you are entering the correct email address with the correct spelling."
            }
            return jsonify(response)

        if user == False:
            response = {
                "status": "fail",
                "message": "Credentials entered were incorrect.  Please try again."
            }
            return jsonify(response)

        access_token = create_access_token(identity=user)
        response = {
            "status": "success",
            "access_token": access_token,
            "message": f"Credentials for {email_address} were authenticated."
        }
        return jsonify(response)

    else:
        return jsonify('ERROR: form did not validate!')

# -------------------------------------------------------------------


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Show login form and login user."""

    if CURR_USER_ID in session:
        flash('You have been logged out', 'info')
    log_out_procedures()

    form = LoginForm()
    if form.validate_on_submit():

        email_address = form.email_address.data
        password = form.password.data
        user = User.authenticate(email_address, password)

        if user == None:

            flash(
                f'There is no user with the email address {email_address}.  Please make sure you are entering the correct email address with the correct spelling.', 'warning')
            return redirect('/login')

        if user == False:

            flash('Credentials entered were incorrect.  Please try again.',
                  'warning')
            return redirect('/login')

        session[CURR_USER_ID] = user.id
        g.user = user
        flash('Login successful!', 'info')

        next_url = request.form.get("next")
        if next_url:
            return redirect(next_url)
        else:
            return redirect('/')

    return render_template('login.html', form=form)


# -------------------------------------------------------------------


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log out user."""
    if CURR_USER_ID not in session:
        flash('There is no user logged in.', 'info')
    else:
        flash('You have been logged out', 'info')
    log_out_procedures()
    return redirect('/login')

#####################################################################
# ---------------------------- Study -------------------------------#
#####################################################################


@app.route('/study')
@login_required
def show_study_material():
    languages = Language.get_all_options()
    return render_template('study_material.html', languages=languages, parts_of_speech=PARTS_OF_SPEECH)

#####################################################################
# ---------------------------- Words -------------------------------#
#####################################################################


@app.route('/words/language/<source_code>', methods=['GET'])
@login_required
def view_user_words(source_code):

    languages = Language.get_all_options()
    sorted_words = db.session.query(VocabWord).filter(
        VocabWord.owner_id == g.user.id, VocabWord.source_code == source_code).order_by(VocabWord.root).all()

    return render_template('words.html', languages=languages, words=sorted_words, source_code=source_code)

# -------------------------------------------------------------------


@app.route('/words/new', methods=['GET', 'POST'])
@login_required
def add_vocab_word():

    form = VocabWordForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate_on_submit():

        source_code = form.source_code.data
        root = form.root.data
        translation = form.translation.data
        definition = form.definition.data
        synonyms = form.synonyms.data
        examples = form.examples.data
        notes = form.notes.data

        new_vocab_word = VocabWord.add_vocab_word(
            session[CURR_USER_ID], source_code, root, translation, definition, synonyms, examples, notes)

        g.user.update_last_language(source_code)

        flash(f"{new_vocab_word.root} created!", 'success')
        return redirect(f"/words/{new_vocab_word.id}")

    else:
        return render_template('new_vocab_word.html', vocab_word_form=form)


# -------------------------------------------------------------------


@app.route('/words/<word_id>', methods=['GET'])
@login_required
def show_vocab_word(word_id):

    word = VocabWord.get_by_id(word_id)
    components = word.components
    parts_of_speech = word.components_pos()
    print(f"POS: {parts_of_speech}", file=sys.stderr)

    vocab_word_form = VocabWordForm(obj=word)
    vocab_word_form.source_code.choices = Language.get_all_options()

    vocab_component_form = VocabComponentForm()

    return render_template('view_vocab_word.html', vocab_word_form=vocab_word_form, vocab_component_form=vocab_component_form, word=word, components=components, parts_of_speech=parts_of_speech)

# -------------------------------------------------------------------


@app.route('/words/<word_id>/delete', methods=['POST'])
@login_required
def delete_vocab_word(word_id):

    word = VocabWord.get_by_id(word_id)
    word_root = word.root
    db.session.delete(word)
    db.session.commit()

    flash(f"{word_root} deleted!", 'success')

    return redirect(f"/words/language/{g.user.last_language}")

# -------------------------------------------------------------------


@app.route('/words/<word_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vocab_word(word_id):

    word = VocabWord.get_by_id(word_id)
    form = VocabWordForm(obj=word)
    form.source_code.choices = Language.get_all_options()
    if form.validate_on_submit():

        source_code = form.source_code.data
        root = form.root.data
        translation = form.translation.data
        definition = form.definition.data
        synonyms = form.synonyms.data
        examples = form.examples.data
        notes = form.notes.data

        update_vocab_word = word.update(source_code,
                                        root, translation, definition, synonyms, examples, notes)

        g.user.update_last_language(source_code)

        flash(f"{update_vocab_word.root} edited!", 'success')
        return redirect(f"/words/{update_vocab_word.id}")

    else:
        flash(f"Error updating vocabulary word!", 'warning')
        return render_template('edit_vocab_word.html', vocab_word_form=form, word=word)

#####################################################################
# ------------------------- Variations -----------------------------#
#####################################################################


@app.route('/words/<word_id>/variations/new', methods=['GET', 'POST'])
@login_required
def add_vocab_component(word_id):

    form = VocabComponentForm()
    if form.validate_on_submit():

        # source_code = form.source_code.data
        part_of_speech = form.part_of_speech.data
        variation = form.variation.data
        translation = form.translation.data
        # description = form.description.data
        examples = form.examples.data
        # notes = form.notes.data

        new_variation = VocabWordComponent.add_variation(word_id,
                                                         session[CURR_USER_ID], part_of_speech, variation, translation, examples)

        flash(f"{new_variation.variation} created!", 'success')
        return redirect(f"/words/{word_id}")

    else:
        word = VocabWord.get_by_id(word_id)
        return render_template('new_vocab_component.html', vocab_component_form=form, word=word)


# -------------------------------------------------------------------


@app.route('/words/<word_id>/variations/<component_id>', methods=['GET', 'POST'])
@login_required
def edit_vocab_component(word_id, component_id):

    component = VocabWordComponent.get_by_id(component_id)

    form = VocabComponentForm()
    if form.validate_on_submit():

        part_of_speech = form.part_of_speech.data
        variation = form.variation.data
        translation = form.translation.data
        description = form.description.data
        examples = form.examples.data
        notes = form.notes.data

        update_component = component.update(
            part_of_speech, variation, translation, description, examples, notes)

        flash(f"{update_component.variation} edited!", 'success')
        return redirect(f"/words/{update_component.root_id}")

    else:
        flash(f"Error updating vocabulary word variation!", 'warning')
        return render_template('edit_vocab_component.html', vocab_component_form=form, component=component)

# -------------------------------------------------------------------


@app.route('/variations/<component_id>/delete', methods=['POST'])
@login_required
def delete_variation(component_id):

    component = VocabWordComponent.get_by_id(component_id)
    variation = component.variation
    root_id = component.root_id
    db.session.delete(component)
    db.session.commit()

    flash(f"{variation} deleted!", 'success')

    return redirect(f"/words/{root_id}")


#####################################################################
# ------------------------- API routes -----------------------------#
#####################################################################

@app.route('/api/auth/login', methods=['POST'])
@cross_origin()
def login_user_via_API():
    email = request.json['email']
    password = request.json['password']
    # print(email, file=sys.stderr)
    # print(password, file=sys.stderr)
    user = User.authenticate(email, password)

    if user == None:
        response = {
            'status': 'fail',
            'message': f'There is no user with the email address {email}.  Please make sure you are entering the correct email address with the correct spelling.'}
        return jsonify(response)

    if user == False:
        response = {
            'status': 'fail',
            'message': 'Credentials entered were incorrect.  Please try again.'}
        return jsonify(response)

    if user:
        access_token = create_access_token(identity=user)
        response = {
            'status': 'success',
            'access_token': access_token,
            'message': f"Credentials for {email} were authenticated."}
        return jsonify(response)

    response = {
        'status': 'error',
        'message': 'Inputs did not validate!'}
    return jsonify(response)

# -------------------------------------------------------------------
# DELETE EVENTUALLY


@app.route('/api/translate/<word>/<source_code>/<translate_code>', methods=['GET'])
@jwt_required()
def translate_OLD(word, source_code, translate_code):

    word = TranslationWord(word, source_code, translate_code)
    translation = word.translated_word
    return jsonify(translation)


# -------------------------------------------------------------------

@app.route('/api/vocab/translate/<word>/<source_code>/<translate_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def translate(word, source_code, translate_code):

    word = TranslationWord(word, source_code, translate_code)
    translation = word.translated_word

    return jsonify(translation)


# -------------------------------------------------------------------
# DELETE

@app.route('/api/dictionary/<word>', methods=['GET'])
@jwt_required()
def search_dictionary_OLD(word):

    word = DictionaryWord(word)
    data = json.loads(word.definitions)
    return jsonify(data)

# -------------------------------------------------------------------


@app.route('/api/vocab/dictionary/<word>', methods=['GET'])
@jwt_required()
def search_dictionary(word):

    word = DictionaryWord(word)
    data = json.loads(word.definitions)
    return jsonify(data)

# -------------------------------------------------------------------


@app.route('/api/variations/<component_id>', methods=['GET'])
@jwt_required()
def get_variation_data_by_api(component_id):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    component = VocabWordComponent.get_by_id(component_id)

    if component.owner_id == user.id:
        return jsonify(component.serialize())

# -------------------------------------------------------------------
# DELETE


@app.route('/api/words/<source_code>', methods=['GET'])
@jwt_required()
def get_users_language_words_OLD(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    user.update_last_language(source_code)

    words = db.session.query(VocabWord.id, VocabWord.root).filter(
        VocabWord.owner_id == user.id, VocabWord.source_code == source_code).order_by(VocabWord.root).all()

    return jsonify([[word[0], word[1]] for word in words])

# -------------------------------------------------------------------


@app.route('/api/vocab/start', methods=['GET'])
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
        'languages': languages,
        'last_source_code': last_language,
        'words_array': [word.serialize_and_components() for word in words],
        'user': user.email_address
    }

    return jsonify(response)

# -------------------------------------------------------------------


@app.route('/api/vocab/words/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_users_language_words(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    words = db.session.query(VocabWord).filter(
        VocabWord.owner_id == user.id, VocabWord.source_code == source_code).order_by(VocabWord.root).all()

    return jsonify([word.serialize_and_components() for word in words])

# -------------------------------------------------------------------
# DELETE


@app.route('/api/last/<source_code>', methods=['GET'])
@jwt_required()
def update_users_last_language_OLD(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    user.update_last_language(source_code)

    return jsonify(user.last_language)

# -------------------------------------------------------------------


@app.route('/api/vocab/last/<source_code>', methods=['GET'])
@cross_origin()
@jwt_required()
def update_users_last_language(source_code):

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)
    user.update_last_language(source_code)

    return jsonify(user.last_language)

# -------------------------------------------------------------------


@app.route('/api/vocab/last', methods=['GET'])
@cross_origin()
@jwt_required()
def get_users_last_language():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    return jsonify(user.last_language)

# -------------------------------------------------------------------


@app.route('/api/vocab/languages', methods=['GET'])
@cross_origin()
@jwt_required()
def get_all_languages():

    languages = Language.get_all_options()

    return jsonify(languages)

# -------------------------------------------------------------------
# DELETE EVENTUALLY

@app.route('/api/words/new', methods=['POST'])
@jwt_required()
def add_new_word_by_api_OLD():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    form = VocabWordAndComponentForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate():

        user_id = user.id
        source_code = request.json['source_code']
        part_of_speech = request.json['part_of_speech']
        word = request.json['word']
        translation = request.json['translation']
        definition = request.json['definition']
        synonyms = request.json['synonyms']
        examples = request.json['examples']

        if definition == '0':
            definition = ''

        new_word = VocabWord.add_vocab_word(
            user_id, source_code, word, translation, definition, synonyms, examples, '')

        print(f"ROOT_ID: {new_word.id}", file=sys.stderr)

        new_component = VocabWordComponent.add_variation(
            new_word.id, user_id, part_of_speech, word, translation, examples)

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


@app.route('/api/vocab/words/new', methods=['POST'])
@jwt_required()
def add_new_word_by_api():

    current_user = get_jwt_identity()
    user = User.get_by_id(current_user)

    form = VocabWordAndComponentForm()
    form.source_code.choices = Language.get_all_options()
    if form.validate():

        user_id = user.id
        source_code = request.json['source_code']
        part_of_speech = request.json['part_of_speech']
        word = request.json['word']
        translation = request.json['translation']
        definition = request.json['definition']
        synonyms = request.json['synonyms']
        examples = request.json['examples']

        if definition == '0':
            definition = ''

        new_word = VocabWord.add_vocab_word(
            user_id, source_code, word, translation, definition, synonyms, examples, '')

        print(f"ROOT_ID: {new_word.id}", file=sys.stderr)

        # new_component = VocabWordComponent.add_variation(
        #     new_word.id, user_id, part_of_speech, word, translation, examples)

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
# DELETE

@app.route('/api/variations/new', methods=['POST'])
@jwt_required()
def add_new_variation_by_api_OLD():

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
        examples = request.json['examples']

        new_component = VocabWordComponent.add_variation(
            root_id, user_id, part_of_speech, word, translation, examples)

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


@app.route('/api/vocab/variations/new', methods=['POST'])
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
        examples = request.json['examples']

        new_component = VocabWordComponent.add_variation(
            root_id, user_id, part_of_speech, word, translation, examples)

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
