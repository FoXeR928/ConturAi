var left_shift='-15.3%'

$('#button_nav').click(function(){
    if($('#header').css('left')!='0px'){
        $('#header').animate({
            left:'0'
        },400)
        $('main').animate({
            'margin-left':'19.3%'
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