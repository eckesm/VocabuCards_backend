

/* ******************************************************************
------------------------------ Settings -----------------------------
****************************************************************** */
const $sourceCode=$('#source_code')

/* ******************************************************************
-------------------------- API requests -----------------------------
****************************************************************** */

async function updateLastLanguage(source_code) {
	const response = await axios.get(`/api/words/${source_code}`);
	words = response.data;

	// $rootSelect.empty();
	// $rootSelect.append(`<option value="new">Add to new word</option>`);
	// for (let word of words) {
	// 	$rootSelect.append(`<option value="${word[0]}">${word[1]}</option>`);
	// }
}


/* ******************************************************************
----------------------- Event Listeners -----------------------------
****************************************************************** */
$sourceCode.on('change', function() {
    console.log($sourceCode.val())
	updateLastLanguage($sourceCode.val());
});


/* ******************************************************************
----------------------- Run When Loaded -----------------------------
****************************************************************** */
$sourceCode.val($('#last_language').val());