$(document).ready(function(){
    get_chats_delete()
    get_users()
    get_configs_ai()
    get_configs()
});

function open_page(page){
    $(".pages").hide()
    $("#"+page).show()
}

function get_chats_delete(){
    $.ajax({
        url:'/chats/delete/irrevocably/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#chats").empty()
                $.each(result.chats, function(index,chat){
                    $("#chats_delete").append("<article class='chat_block -separete_block'><div class='text_block -separete_main'><p class='chat_name search_element'>"+chat.chat_name+"</p><p class='chat_name search_element'>"+chat.user_login+"</p></div><div class='checkbox_container -separete_second -button_del_close'><input class='checkbox_chat' type='checkbox' name='select_chat' id="+chat.id+"></div></article>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function delete_all_chats(){
    $.ajax({
        url:'/chats/delete/irrevocably/all',
        method:'DELETE',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==true){
                    get_chats_delete()
                }
            create_flash(result["category"],result["message"])
        },
        error: function(error){
            console.log(error);
            create_flash("error","Ошибка удаления")
        }
    })
} 

function delete_checked_chats(){
    let chats_id=[]
    $('.checkbox_chat').each(function(){
        if ($(this).prop('checked')){
            chats_id.push($(this).attr('id'))
        }
    })
    if (chats_id.length>0){
        $.ajax({
            url:'/chats/delete/irrevocably/list',
            method:'DELETE',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(chats_id),
            success : function(result) {
                if (result["result"]==true){
                    get_chats_delete()
                }
                create_flash(result["category"],result["message"])
            },
            error: function(error){
                console.log(error);
                create_flash("error","Ошибка удаления")
            }
        })
    }
} 

function recovery_checked_chats(){
    let chats_id=[]
    $('.checkbox_chat').each(function(){
        if ($(this).prop('checked')){
            chats_id.push($(this).attr('id'))
        }
    })
    if (chats_id.length>0){
        $.ajax({
            url:'/chats/recovery/list',
            method:'PATCH',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(chats_id),
            success : function(result) {
                if (result["result"]==true){
                    get_chats_delete()
                }
                create_flash(result["category"],result["message"])
            },
            error: function(error){
                console.log(error);
                $('.loader').removeAttr('style');
            }
        })
    } 
}

function get_users(){
    $.ajax({
        url:'/users/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#table_block_users").empty()
                $.each(result.users, function(index,user){
                    role="Пользователь"
                    if(user.isAdmin==true){
                        role="Администратор"
                    }
                    $("#table_block_users").append("<tr class='table_body_element_block'><td class='table_element -table_body_element search_element'>"+user.login+"</td><td class='table_element -table_body_element'>"+user.user_name+"</td><td class='table_element -table_body_element'>"+role+"</td><td class='table_element_button -table_body_element'><button onclick='open_form_update()' class='update_button -button'>Изменить</button></td></tr>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function get_configs_ai(){
    $.ajax({
        url:'/configs/ai/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#table_block_ai").empty()
                $.each(result.configs_ai, function(index,config){
                    if (config.input_format=="textarea"){
                        input_element="<textarea class='textarea_value  -separete_main -input_separete'>"+config.value+"</textarea>"
                    }else if (config.input_format=="boolen"){
                        var checked_element=""
                        if (config.value==1){
                            checked_element="checked"
                        }
                        input_element="<input type='checkbox' class='input_value  -separete_main -input_separete' "+checked_element+">"
                    }else{
                        input_element="<input type="+config.input_format+" class='input_value  -separete_main -input_separete' value="+config.value+">"
                    }
                    $("#table_block_ai").append("<tr class='table_body_element_block'><td class='table_element -table_body_element'>"+config.name+"</td><td class='table_element -table_body_element'>"+config.about+"</td><td class='table_element -table_body_element'><form class='form_config -separete_block'>"+input_element+"<button class='button_save -separete_second -button_separete'>Сохранить</button></form></td></tr>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function get_configs(){
    $.ajax({
        url:'/configs/app/get',
        method:'GET',
        headers:{
            "Content-Type":"application/json",
            "Authorization": "Bearer "+get_token()
        },
        success : function(result) {
            if (result["result"]==false){
                window.location.href="/"
            }else{
                $("#table_block").empty()
                $.each(result.configs_ai, function(index,config){
                    if (config.input_format=="textarea"){
                        input_element="<textarea class='textarea_value  -separete_main -input_separete'>"+config.value+"</textarea>"
                    }else if (config.input_format=="boolen"){
                        var checked_element=""
                        if (config.value==1){
                            checked_element="checked"
                        }
                        input_element="<input type='checkbox' class='input_value  -separete_main -input_separete' "+checked_element+"></input>"
                    }else{
                        input_element="<input type="+config.input_format+" class='input_value  -separete_main -input_separete' value="+config.value+"></input>"
                    }
                    $("#table_block").append("<tr class='table_body_element_block'><td class='table_element -table_body_element'>"+config.name+"</td><td class='table_element -table_body_element'>"+config.about+"</td><td class='table_element -table_body_element'><form class='form_config -separete_block'>"+input_element+"<button class='button_save -separete_second -button_separete'>Сохранить</button></form></td></tr>")
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function file_read(event){
    event.preventDefault();
    file_send=$("#file")[0].files;
    if (file_send.length>0){
        formdata=new FormData()
        formdata.append('file',file_send[0])
        $(".main_nav").append("<span class='loader'></span>")
        $.ajax({
            url:'/AI/docs/read',
            method:'POST',
            data:formdata,
            processData: false,
            contentType: false,
            success : function(result) {
                $('#file_name_text').val(result['name'])
                $('#file_text').val(result['text'])
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
            }
        })
        $('.loader').remove();
        $("#file").val('')
    }
}

function send_text(event){
    event.preventDefault()
    text_name=$('#file_name_text').val()
    text=$('#file_text').val()
    if (text.length>0){
        $.ajax({
            url:'/AI/docs/read',
            method:'POST',
            data:{},
            success : function() {
                $('#file_name_text').val('')
                $('#file_text').val('')
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
            }
        })
        $('.loader').remove();
    }
}

function open_form_update(){
    $("#hide_form_update").show();
}
function close_form_update(){
    $("#hide_form_update").hide();
}