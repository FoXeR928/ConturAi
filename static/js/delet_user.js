$('#button_del_user').click(function(){
    user_del=$(this).val();
    href_del='/admin/users/delet_user/'+user_del;
    window.location.href=href_del;
})