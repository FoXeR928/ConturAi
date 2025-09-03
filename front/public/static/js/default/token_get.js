function get_token(){
    var token = document.cookie.match(/token=(.+?)(;|$)/);
    return token[1]
}