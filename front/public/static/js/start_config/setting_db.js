$('#sql_driver').on('change',function(){
    select=$(this).val()
    if (select=='sqlite'){
        $('.-hide').hide()
        $('.-local').show()
    }else if (select=='postgresql'){
        $('.-hide').hide()
        $('#sql_host').val('localhost')
        $('#sql_port').val(5432)
        $('.-server').show()
    }else if (select=='mysql'){
        $('.-hide').hide()
        $('#sql_host').val('localhost')
        $('#sql_port').val(3306)
        $('.-server').show()
    }
})
$("#send_settings").click(function(event){
    event.preventDefault();
    var app_port=$('#app_port').val()
    var sql_db=$('#sql_db').val()
    var sql_driver=$('#sql_driver').val()
    let db_data={
        "app_port": app_port,
        "sql_driver": sql_driver,
        "sql_host": null,
        "sql_port": null,
        "sql_db": sql_db,
        "sql_user": null,
        "sql_password": null,
        "db_path": null
      }
    if (sql_driver=="sqlite"){
        db_data["db_path"]=$('#db_path').val()
    }else{
        db_data["sql_host"]=$('#sql_host').val()
        db_data["sql_port"]=$('#sql_port').val()
        db_data["sql_user"]=$('#sql_user').val()
        db_data["sql_password"]=$('#sql_password').val()
    }
    $.ajax({
        url:'/config/app/start/create',
        method:'POST',
        headers:{
            "Content-Type":"application/json"
        },
        data:JSON.stringify(db_data),
        success : function(result) {
            console.log(result)
            $("#main").append("<div class='flash "+result["status"]+"'>"+result["message"]+"</div>")
            setTimeout(function(){
                $('.flash').remove();
              }, 300);
        },
        error: function(error){
            alert('Ошибка '+error)
            console.log(error);
        }
    })
})