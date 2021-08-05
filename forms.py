from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, IntegerField, RadioField, SelectField, PasswordField, TextAreaField, FileField
from wtforms.validators import ValidationError, InputRequired, Optional, Email, EqualTo, URL, Length
import email_validator
from models import User, Language

PERMITTED_NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqurstuvwxyz-_'. "
PERMITTED_PASSWORD_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqurstuvwxyz1234567890!@#$%^<>&*(){}|-_+=;:?~`.,"

POS_CHOICES = [('adjective', 'adjective'), ('adverb', 'adverb'), ('article', 'article'), ('conjunction', 'conjunction'),
               ('expression', 'expression'), ('noun', 'noun'), ('preposition', 'preposition'), ('verb', 'verb'), ('other', 'other')]


class PermittedChars(object):
    def __init__(self, permitted_characters, message=None):
        self.permitted_characters = permitted_characters
        if not message:
            message = f'Field can only contain the following characters: {permitted_characters}'
        self.message = message

    def __call__(self, form, field):
        for char in field.data:
            if char not in self.permitted_characters:
                raise ValidationError(self.message)


def AvailableEmail(form, field):
    email = field.data
    if User.get_by_email(email) != None:
        raise ValidationError(
            f'The email address "{email}" is already associated with an account.')


class LoginForm(FlaskForm):
    """User login form."""

    class Meta:
        csrf = False

    email_address = StringField("Email address", validators=[
        InputRequired(message="Email address required."),
        Email(
            message="Email address format required. Example: username@domain.com")])

    password = PasswordField("Password", validators=[
                             InputRequired(message="Password required.")])


class AddUserForm(FlaskForm):
    """Form for adding users."""

    class Meta:
        csrf = False

    name = StringField("Name", validators=[
        InputRequired(message="Name required."),
        Length(
            min=3, max=25, message="Must be between 3 and 25 characters."),
        PermittedChars(permitted_characters=PERMITTED_NAME_CHARS, message="Name can only contain letters and -_'.")])

    email_address = StringField("Email address", validators=[
                                InputRequired(
                                    message="Email address required."),
                                Email(
                                    message="Email address format required. Example: username@domain.com"),
                                AvailableEmail])

    password = PasswordField("Password", validators=[
                             InputRequired(message="Password required."),
                             Length(
                                 min=8, max=40, message="Password must be between 8 and 40 characters."),
                             PermittedChars(permitted_characters=PERMITTED_PASSWORD_CHARS, message="Password can only contain letters, numbers, and !@#$%^<>&*()\u007B\u007D|-_+=;:?~`.,")])

    password_check = PasswordField("Password", validators=[
        InputRequired(message="Re-enter Password required."),
        Length(
            min=8, max=40, message="Re-enter Password must be between 8 and 40 characters."),
        PermittedChars(permitted_characters=PERMITTED_PASSWORD_CHARS, message="Password can only contain letters, numbers, and !@#$%^<>&*()\u007B\u007D|-_+=;:?~`.,")])

    # source_code = SelectField("Starting language",
    #                           validators=[InputRequired(message="Starting Foreign Language required.")])


class VocabWordForm(FlaskForm):
    """Form for vocabulary words."""

    class Meta:
        csrf = False

    source_code = SelectField(
        "Language *", validators=[InputRequired(message="Language is required.")])
    word = StringField(
        "Word *", validators=[InputRequired(message="Word is required.")])
    translation = StringField("Translation",
                              validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])


class VocabComponentForm(FlaskForm):
    """Form for vocabulary word components."""

    class Meta:
        csrf = False

    part_of_speech = SelectField("Part of speech",
                                 choices=POS_CHOICES,
                                 validators=[InputRequired(message="Part of Speech is required.")])
    word = StringField(
        "Word *", validators=[InputRequired(message="Word is required.")])
    translation = StringField("Translation",
                              validators=[Optional()])
    description = StringField("Description", validators=[Optional()])
    definition = StringField("Definition",
                             validators=[Optional()])
    synonyms = StringField("Synonyms",
                           validators=[Optional()])
    examples = TextAreaField("Examples", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])


class VocabWordAndComponentForm(FlaskForm):
    """Form for adding a new vocabulary word and component."""

    class Meta:
        csrf = False

    source_code = SelectField(
        "Language", validators=[InputRequired(message="Language is required.")])
    word = StringField(
        "Word *", validators=[InputRequired(message="Word is required.")])
    translation = StringField("Translation",
                              validators=[Optional()])
    description = StringField("Description", validators=[Optional()])
    definition = StringField("Definition",
                             validators=[Optional()])
    part_of_speech = SelectField("Part of speech",
                                 choices=POS_CHOICES,
                                 validators=[InputRequired(message="Part of speech is required.")])
    synonyms = StringField("Synonyms",
                           validators=[Optional()])
    examples = TextAreaField("Examples", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
