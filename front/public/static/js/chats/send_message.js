
$('#message').on('input',function(){
    value_check=$(this).val();
    if (value_check!=''){
        $(this).removeAttr('style');
    }
})
