var pressTimer;

$("#password-show").mouseup(function(){
	clearTimeout(pressTimer);
    $('.-password').attr('type', 'password');
    $("#password-show").removeClass('view');
}).mousedown(function(){
    pressTimer = window.setInterval(function() {
        $('.-password').attr('type', 'text');
        $("#password-show").addClass('view')
	}, 100);
}).mouseout(function(){
    clearTimeout(pressTimer);
    $('.-password').attr('type', 'password');
    $("#password-show").removeClass('view');
})