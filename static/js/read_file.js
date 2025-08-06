$('#file').change(function(event){
    event.preventDefault();
    var formData = new FormData();
    file_send=$(this)[0].files;
    if (file_send.length>0){
        formData.append('file',file_send[0]);
        $('.loader').css({'display': 'inline-block'});
        $.ajax({
            url:'/admin/ai/docs/read_file',
            method:'POST',
            data:formData,
            processData: false,
            success : function(result) {
                $('#file_name_text').val(result['name'])
                $('#file_text').val(result['text'])
                $('.loader').removeAttr('style');
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
                $('.loader').removeAttr('style');
            }
        })
        $(this).val('')
    }
})
$('#send_text').click(function(event){
    event.preventDefault()
    text_name=$('#file_name_text').val()
    text=$('#file_text').val()
    if (text.length>0){
        $.ajax({
            url:'/api/ai/add_docs',
            method:'POST',
            data:{},
            success : function() {
                $('#file_name_text').val('')
                $('#file_text').val('')
                window.location.reload()
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
                $('.loader').removeAttr('style');
            }
        })
    }
})