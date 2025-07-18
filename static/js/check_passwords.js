$('#send_update').click(function(event){
    password=$('#password_update').val()
    password_check=$('#password_update_check').val()
    if (password!=''){
        event.preventDefault()
    }
    if ((password==password_check) && (password.length>=8)){
        return true
    }
})
function test(){
    password=$('#password_update').val()
    password_check=$('#password_update_check').val()
    if (password!=''){
        return false
    }
    if ((password==password_check) && (password.length>=8)){
        return true
    }
}