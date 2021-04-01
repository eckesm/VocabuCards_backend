/* ******************************************************************
------------------------------ Settings -----------------------------
****************************************************************** */

let activeSourceWord = null;
let activeTranslatedWord = null;
let languageSetting = $('#last_language').val();

const $languageSourceCode = $('#language-source-code');
const $modalLanguageSourceCode = $('#modal-language-source-code');
const $translateInput = $('#translate-input');
const $translatedWord = $('#translated-word');
const $definitionSelect = $('#definition-select');
const $partOfSpeech = $('#part-of-speech');
const $synonyms = $('#synonyms');
const $examples = $('#examples');
const $submit = $('#translate-submit');
const $search = $('#translated-search');
const $pos = $('#part-of-speech');
const $pastedText = $('#pasted-text');
const $adjustedHtml = $('#adjusted-html');
const $renderHtml = $('#render-html');
const $rootSelect = $('#root-select');
const $addWordButton = $('#add-word-button');

const IGNORED = [
	' ',
	'',
	'/',
	'.',
	',',
	'!',
	'@',
	'#',
	'-',
	'↵',
	'\n',
	'(',
	')',
	'"',
	'”',
	'[',
	']',
	'{',
	'}',
	'0',
	'1',
	'2',
	'3',
	'4',
	'5',
	'6',
	'7',
	'8',
	'9',
	'$',
	'%',
	'&',
	'*',
	'?',
	'<',
	'>',
	'+',
	'=',
	'_',
	'|',
	'–',
	':'
];

/* ******************************************************************
-------------------------- API requests -----------------------------
****************************************************************** */

async function getTranslation(word, sourceCode, translateCode) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	const response = await axios.get(`/api/translate/${word}/${sourceCode}/${translateCode}`, { headers: headers });
	translatedWord = response.data;
	$translatedWord.val(translatedWord);
}

async function searchDictionary(word) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	const response = await axios.get(`/api/dictionary/${word}`, { headers: headers });
	data = response.data;
	results = data['results'];
	activeTranslatedWord = results;
	$definitionSelect.empty();

	const studyMaterialModel = document.getElementById('studyMaterialModel');
	const definitionSelect = studyMaterialModel.querySelector('#definition-select');
	let index = 0;
	for (def in results) {
		let option = document.createElement('option');
		option.text = results[index]['definition'];
		option.value = index;
		option.dataset.pos = results[index]['partOfSpeech'];
		definitionSelect.add(option);
		index++;
	}

	updateDefinitionChange(activeTranslatedWord);
}

async function updateLanguageWords(source_code) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	const response = await axios.get(`/api/words/${source_code}`, { headers: headers });
	words = response.data;

	$rootSelect.empty();
	$rootSelect.append(`<option value="new">Add to new word</option>`);
	for (let word of words) {
		$rootSelect.append(`<option value="${word[0]}">${word[1]}</option>`);
	}
}

async function createNewWord(source_code, word, translation, definition, part_of_speech, synonyms, examples) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	data = {
		source_code    : source_code,
		part_of_speech : part_of_speech,
		word           : word,
		translation    : translation,
		definition     : definition,
		synonyms       : synonyms,
		examples       : examples
	};

	console.log(data);
	const response = await axios.post('/api/words/new', data, { headers: headers });

	console.log(response.data);

	if (response.data['status'] == 'errors') {
		errors = response.data['errors'];
		for (let error in errors) {
			for (let err of errors[error]) {
				console.log(err);
				$('#errors_ul').append(`<li>${err}</li>`);
			}
		}
	}
	else {
		window.open(`/words/${response.data['word']['id']}`, '_blank');
		$('#studyMaterialModel').modal('hide');
	}
}

async function createNewVariation(root_id, source_code, part_of_speech, word, translation, examples) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	data = {
		root_id        : root_id,
		source_code    : source_code,
		part_of_speech : part_of_speech,
		word           : word,
		translation    : translation,
		examples       : examples
	};

	const response = await axios.post('/api/variations/new', data, { headers: headers });

	console.log(response.data);

	if (response.data['status'] == 'errors') {
		errors = response.data['errors'];
		for (let error in errors) {
			for (let err of errors[error]) {
				console.log(err);
				$('#errors_ul').append(`<li>${err}</li>`);
			}
		}
	}
	else {
		window.open(`/words/${response.data['component']['root_id']}`, '_blank');
		$('#studyMaterialModel').modal('hide');
	}
}

/* ******************************************************************
-------------------- Functions & Auxillary --------------------------
****************************************************************** */

function splitString(unsplitString) {
	const splitList = [];
	let startPosition = 0;
	let endPosition = 0;
	for (let charPosition = 0; charPosition < unsplitString.length; charPosition++) {
		if (IGNORED.indexOf(unsplitString[charPosition]) == -1) {
			endPosition++;
		}
		else {
			word = unsplitString.slice(startPosition, charPosition);
			splitList.push(word);
			if (unsplitString[charPosition] != ' ') {
				splitList.push(unsplitString[charPosition]);
			}
			else {
				splitList.push(' ');
			}
			startPosition = charPosition + 1;
		}
	}
	return splitList;
}

function refineSplitString(wordList) {
	if (wordList.length < 3) {
		return wordList;
	}

	for (let position = 2; position < wordList.length; position++) {
		let A = wordList[position - 2];
		let B = wordList[position - 1];
		let C = wordList[position];

		if (A == '\n' && B == '' && C == '\n') {
			wordList.splice(position - 1, 2);
			position = Math.max((position = 2), 0);
		}
	}
	return wordList;
}

function renderHtml() {
	$adjustedHtml.empty();
	const pastedText = $pastedText.val();
	const unrefinedList = splitString(pastedText);
	const refinedList = refineSplitString(unrefinedList);

	let paragraphCount = 1;
	$adjustedHtml.append('<div id="p-1" class="paragraph"></div>');

	for (let word of refinedList) {
		if (word == '\n') {
			paragraphCount++;
			$adjustedHtml.append(`<div id="p-${paragraphCount}" class="paragraph"></div>`);
		}
		else if (word == ' ') {
			$(`#p-${paragraphCount}`).append(`<span class="word space">&nbsp</span>`);
		}
		else if (IGNORED.indexOf(word) == -1) {
			$(`#p-${paragraphCount}`).append(
				`<span class="word clickable" data-bs-toggle="modal" data-bs-target="#studyMaterialModel" data-bs-whatever="${word}">${word}</span>`
			);
		}
		else {
			$(`#p-${paragraphCount}`).append(`<span class="word ignore">${word}</span>`);
		}
	}

	// updateClickablePopovers();
	updateClickableClickEvent();
	updateClickableModals();
}

// function updateClickablePopovers() {
// 	var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
// 	var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
// 		return new bootstrap.Popover(popoverTriggerEl);
// 	});
// }

function updateClickableModals() {
	const studyMaterialModel = document.getElementById('studyMaterialModel');
	studyMaterialModel.addEventListener('show.bs.modal', function(event) {
		resetModalLoad();

		// Button that triggered the modal
		const button = event.relatedTarget;
		// Extract info from data-bs-* attributes
		const word = button.getAttribute('data-bs-whatever');
		// If necessary, you could initiate an AJAX request here
		// and then do the updating in a callback.
		//
		// Update the modal's content.
		const modalTitle = studyMaterialModel.querySelector('.modal-title');

		modalTitle.textContent = word;
		$translateInput.val(word);
		getTranslation(word, $languageSourceCode.val(), 'en');
	});
}

function updateClickableClickEvent() {
	$clickable = $('.clickable');

	$clickable.on('click', function() {
		$(this).addClass('clicked');
	});
}

function resetModalLoad() {
	$translatedWord.val('');
	$definitionSelect.empty();
	$definitionSelect.append(
		'<option value="placeholder" selected>Search the dictionary to see definitions...</option>'
	);
	$partOfSpeech.val('');
	$synonyms.val('');
	$examples.val('');
	$('#errors_ul').empty();
	$rootSelect.val('new');
}

function updateDefinitionChange(wordObject) {
	$partOfSpeech.val(wordObject[$definitionSelect.val()]['partOfSpeech']);

	const synonyms = wordObject[$definitionSelect.val()]['synonyms'];
	synonymsDisplay = constructSynonymsDisplay(synonyms);
	$synonyms.val(synonymsDisplay);

	const examples = wordObject[$definitionSelect.val()]['examples'];
	examplesDisplay = constructExamplesDisplay(examples);
	$examples.val(examplesDisplay);
}

function constructExamplesDisplay(array) {
	let display = '';
	if (array) {
		for (let index = 0; index < array.length; index++) {
			if (index > 0) {
				display += '; ';
			}
			display += array[index];
		}
	}
	else {
		display = '';
	}

	return display;
}

function constructSynonymsDisplay(array) {
	let display = '';
	if (array) {
		for (let index = 0; index < array.length; index++) {
			if (index > 0) {
				display += ', ';
			}
			display += array[index];
		}
	}
	else {
		display = '';
	}

	return display;
}

/* ******************************************************************
----------------------- Event Listeners -----------------------------
****************************************************************** */

$submit.click(function(e) {
	e.preventDefault();
	getTranslation($translateInput.val(), $languageSourceCode.val(), 'en');
});

$search.click(function(e) {
	e.preventDefault();
	searchDictionary($translatedWord.val());
});

$renderHtml.click(renderHtml);

$translateInput.on('change', function() {
	activeSourceWord = $translateInput.val();
});

$definitionSelect.on('change', function() {
	updateDefinitionChange(activeTranslatedWord);
});

$languageSourceCode.on('change', function() {
	languageSetting = $languageSourceCode.val();
	$modalLanguageSourceCode.val(languageSetting);
	updateLanguageWords(languageSetting);
});

$modalLanguageSourceCode.on('change', function() {
	languageSetting = $modalLanguageSourceCode.val();
	$languageSourceCode.val(languageSetting);
	updateLanguageWords(languageSetting);
});

$addWordButton.on('click', function() {
	const root_id = $rootSelect.val();
	const source_code = $modalLanguageSourceCode.val();
	const word = $translateInput.val();
	const translation = $translatedWord.val();
	let definition = $('#definition-select option:selected').text();
	let definition_value = $('#definition-select option:selected').val();
	const part_of_speech = $partOfSpeech.val();
	const synonyms = $synonyms.val();
	const examples = $examples.val();

	if (definition_value == 'placeholder') {
		definition = '';
	}

	if (root_id == 'new') {
		createNewWord(source_code, word, translation, definition, part_of_speech, synonyms, examples);
	}
	else {
		createNewVariation(root_id, source_code, part_of_speech, word, translation, examples);
	}
});

/* ******************************************************************
----------------------- Run When Loaded -----------------------------
****************************************************************** */

updateLanguageWords(languageSetting);
