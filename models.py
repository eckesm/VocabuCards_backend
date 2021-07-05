from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from secrets import token_urlsafe
import string
import random
import jwt
import datetime


db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    db.app = app
    db.init_app(app)


def generate_random_string(length, unique_callback):
    unique_string = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=length))
    while(unique_callback(unique_string) != None):
        unique_string = ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=length))
    return unique_string


def generate_random_integer(length, unique_callback):
    unique_string = ''.join(random.choices(string.digits, k=length))
    while(unique_callback(unique_string) != None):
        unique_string = ''.join(random.choices(string.digits, k=length))
    return int(unique_string)


class Language(db.Model):
    """Language model."""

    __tablename__ = 'languages'

    id = db.Column(db.String(5), primary_key=True)
    language = db.Column(db.Text, nullable=False, unique=True)
    english = db.Column(db.Text, nullable=False, unique=True)

    @classmethod
    def get_all_options(cls):
        return [(language.id, language.english) for language in Language.query.all()]


class User(db.Model):
    """User model."""

    __tablename__ = 'users'

    id = db.Column(db.Text, primary_key=True)
    email_address = db.Column(db.String(254), nullable=False, unique=True)
    email_confirm_token = db.Column(db.Text, nullable=True)
    is_email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.Text, nullable=False)
    password_reset_token = db.Column(db.Text, nullable=True)
    api_token = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(25), nullable=False)
    last_language = db.Column(
        db.String(5), db.ForeignKey('languages.id'), default='en')
    first_login = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           server_default=func.now())
    last_login = db.Column(db.DateTime, nullable=False,
                           server_default=func.now())
    current_text = db.Column(db.Text, nullable=True)

    words = db.relationship('VocabWord', backref='owner',
                            cascade='all, delete-orphan')

    def change_password(self, password):
        """Change password."""
        hashed = bcrypt.generate_password_hash(password, rounds=14)
        self.password = hashed.decode("utf8")
        self.password_reset_token = None
        db.session.add(self)
        db.session.commit()

    def update_last_language(self, source_code):
        """Update the last source code used by the user."""
        self.last_language = source_code
        db.session.add(self)
        db.session.commit()
        return source_code

    def update_current_text(self, text):
        """Update the user's current text."""
        self.current_text = text
        db.session.add(self)
        db.session.commit()
        return text

    def update_last_login(self):
        """Update user's last login to now."""
        self.last_login = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()
        return self.last_login

    def update_first_login(self):
        """Update user's first login status to false."""
        self.first_login = False
        db.session.add(self)
        db.session.commit()
        return self.first_login

    def confirm_email_address(self):
        """Update is_email_confirmed to True and clear email_confirm_token."""
        self.is_email_confirmed = True
        self.email_confirm_token = None
        db.session.add(self)
        db.session.commit()
        return self.is_email_confirmed

    @ classmethod
    def generate_api_token(cls):
        return token_urlsafe(16)

    @ classmethod
    def register(cls, name, email_address, password, source_code='en'):
        """Register a new user to the database."""
        hashed = bcrypt.generate_password_hash(password, rounds=14)
        hashed_utf = hashed.decode("utf8")

        new_user = cls(id=generate_random_string(10, cls.get_by_id), name=name, email_address=email_address.lower(
        ), password=hashed_utf, last_language=source_code, api_token=cls.generate_api_token(), email_confirm_token=cls.generate_api_token())
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @ classmethod
    def authenticate(cls, email_address, password):
        """Validate that user exists and password is correct."""
        user = cls.query.filter_by(
            email_address=email_address.lower()).one_or_none()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                return cls.get_by_email(email_address.lower())
            else:
                return False
        else:
            return None

    @ classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).one_or_none()

    @ classmethod
    def get_by_email(cls, email_address):
        return cls.query.filter_by(email_address=email_address.lower()).one_or_none()

    @ classmethod
    def get_by_password_reset_token(cls, token):
        return cls.query.filter_by(password_reset_token=token).one_or_none()

    @ classmethod
    def get_by_email_confirm_token(cls, token):
        return cls.query.filter_by(email_confirm_token=token).one_or_none()


class Translation(db.Model):
    """Translated word model."""

    __tablename__ = 'translations'

    id = db.Column(db.Text, primary_key=True)
    source_code = db.Column(db.String(5), db.ForeignKey('languages.id'))
    translate_code = db.Column(db.String(5), db.ForeignKey('languages.id'))
    source_word = db.Column(db.Text, nullable=False)
    translated_word = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Translation id: {self.id} | {self.source_code}: {self.source_word} | {self.translate_code}: {self.translated_word}>"

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def get_by_source_word(cls, source_code, translate_code, source_word):
        return cls.query.filter_by(source_code=source_code, translate_code=translate_code, source_word=source_word).one_or_none()

    @classmethod
    def add_translation(cls, source_code, translate_code, source_word, translated_word):
        new_translation = cls(id=generate_random_string(10, cls.get_by_id), source_code=source_code,
                              translate_code=translate_code, source_word=source_word, translated_word=translated_word)
        db.session.add(new_translation)
        db.session.commit()
        return new_translation


class DictionaryEntry(db.Model):
    """Dictionary entry model."""

    __tablename__ = 'dictionary_entries'

    id = db.Column(db.Text, primary_key=True)
    language_code = db.Column(db.String(5), db.ForeignKey('languages.id'))
    word = db.Column(db.Text, nullable=False)
    definitions = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Dictionary id: {self.id} | {self.language_code}: {self.word}>"

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def get_by_word(cls, language_code, word):
        return cls.query.filter_by(language_code=language_code, word=word).one_or_none()

    @classmethod
    def add_dictionary_entry(cls, language_code, word, definitions):
        new_entry = cls(id=generate_random_string(10, cls.get_by_id),
                        language_code=language_code, word=word, definitions=definitions)
        db.session.add(new_entry)
        db.session.commit()
        return new_entry


class VocabWord(db.Model):
    """Vocabulary word model."""

    __tablename__ = 'vocab_words'

    id = db.Column(db.Text, primary_key=True)
    owner_id = db.Column(db.Text, db.ForeignKey('users.id'))
    source_code = db.Column(db.String(5), db.ForeignKey('languages.id'))
    root = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    components = db.relationship('VocabWordComponent', backref='root_word',
                                 cascade='all, delete-orphan')

    def serialize(self):
        return{
            'id': self.id,
            'owner_id': self.owner_id,
            'source_code': self.source_code,
            'root': self.root,
            'translation': self.translation,
            'notes': self.notes,
            'components': [component.id for component in self.components]
        }

    def serialize_and_components(self):
        return{
            'id': self.id,
            'owner_id': self.owner_id,
            'source_code': self.source_code,
            'root': self.root,
            'translation': self.translation,
            'notes': self.notes,
            'components': [component.serialize() for component in self.components]
        }

    def components_pos(self):
        pos = {}

        for component in self.components:
            pos[component.part_of_speech] = []

        for component in self.components:
            pos[component.part_of_speech].append(component.variation)

        return pos

    def update(self, source_code, root, translation, notes):
        self.source_code = source_code
        self.root = root
        self.translation = translation
        self.notes = notes
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def add_vocab_word(cls, owner_id, source_code, root, translation, notes):
        new_vocab_word = cls(id=generate_random_string(20, cls.get_by_id), owner_id=owner_id, source_code=source_code,
                             root=root, translation=translation, notes=notes)
        db.session.add(new_vocab_word)
        db.session.commit()
        return new_vocab_word


class VocabWordComponent(db.Model):
    """Component of vocabulary word model."""

    __tablename__ = 'vocab_word_components'

    id = db.Column(db.Text, primary_key=True)
    root_id = db.Column(db.Text, db.ForeignKey('vocab_words.id'))
    owner_id = db.Column(db.Text, db.ForeignKey('users.id'))
    variation = db.Column(db.Text, nullable=False)
    translation = db.Column(db.Text, nullable=True)
    part_of_speech = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    definition = db.Column(db.Text, nullable=True)
    synonyms = db.Column(db.Text, nullable=True)
    examples = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def serialize(self):
        return{
            'id': self.id,
            'root_id': self.root_id,
            'owner_id': self.owner_id,
            'variation': self.variation,
            'translation': self.translation,
            'part_of_speech': self.part_of_speech,
            'description': self.description,
            'definition': self.definition,
            'synonyms': self.synonyms,
            'examples': self.examples,
            'notes': self.notes
        }

    def update(self, part_of_speech, variation, translation, description, definition, synonyms, examples, notes):
        self.part_of_speech = part_of_speech
        self.variation = variation
        self.translation = translation
        self.description = description
        self.definition = definition
        self.synonyms = synonyms
        self.examples = examples
        self.notes = notes
        db.session.add(self)
        db.session.commit()
        return self

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def add_variation(cls, root_id, owner_id, part_of_speech, variation, translation, description, definition, synonyms, examples, notes):
        new_variation = cls(id=generate_random_string(20, cls.get_by_id), root_id=root_id, owner_id=owner_id,
                            part_of_speech=part_of_speech, variation=variation, translation=translation, description=description, definition=definition, synonyms=synonyms, examples=examples, notes=notes)
        db.session.add(new_variation)
        db.session.commit()
        return new_variation
