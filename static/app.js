$('#logout_button').on('click',function(e){
    e.preventDefault()
    localStorage.removeItem('access_token')
    $('#logout_form').submit()
})

