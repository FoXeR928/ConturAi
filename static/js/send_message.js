$('#send_message').click(function(event){
    event.preventDefault();
    chat_send=$('#chat_id').val();
    message_send=$('#message').val();
    if (message_send!=''){
        $('.loader').css({'display': 'inline-block'});
        $("ul#chat")[0].scrollIntoView();
        $.ajax({
            url:'/chats/create_message',
            method:'POST',
            data:{chat_id:chat_send,message:message_send},
            success : function() {
                window.location.reload(true);
            },
            error: function(error){
                console.log(error);
                $('.loader').removeAttr('style');
            }
        })
    }
    else{
        $('#message').css('border','1px solid red');
    }
})
$('#message').on('input',function(){
    value_check=$(this).val();
    if (value_check!=''){
        $(this).removeAttr('style');
    }
})
