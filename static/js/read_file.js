$('#file').change(function(event){
    event.preventDefault();
    var formData = new FormData();
    file_send=$(this)[0].files[0];
    formData.append('file',file_send);
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

})