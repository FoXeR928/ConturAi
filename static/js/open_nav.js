var left_shift='-245px'

$('#button_nav').click(function(){
    if($('#header').css('left')==left_shift){
        $('#header').animate({
            left:'0'
        },400)
        $('main').animate({
            'margin-left':'310px'
        },400)

    }
    else{
        $('#header').animate({
            left:left_shift,
        },400)
        $('main').animate({
            'margin-left':'75px'
        },400)
    }
})
$('.button_nav_open').click(function(){
    $(this).parent().parent().children('.nav_hide_block').slideToggle()
})