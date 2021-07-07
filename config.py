import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    GOOGLE_LANGUAGE_KEY = os.environ.get(
        'GOOGLE_LANGUAGE_KEY')
    WORDS_API_KEY = os.environ.get('WORDS_API_KEY')

    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')

    REACT_PRODUCTION_DOMAIN = os.environ.get(
        'REACT_PRODUCTION_DOMAIN')


class ProductionConfig(Config):
    TESTING = False
    DEBUG = False


class DevelopmentConfig(Config):
    TESTING = False
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
