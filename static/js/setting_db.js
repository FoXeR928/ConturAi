$('#db_select').on('change',function(){
    select=$(this).val()
    if (select=='sqlite'){
        $('.-hide').hide()
        $('.-hide').val('')
        $('#db_path').val('../instance/db.db')
        $('#db_server').val('-')
        $('#db_port').val(1)
        $('#db_user').val('-')
        $('#db_password').val('-')
        $('#db_name').val('-')
        $('.-local').show()
    }else if (select=='postgres'){
        $('.-hide').hide()
        $('.-hide').val('')
        $('#db_path').val('-')
        $('#db_server').val('localhost')
        $('#db_port').val(5432)
        $('#db_name').val('ragi_db')
        $('.-server').show()
    }
})