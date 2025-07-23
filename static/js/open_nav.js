var left_shift='-140px'

$('#button_nav').click(function(){
    if($('#header').css('left')==left_shift){
        $('#header').animate({
            left:'0'
        },400)
    }
    else{
        $('#header').animate({
            left:left_shift
        },400)
    }
})