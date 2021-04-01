/* ******************************************************************
------------------------------ Settings -----------------------------
****************************************************************** */
const USER_ID = $('#user_id').val();

const $languageSourceCode = $('#language-source-code');

/* ******************************************************************
-------------------------- API requests -----------------------------
****************************************************************** */

async function populateLanguageWords(source_code) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	};
	const response = await axios.get(`/api/last/${source_code}`, { headers: headers });
	let last_source_code = response.data;
	window.location.href = `/words/language/${last_source_code}`;
}

/* ******************************************************************
----------------------- Event Listeners -----------------------------
****************************************************************** */

$languageSourceCode.on('change', function() {
	populateLanguageWords($languageSourceCode.val());
});
