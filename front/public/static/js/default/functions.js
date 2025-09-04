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

function search_on_page(event){
    event.preventDefault();
    search=$("#search").val();
    $('.search_element').each(function(){
        if (($(this).text()).includes(search)!=true){
            $(this).parent().hide();
        }
    })
    if(search==''){
        $('.search_element').parent().show()
    }
}

function get_chats_nav(token){
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
    $(this).parent().parent().parent().hide();
}