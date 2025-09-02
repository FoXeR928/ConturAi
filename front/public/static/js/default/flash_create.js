function create_flash(flash_status,message){
    $("#main").prepend("<div class='flash "+flash_status+"'>"+message+"</div>")
    setTimeout(function(){
        $('.flash').remove();
    }, 4000);
}