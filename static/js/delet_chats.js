$('#button_del_select').click(function(event){
    event.preventDefault();
    let chats_id=[]
    $('.checkbox_chat').each(function(){
        if ($(this).prop('checked')){
            chats_id.push($(this).attr('id'))
        }
    })
    $.ajax({
        url:'/admin/chats/delet',
        method:'POST',
        data:{'chats':chats_id},
        success : function() {
            location.reload()
        },
        error: function(error){
            console.log(error);
            $('.loader').removeAttr('style');
        }
    }) 
})