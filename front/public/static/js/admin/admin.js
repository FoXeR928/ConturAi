function open_page(page){
    $(".pages").hide()
    $("#"+page).show()
    if (page.includes("chats")){
        get_chats_delete()
    }else if (page.includes("users")){
        get_users()
    }else if (page.includes("configs_ai")){
        get_configs_ai()
    }else if (page.includes("configs")){
        get_configs()
    }
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
                create_flash(result["category"],result["message"])
            }else{
                $("#chats").empty()
                $.each(result.chats, function(index,chat){
                    $("#chats_delete").append("<article class='chat_block -separete_block'><div class='text_block -separete_main'><p class='chat_name search_element_chats'>"+chat.chat_name+"</p><p class='chat_name search_element'>"+chat.user_login+"</p></div><div class='checkbox_container -separete_second -button_del_close'><input class='checkbox_chat' type='checkbox' name='select_chat' id="+chat.id+"></div></article>")
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
                create_flash(result["category"],result["message"])
            }else{
                $("#table_block_users").empty()
                $.each(result.users, function(index,user){
                    command="open_form_update('"+user.login+"')"
                    role="Пользователь"
                    if(user.isAdmin==true){
                        role="Администратор"
                    }
                    $("#table_block_users").append('<tr class="table_body_element_block"><td class="table_element -table_body_element search_element search_element_users">'+user.login+'</td><td class="table_element -table_body_element">'+user.user_name+'</td><td class="table_element -table_body_element">'+role+'</td><td class="table_element_button -table_body_element"><button onclick="'+command+'" class="update_button -button">Изменить</button></td></tr>')
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function create_user(){
    login=$("#registration_login").val()
    user_name=$("#registration_user_name").val()
    password=$("#registration_password").val()
    password_checked=$("#registration_password_check").val()
    data_user={"login":login,"user_name":user_name,"password":password}
    if (login!="" && password!="" && password.length>=8 && password==password_checked){
        $.ajax({
            url:'/users/registration',
            method:'POST',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(data_user),
            success : function(result) {
                create_flash(result["category"],result["message"])
                get_users()
                close_form()
            },
            error: function(error){
                console.log(error);
                window.location.href="/"
            }
        })
        $("#registration_login").val("")
        $("#registration_user_name").val("")
        $("#registration_password").val("")
        $("#registration_password_check").val("")
    }
}


function update_user(){
    login=$("#update_login").val()
    user_role=$("#update_user_role").val()
    password=$("#update_password").val()
    password_checked=$("#update_password_check").val()
    if (login!="" && password!="" && password.length>=8 && password==password_checked){
        data_user={"login":login,"password":password}
        $.ajax({
            url:'/users/change/password',
            method:'PATCH',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(data_user),
            success : function(result) {
                create_flash(result["category"],result["message"])
                close_form_update()
            },
            error: function(error){
                console.log(error);
                window.location.href="/"
            }
        })
        $("#update_login").val("")
        $("#update_password").val("")
        $("#update_password_check").val("")
    }
    if (user_role!=null){
        if (user_role==1){
            user_role_add=true
        }else{
            user_role_add=false
        }
        data_user={"login":login,"isAdmin":user_role_add}
        $.ajax({
            url:'/users/change/role',
            method:'PATCH',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(data_user),
            success : function(result) {
                create_flash(result["category"],result["message"])
                close_form_update()
            },
            error: function(error){
                console.log(error);
                window.location.href="/"
            }
        })
    }
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
                create_flash(result["category"],result["message"])
            }else{
                $("#table_block_ai").empty()
                $.each(result.configs_ai, function(index,config){
                    command="update_config_ai('"+config.name+"','"+config.input_format+"')"
                    if (config.input_format=="textarea"){
                        input_element="<textarea class='textarea_value  -separete_main -input_separete' id='"+config.name+"'>"+config.value+"</textarea>"
                    }else if (config.input_format=="boolen"){
                        var checked_element=""
                        if (config.value==1){
                            checked_element="checked"
                        }
                        input_element="<input type='checkbox' class='input_value  -separete_main -input_separete' id='"+config.name+"' "+checked_element+">"
                    }else{
                        input_element="<input type="+config.input_format+" class='input_value  -separete_main -input_separete' id='"+config.name+"' value="+config.value+">"
                    }
                    $("#table_block_ai").append('<tr class="table_body_element_block"><td class="table_element -table_body_element search_element_configs_ai">'+config.name+'</td><td class="table_element -table_body_element">'+config.about+'</td><td class="table_element -table_body_element -separete_block">'+input_element+'<button class="button_save -separete_second -button_separete" onclick="'+command+'">Сохранить</button></td></tr>')
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function set_configs_ai(){
    model_chunk=$("#set_model_chunk").val()
    model=$("#set_model").val()
    collection=$("#set_collection").val()
    rag_host=$("#set_rag_host").val()
    rag_port_http=$("#set_rag_port_http").val()
    rag_port_grpc=$("#set_rag_port_grpc").val()
    rag_grpc=$("#set_rag_grpc").prop("checked")
    data_ai={"model_chunk":model_chunk,"model":model,"collection":collection,"rag_host":rag_host,"rag_port_http":rag_port_http,"rag_port_grpc":rag_port_grpc,"rag_grpc":rag_grpc}
    if(model_chunk!="" && model!="" && collection!="" && rag_host!="" && rag_port_http!="" && rag_port_grpc!=""){
        $.ajax({
            url:'/configs/ai/start/create',
            method:'POST',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify(data_ai),
            success : function(result) {
                create_flash(result["category"],result["message"])
                get_configs_ai()
                close_form_config()
            },
            error: function(error){
                console.log(error);
                window.location.href="/"
            }
        })
        model_chunk=$("#set_model_chunk").val("")
        model=$("#set_model").val("")
        collection=$("#set_collection").val("")
        rag_host=$("#set_rag_host").val("")
        rag_port_http=$("#set_rag_port_http").val("")
        rag_port_grpc=$("#set_rag_port_grpc").val("")
    }
}

function update_config_ai(config,format){
    get_config=$("#"+config).val()
    if (format=="boolen"){
        get_config=$("#"+config).prop("checked")
    }
    if (get_config!=""){
        $.ajax({
            url:'/configs/ai/update',
            method:'PATCH',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify({"name":config,"value":get_config}),
            success : function(result) {
                create_flash(result["category"],result["message"])
                get_configs_ai()
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
            }
        })
    }
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
                create_flash(result["category"],result["message"])
            }else{
                $("#table_block").empty()
                $.each(result.configs_ai, function(index,config){
                    command="update_config('"+config.name+"','"+config.input_format+"')"
                    if (config.input_format=="textarea"){
                        input_element="<textarea class='textarea_value  -separete_main -input_separete' id='"+config.name+"'>"+config.value+"</textarea>"
                    }else if (config.input_format=="boolen"){
                        var checked_element=""
                        if (config.value==1){
                            checked_element="checked"
                        }
                        input_element="<input type='checkbox' class='input_value  -separete_main -input_separete' id='"+config.name+"' "+checked_element+"></input>"
                    }else{
                        input_element="<input type="+config.input_format+" class='input_value  -separete_main -input_separete' id='"+config.name+"' value="+config.value+"></input>"
                    }
                    $("#table_block").append('<tr class="table_body_element_block"><td class="table_element -table_body_element search_element_configs">'+config.name+'</td><td class="table_element -table_body_element">'+config.about+'</td><td class="table_element -table_body_element -separete_block">'+input_element+'<button class="button_save -separete_second -button_separete" onclick="'+command+'">Сохранить</button></td></tr>')
                })
            }
        },
        error: function(error){
            console.log(error);
            window.location.href="/"
        }
    })
}

function update_config(config,format){
    get_config=$("#"+config).val()
    if (format=="boolen"){
        get_config=$("#"+config).prop("checked")
    }
    if (get_config!=""){
        $.ajax({
            url:'/configs/app/update',
            method:'PATCH',
            headers:{
                "Content-Type":"application/json",
                "Authorization": "Bearer "+get_token()
            },
            data:JSON.stringify({"name":config,"value":get_config}),
            success : function(result) {
                create_flash(result["category"],result["message"])
                get_configs()
            },
            error: function(error){
                alert('Ошибка '+error)
                console.log(error);
            }
        })
    }
}

function file_read(){
    file_send=$("#file")[0].files;
    if (file_send.length>0){
        formdata=new FormData()
        formdata.append('doc',file_send[0])
        $(".main_nav").append("<span class='loader'></span>")
        $.ajax({
            url:'/AI/docs/read',
            method:'POST',
            headers:{
                "Authorization": "Bearer "+get_token()
            },
            data:formdata,
            processData: false,
            contentType:false,
            success : function(result) {
                if (result["result"]==false){
                    create_flash(result["category"],result["message"])
                }else{
                    $('#file_name_text').val(result['file_name'])
                    $('#file_text').val(result['file_text'])
                    create_flash(result["category"],result["message"])
                }
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

function open_form_update(user){
    $("#update_login").val(user)
    $("#hide_form_update").show();
}
function close_form_update(){
    $("#update_login").val("")
    $("#update_user_role").val("")
    $("#update_password").val("")
    $("#update_password_check").val("")
    $("#hide_form_update").hide();
}
function open_form_config(){
    $("#hide_form_config").show();
}
function close_form_config(){
    $("#hide_form_config").hide();
}