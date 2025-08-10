$('#search').on('input',function(){
    search=$(this).val();
    $('.search_element').each(function(){
        if (($(this).text()).includes(search)!=true){
            $(this).parent().hide();
        }
    })
    if(search==''){
        $('.search_element').parent().show()
    }
})