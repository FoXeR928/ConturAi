$("#send_chat").click(function(event){
    event.preventDefault();
    chat_name=$("#name_chat").val()
    if (chat_name!=""){
        $.ajax({
            url:'/chats/create',
            method:'POST',
            data:JSON.stringify({"chat_name":chat_name}),
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            success : function(result) {
                create_flash(flash_status=result["category"],message=result["message"])
                get_chats_function(get_token())
            },
            error: function(error){
                console.log(error);
                $('.loader').removeAttr('style');
            }
        }) 
    }else{
        create_flash(flash_status="warning",message="Поле названия пустое")
    }
    
})