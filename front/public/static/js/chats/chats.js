$(document).ready(function(){
    get_chats()
});

function create_chat(event){
    event.preventDefault();
    chat_name=$("#name_chat").val()
    if (chat_name!=""){
        $.ajax({
            url:'/chats/create',
            method:'POST',
            data:JSON.stringify({"name":chat_name}),
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            success : function(result) {
                get_chats()
                get_chats_nav()
                $("#name_chat").val("")
                close_form()

                create_flash(flash_status=result["category"],message=result["message"])  
            },
            error: function(error){
                console.log(error);
            }
        }) 
    }else{
        create_flash(flash_status="warning",message="Поле названия пустое")
    }
    
}

function get_chats(){
    $.ajax({
        url:'/chats/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#chats").empty()
                $.each(result.chats, function(index,chat){
                    $("#chats").append("<article class='chat_block -separete_block'><a class='chat_name -separete_main search_element_chats' href='messages?chat="+chat.id+"'>"+chat.chat_name+"</a><button class='button_del_chat -button_del_close -separete_second' onclick='delete_chat(event,"+chat.id+")'>Удалить</a></article>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function delete_chat(event,chat_id){
    console.log(chat_id)
    event.preventDefault();
    $.ajax({
        url:'/chats/delete',
        method:'PATCH',
        data:JSON.stringify({"id":chat_id}),
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            get_chats(get_token())
            get_chats_nav(get_token())
            create_flash(flash_status=result["category"],message=result["message"])
        },
        error: function(error){
            console.log(error);
            $('.loader').removeAttr('style');
        }
    }) 
}