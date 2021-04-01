const editWordModal = document.getElementById('editWordModal');
const addComponentModal = document.getElementById('addComponentModal');
const editComponentModal = document.getElementById('editComponentModal');

// const addComponentForm = document.getElementById('addComponentForm');
const editComponentForm = document.getElementById('editComponentForm');

async function getComponentData(component_id) {
	headers = {
		Authorization : 'Bearer ' + localStorage.getItem('access_token')
	}
	const response = await axios.get(`/api/variations/${component_id}`, { headers: headers });

    editComponentModal.querySelector('#part_of_speech').value = response.data['part_of_speech']
	editComponentModal.querySelector('#variation').value = response.data['variation'];
	editComponentModal.querySelector('#translation').value = response.data['translation'];
	editComponentModal.querySelector('#description').value = response.data['description'];
	editComponentModal.querySelector('#examples').value = response.data['examples'];
	editComponentModal.querySelector('#notes').value = response.data['notes'];
}


editWordModal.addEventListener('show.bs.modal', function(event) {
	// Button that triggered the modal
	const button = event.relatedTarget;

	// Extract info from data-bs-* attributes
	const word = button.getAttribute('data-bs-whatever');

	// Update the modal's content.
	const modalTitle = editWordModal.querySelector('.modal-title');
	modalTitle.textContent = word;
});

addComponentModal.addEventListener('show.bs.modal', function(event) {
	// Button that triggered the modal
	const button = event.relatedTarget;

	// Extract info from data-bs-* attributes
	const heading = button.getAttribute('data-bs-whatever');

	// Update the modal's content.
	const modalTitle = addComponentModal.querySelector('.modal-title');
	modalTitle.textContent = heading;
});

editComponentModal.addEventListener('show.bs.modal', function(event) {
	// Button that triggered the modal
	const button = event.relatedTarget;

	// Extract info from data-bs-* attributes
	const heading = button.getAttribute('data-bs-whatever');
	const component_id = button.getAttribute('data-component-id');
	const word_id = button.getAttribute('data-word-id');
    editComponentForm.action=`/words/${word_id}/variations/${component_id}`

	// Update the modal's content.
	const modalTitle = editComponentModal.querySelector('.modal-title');
	modalTitle.textContent = heading;

	getComponentData(component_id);

});