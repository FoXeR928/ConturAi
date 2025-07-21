$('.form_users').on('submit',function(event){
    password=$(this).children('.password').val();
    password_check=$(this).children('.password_check').val();

    if ((password!='') && ((password.length<8) || (password!=password_check))){
        event.preventDefault();
        if (password.length<8){
            $(this).children('.password').css('border','1px solid red');
        }
        if (password!=password_check){
            $(this).children('.password_check').css('border','1px solid red');
        }
    }
    else{
        this.submit();
    }
})

$('.password_check').on('input',function(){
    password=$(this).parent().children('.password').val();
    password_check=$(this).val();
    if (password==password_check){
        $(this).removeAttr('style');
    }
    else{
        $(this).css('border','1px solid red');
    }
})

$('.password').on('input',function(){
    password=$(this).val();
    if (password.length>=8){
        $(this).removeAttr('style')
    }
    else{
        $(this).css('border','1px solid red');
    }
})