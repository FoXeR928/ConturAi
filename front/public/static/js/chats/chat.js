let param=new URLSearchParams(document.location.search)
chat_id=param.get("chat")

$(document).ready(function(){
    get_messages_function(get_token(),chat_id)
});

function get_messages_function(token,chat_id){
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
                    $("#chat").append("<li class='message_box "+message.role+"' id='"+message.id+"'><p class='message'>"+message.text+"</p></li>")
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
    message_send=$('#message').val();
    if (message_send!=''){
        $('.loader').css({'display': 'inline-block'});
        $("ul#chat")[0].scrollIntoView();
        $.ajax({
            url:'AI/messages/create_ai?chat_id='+chat_id,
            method:'POST',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+token
            },
            data:JSON.stringify({'text':message_send}),
            success : function() {
                get_messages_function(token,chat_id)
            },
            error: function(error){
                console.log(error);
                $('.loader').removeAttr('style');
            }
        })
    }
}
                
            