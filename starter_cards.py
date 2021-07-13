#####################################################################
# -------------------- Create Starter Words ----------------------- #
#####################################################################

from models import VocabWord, VocabWordComponent

STARTER_WORDS = {
    'fr': [
        {
            'root': 'chien',
            'translation': 'dog',
            'notes': 'masculine noun.',
            'variations': [
                {
                    'part_of_speech': 'noun',
                    'variation': 'un chien',
                    'translation': 'a dog',
                    'description': 'singular, indefinite',
                    'definition': 'a domestic mammal that is related to the wolves and foxes.',
                    'synonyms': 'canine, hound, pooch',
                    'examples': 'Vous ne pouvez pas apprendre de nouveaux tours à un vieux chien.'
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'le chien',
                    'translation': 'the dog',
                    'description': 'singular, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': '(des) chiens',
                    'translation': 'dogs',
                    'description': 'plural, indefinite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'les chiens',
                    'translation': 'the dogs',
                    'description': 'plural, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                }
            ]
        }
    ],
    'sv': [
        {
            'root': 'hund',
            'translation': 'dog',
            'notes': 'en noun with -arna ending.',
            'variations': [
                {
                    'part_of_speech': 'noun',
                    'variation': 'en hund',
                    'translation': 'a dog',
                    'description': 'singular, indefinite',
                    'definition': 'a domestic mammal that is related to the wolves and foxes.',
                    'synonyms': 'canine, hound, pooch',
                    'examples': 'Du kan inte lära en gammal hund nya knep.'
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'hunden',
                    'translation': 'the dog',
                    'description': 'singular, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'hundar',
                    'translation': 'dogs',
                    'description': 'plural, indefinite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'hundarna',
                    'translation': 'the dogs',
                    'description': 'plural, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                }
            ]
        },
        {
            'root': 'försöka',
            'translation': 'try, attempt',
            'notes': 'ett noun, -er verb.',
            'variations': [
                {
                    'part_of_speech': 'noun',
                    'variation': 'ett försök',
                    'translation': 'an attempt',
                    'description': 'singular, indefinite',
                    'definition': 'a domestic mammal that is related to the wolves and foxes.',
                    'synonyms': 'try, attempt, experiment',
                    'examples': 'Ge det ett försök.'
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'försöket',
                    'translation': 'the attempt',
                    'description': 'singular, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'försök',
                    'translation': 'attempts',
                    'description': 'plural, indefinite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'noun',
                    'variation': 'försöken',
                    'translation': 'the attempts',
                    'description': 'plural, definite',
                    'definition': '',
                    'synonyms': '',
                    'examples': ''
                },
                {
                    'part_of_speech': 'verb',
                    'variation': 'försöker',
                    'translation': 'to (be) try(ing)',
                    'description': 'present tense',
                    'definition': '',
                    'synonyms': '',
                    'examples': 'Jag försöker bli bättre.'
                },
                {
                    'part_of_speech': 'verb',
                    'variation': 'försökte',
                    'translation': 'tried',
                    'description': 'past imperfect',
                    'definition': '',
                    'synonyms': '',
                    'examples': 'Jag försökte.'
                },
                {
                    'part_of_speech': 'verb',
                    'variation': 'försökt',
                    'translation': 'tried',
                    'description': 'supine / past perfect',
                    'definition': '',
                    'synonyms': '',
                    'examples': 'Jag har försökt.'
                }
            ]
        }
    ]
}


def create_starter_word(owner_id, source_code, root, translation, notes):
    new_vocab_word = VocabWord.add_vocab_word(
        owner_id, source_code, root, translation, notes)
    return new_vocab_word


def create_starter_component(root_id, owner_id, part_of_speech, variation, translation, description, definition, synonyms, examples):
    new_variation = VocabWordComponent.add_variation(
        root_id, owner_id, part_of_speech, variation, translation, description, definition, synonyms, examples, '')
    return new_variation


def create_all_language_starters(owner_id, source_code):

    if source_code in STARTER_WORDS:
        for word in STARTER_WORDS[source_code]:
            new_word = create_starter_word(
                owner_id, source_code, word['root'], word['translation'], word['notes'])
            for variation in word['variations']:
                create_starter_component(new_word.id, owner_id, variation['part_of_speech'], variation['variation'], variation['translation'],
                                         variation['description'], variation['definition'], variation['synonyms'], variation['examples'])
        return {
            'status': 'success',
            'message': 'Successfully created starter vocabulary words.'
        }

    else:
        return {
            'source_code': source_code,
            'message': f'There are no starter vocabulary words prepared for {source_code} language setting.',
            'status': 'not_configured'
        }
