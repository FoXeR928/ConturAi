$(document).ready(function(){
    get_chats_delete(get_token())
});

function open_page(page){
    $(".pages").hide()
    $("#"+page).show()
}

function get_chats_delete(token){
    $.ajax({
        url:'/chats/delete/irrevocably/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+token
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#chats").empty()
                $.each(result.chats, function(index,chat){
                    $("#chats_delete").append("<article class='chat_block -separete_block'><div class='text_block -separete_main'><p class='chat_name search_element'>"+chat.chat_name+"</p><p class='chat_name search_element'>"+chat.user_login+"</p></div><div class='checkbox_container -separete_second -button_del_close'><input class='checkbox_chat' type='checkbox' name='select_chat' id="+chat.id+"></div></article>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}