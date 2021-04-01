async function login(email_address, password) {
	data = {
		email_address : email_address,
		password      : password
	};
	const response = await axios.post('/get-cookie', data);

	status = response['data']['status'];
	message = response['data']['message'];
	if (status == 'success') {
		access_token = response['data']['access_token'];
		localStorage.setItem('access_token', access_token);
		window.location.href = '/study';
		$('#login_form').submit();
	}
	else {
		$('#login_form').submit();
	}
}

$('#login_button').on('click', function(e) {
	e.preventDefault();
	login($('#email_address').val(), $('#password').val());
});
