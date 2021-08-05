from models import db, connect_db, generate_random_integer, Language, Translation, User
from app import app

db.drop_all()
db.create_all()

language1 = Language(id='de', language='Deutsch', english='German')
language2 = Language(id='en', language='English', english='English')
language3 = Language(id='es', language='Español', english='Spanish')
language4 = Language(id='fi', language='Suomea', english='Finnish')
language5 = Language(id='fr', language='Français', english='French')
language6 = Language(id='it', language='Italiano', english='Italian')
language7 = Language(id='pt-BR', language='Português (Brasil)',
                     english='Portuguese (Brazil)')
language8 = Language(
    id='pt-PT', language='Português (Portugal)', english='Portuguese (Portugal)')
language9 = Language(id='ru', language='русский', english='Russian')
language10 = Language(id='sv', language='Svenska', english='Swedish')

db.session.add_all([language1, language2, language3,
                    language4, language5, language6, language7, language8, language9, language10])
db.session.commit()

user1 = User.register('Matt', 'eckesm@gmail.com', 'passwordeckesm')
db.session.add(user1)
db.session.commit()
