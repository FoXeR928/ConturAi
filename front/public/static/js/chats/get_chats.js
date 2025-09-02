<article class="chat_block -separete_block">
    <a class="chat_name -separete_main search_element" href="{{url_for('chats.get_chat_api', chat=chat_id)}}">{{chat_name}}</a>
    <a class="button_del_chat -button_del_close -separete_second" href="{{url_for('chats.delet_chat_api', chat=chat_id)}}">Удалить</a>
</article>
<a class="nav_interior_element -button" href="{{url_for('chats.get_chat_api', chat=chat_id)}}">{{chat_name}}</a>