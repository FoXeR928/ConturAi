function auth(event){
    event.preventDefault();
    login=$("#user").val();
    password=$("#password").val();
    expires_use=$("expires").prop('checked');
    send_data={
        "username":login,
        "password":password,
        "expires_use":expires_use
    }
    if (login!="" && password!=""){
        $.ajax({
            url:'/auth/login',
            method:'POST',
            headers:{
                "Content-Type":"application/x-www-form-urlencoded"
            },
            data:send_data,
            success : function(result) {
                if (result["result"]==false){
                    create_flash(flash_status=result["categoty"],message=result["message"])
                }else{
                    document.cookie="token="+result["access_token"]
                    create_flash(flash_status="success",message="Авторизация пройдена")
                    window.location.href="/chats"
                }
            },
            error: function(error){
                console.log(error);
                create_flash(flash_status="warning",message="Авторизация пройдена")
            }
        })
    }else{
        create_flash(flash_status="warning",message="Не все поля заполнены")
    }
}