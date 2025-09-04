$(document).ready(function(){
    get_messages(get_token(),get_chat_id())
});

function get_chat_id(){
    let param=new URLSearchParams(document.location.search)
    chat_id=param.get("chat")
    return chat_id
}

function get_messages(token,chat_id){
    $.ajax({
        url:'messages/get?chat_id='+chat_id,
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+token
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/chats"
            }else{
                $("#chat").empty()
                $.each(result.messages_history, function(index,message){
                    $("#chat").append("<li class='message_box "+message.chat_role+"' id='"+message.id+"'><p class='message'>"+message.text+"</p></li>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/chats"
        }
    })
}

function send_message(event){
    event.preventDefault();
    token=get_token()
    chat_id=get_chat_id()
    var message_send=$('#message').val();
    var message_ai=$('#message_ai').prop('checked');
    if (message_ai==true){
        url_for='/AI/messages/create_ai?chat_id='
    }else{
        url_for='messages/create?chat_id='
    }
    if (message_send!=''){
        $("#chat").append("<span class='loader'></span>")
        $("#chat")[0].scrollIntoView();
        $.ajax({
            url:url_for+chat_id,
            method:'POST',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+token
            },
            data:JSON.stringify({'text':message_send}),
            success : function() {
                $('.loader').remove();
                get_messages(token,chat_id)
            },
            error: function(error){
                $('.loader').remove();
                console.log(error);
                create_flash("error","Ошибка отправки")
            }
        })
    }
}
                
            