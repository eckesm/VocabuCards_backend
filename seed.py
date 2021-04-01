from models import db, connect_db, generate_random_integer, Language, Translation, User
from app import app

db.drop_all()
db.create_all()

language1 = Language(id='en', language='English', english='English')
language2 = Language(id='fr', language='French', english='French')
language3 = Language(id='ge', language='German', english='German')
language4 = Language(id='ru', language='Russian', english='Russian')
language5 = Language(id='es', language='Spanish', english='Spanish')
language6 = Language(id='sv', language='Svenska', english='Swedish')

db.session.add_all([language1, language2, language3,
                   language4, language5, language6])
db.session.commit()

user1 = User.register('Matt', 'eckesm@gmail.com', 'passwordeckesm')
db.session.add(user1)
db.session.commit()
