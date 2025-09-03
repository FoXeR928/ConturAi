$(document).ready(function(){
    get_chats_function(get_token())
});
function get_chats_function(token){
    $.ajax({
        url:'/chats/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+token
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $.each(result.chats, function(index,chat){
                    $("#chats").append("<article class='chat_block -separete_block'><a class='chat_name -separete_main search_element'>"+chat.chat_name+"</a><a class='button_del_chat -button_del_close -separete_second'>Удалить</a></article>")
                    $("#chats_nav").append("<a class='nav_interior_element -button'>"+chat.chat_name+"</a>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}


    
    

