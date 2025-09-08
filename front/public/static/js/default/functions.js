function get_token(){
    var token_get = document.cookie.match(/token=(.+?)(;|$)/);
    if (token_get==null){
        token=null
    }else{
        token=token_get[1]
    }
    return token
}

function create_flash(flash_status,message){
    $("#main").prepend("<div class='flash "+flash_status+"'>"+message+"</div>")
    setTimeout(function(){
        $('.flash').remove();
    }, 4000);
}

function search_on_page(table){
    search=$("#search"+table).val();
    $('.search_element'+table).each(function(){
        if (($(this).text()).includes(search)!=true){
            $(this).parent().hide();
        }
    })
    if(search==''){
        $('.search_element'+table).parent().show()
    }
}

function get_chats_nav(){
    $.ajax({
        url:'/chats/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#chats_nav").empty()
                $.each(result.chats, function(index,chat){
                    $("#chats_nav").append("<a class='nav_interior_element -button' href='messages?chat="+chat.id+"'> "+chat.chat_name+"</a>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}
function open_form(){
    $("#hide_form").show();
}
function close_form(){
    $("#hide_form").hide();
}

function password_check(form){
    password=$('#'+form+'password').val();
    password_checked=$('#'+form+'password_check').val();
    if ((password=='') || (password.length>=8)){
        $('#'+form+'password').removeAttr('style')
    }else{
        $('#'+form+'password').css('border','1px solid red');
    }
    if ((password==password_checked)){
        $('#'+form+'password_check').removeAttr('style')
    }else{
        $('#'+form+'password_check').css('border','1px solid red');
    }
}
function open_nav(){
    var left_shift='-283px'
    if($('#header').css('left')!='0px'){
        $('#header').animate({
            left:'0'
        },400)
        $('main').animate({
            'margin-left':'360px'
        },400)

    }
    else{
        $('#header').animate({
            left:left_shift,
        },400)
        $('main').animate({
            'margin-left':'75px'
        },400)
    }
}

function open_nav_hide(){
    $('.nav_hide_block').slideToggle()
}