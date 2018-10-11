var chat_socket = null;

function initSocket(room_slug, scrollItem) {
    var chat_room = $('.chat-room');
    var chat_room_header = chat_room.find('h3');
    var chat_room_user_count = chat_room.find('.user-count');
    var messages_wrapper = chat_room.find('.message-list');
    var message_input = chat_room.find('.message-input');
    var message_submit = chat_room.find('.send-message');
    var leave_room = chat_room.find('#leave-room');
    var chat_room_members = $('.chat-room-members');
    var member_list_wrapper = chat_room_members.find('.member-list-wrapper');
    var member_form = chat_room_members.find('.form-wrapper');
    var chat_room_members_footer = $('.chat-room-members footer');
    var user_typing = chat_room.find('#user-typing');
    var current_username = messages_wrapper.data('current-username');
    var room_action = chat_room.find('.room-action');
    var room_id = null;

    var chat_url = '/ws/chat/' + room_slug + '/';
    var ws_protocol = window.location.protocol == 'https:' ? 'wss://' : 'ws://';

    var socket_endpoint = ws_protocol + window.location.host + chat_url;
    var socket = new WebSocket(socket_endpoint);

    socket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        var type = data['type'];

        if (type == 'room_properties') {
            handleRoomProperties(data);
        } else if (type == 'user_typing') {
            handleUserTyping(data);
        } else if (type == 'room_members') {
            handleRoomMembers(data);
        } else if (type == 'new_room') {
            handleNewRoom(data);
        } else {
            handleMessage(data, type);
        }
    };

    socket.onopen = function (e) {
        console.log('Chat socket opened at ' + socket_endpoint);
        messages_wrapper.html('');
    };

    socket.onclose = function (e) {
        console.log('Chat socket closed');
        //alert('Chat error, try to reload the page');
    };

    function handleRoomProperties(data) {
        room_id = data['room_id'];
        chat_room_header.html(data['room_name']);

        var user_count = data['user_count'];
        var localized_message = ngettext('member', 'members', user_count);
        chat_room_user_count.html(user_count + ' ' + localized_message);

        if (data['is_user_to_user']) {
            leave_room.hide();
        } else {
            leave_room.show();
        }

        var rel_room = 'room-' + room_id;
        var room_list_wrapper = $('#page-chat #pills-rooms');
        if (room_list_wrapper.length) {
            var room_item = room_list_wrapper.find('[rel=' + rel_room + ']');
            if (room_item.length === 0) {
                var room_item_template = room_list_wrapper.find('.chat-item-template').clone(true);
                room_item_template = room_item_template.clone(true);
                room_item_template.html(room_item_template.html().replace('room-name-placeholder', data['room_name']));
                room_item_template.html(room_item_template.html().replace('room-modified-placeholder', data['room_modified']));
                room_item_template.html(room_item_template.html().replace('room-slug-placeholder', data['room_slug']));
                room_item_template.removeClass("chat-item-template");
                room_item_template.attr('rel', rel_room);
                room_list_wrapper.prepend(room_item_template);
            }
        }
    }

    function handleNewRoom(data) {
        var slug = data['slug'];

        hideRoomMembers();

        if (chat_socket) {
            chat_socket.close();
        }
        chat_socket = initSocket(slug, null);
    }

    function handleUserTyping(data) {
        var username = data['username'];
        if (current_username != username) {
            user_typing.html(data['text']);
            if (!user_typing.is(":visible")) {
                user_typing.animate({opacity: 1}, 500);
            } else {
                user_typing.stop(true);
                user_typing.animate({opacity: 1}, 0);
            }
            user_typing.animate({opacity: 0}, 3000);
        }
    }

    function handleRoomMembers(data) {
        member_form.html('');
        member_list_wrapper.html('');

        var members = data['members'];
        members.forEach(function (member) {
            member_list_wrapper.append(member['html']);
        });
        member_form.append(data['form']);

        var event = $.Event('whisper.form.attached');
        event.selector = '.chat-room-members .form-wrapper';
        $(window).trigger(event);
    }

    function handleMessage(data, type) {
        var message = data['message'];
        var username = data['username'];
        var timestamp = data['timestamp'];
        var message_class = 'message';
        if (current_username == username) {
            message_class = 'my message';
        } else if (username == null) {
            message_class = 'system message';
            username = 'System';
        }

        messages_wrapper.append('<div class="' + message_class + '"><span>' + message + '</span><small>' + username + ', ' + timestamp + '</small></div>');

        scrollDownChat(type == 'chat_message', scrollItem);
    }

    function sendMessage() {
        var message = message_input.val().trim();

        if (message.length > 0) {
            if (socket.readyState === socket.OPEN) {
                socket.send(JSON.stringify({
                    'message': message
                }));
                message_input.val('').trigger("input.autoExpand");
            } else {
                alert('Chat error, try to reload the page');
            }
        }
    }

    function sendUserTyping() {
        if (socket.readyState === socket.OPEN) {
            socket.send(JSON.stringify({
                'type': 'user_typing'
            }));
        }
    }

    function leaveRoom() {
        socket.send(JSON.stringify({
            'type': 'leave_room'
        }));
        $('[rel=room-' + room_id + ']').remove();
    }

    message_input.focus();
    message_input.unbind('keyup');
    message_input.on('keyup', function (e) {
        if (e.keyCode === 13 && !e.shiftKey) {  // enter, return, without shift
            sendMessage();
        } else {
            sendUserTyping();
        }
    });

    message_submit.unbind('click');
    message_submit.on('click', function (e) {
        sendMessage();
    });

    leave_room.unbind('click');
    leave_room.on('click', function (e) {
        leaveRoom();
        hideChatRoom(socket);
    });

    room_action.unbind('click');
    room_action.click(function (e) {
        var url = $(this).data('url');
        url = url.replace('-slug-placeholder-', room_slug);
        $(this).attr('href', url);
    });

    chat_room_members.unbind('click');
    chat_room_members.on('click', '.remove-member', function (event) {
        socket.send(JSON.stringify({
            'type': 'remove_member',
            'user_id': $(this).data('user-id')
        }));
        $(this).closest('.chat-item').remove();

        event.preventDefault();
    });


    chat_room_members_footer.unbind('click');
    chat_room_members_footer.on('click', 'button', function (event) {
        var member_select = member_form.find('select');

        if (Array.isArray(member_select.val()) && member_select.val().length) {
            if (socket.readyState === socket.OPEN) {
                socket.send(JSON.stringify({
                    'type': 'add_members',
                    'user_ids': member_select.val()
                }));
                member_select.val('')
            } else {
                alert('Chat error, try to reload the page');
            }
        }

        event.preventDefault();
    });


    return socket;
}

function initChat() {
    chat_socket = null;

    $('#chat-channels-show').click(function (event) {
        $('#page-chat').addClass("show");
        $('.chat-channels').addClass("show");
        event.preventDefault();
    });

    $('#chat-channels-hide').click(function (event) {
        $('#page-chat').removeClass("show");
        $('.chat-channels').removeClass("show");
        event.preventDefault();
    });

    $('body').on('click', '.chat-room-show', function (event) {
        $('#page-chat').addClass("show");
        $('.chat-room').addClass("show");
        $('.chat-channels').removeClass("show");

        var room_slug = $(this).data('room-slug');

        if (room_slug) {
            if (chat_socket) {
                chat_socket.close();
            }

            chat_socket = initSocket(room_slug, null);
        }

        event.preventDefault();
    });

    $('#chat-room-hide').click(function (event) {
        hideChatRoom(chat_socket);
        event.preventDefault();
    });

    $('.chat-room-members-show').click(function (event) {
        $('.chat-room-members').addClass("show");
        $('.chat-room').addClass("hide-left");

        if (chat_socket) {
            chat_socket.send(JSON.stringify({
                'type': 'room_members'
            }));
        }
        event.preventDefault();
    });

    $('#chat-room-members-hide').click(function (event) {
        hideRoomMembers();
        event.preventDefault();
    });

    initHideOnEsc()
}

function initUnreadChatMessagesSocket() {
    var unread_chat_messages = $('.unread-chat-messages');
    var unread_chat_rooms = $('.unread-chat-rooms');
    var socket_url = '/ws/chat/unread-messages/';
    var ws_protocol = window.location.protocol == 'https:' ? 'wss://' : 'ws://';

    var socket_endpoint = ws_protocol + window.location.host + socket_url;
    var socket = new ReconnectingWebSocket(socket_endpoint, null, {reconnectInterval: 3000});

    socket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        var unread_messages = data['unread_messages'];
        var unread_rooms = data['unread_rooms'];

        if (unread_messages == 0) {
            unread_messages = '';
        }

        unread_chat_messages.html(unread_messages);

        if (unread_rooms.length == 0) {
            unread_chat_rooms.html('');
        } else {
            unread_chat_rooms.html(unread_rooms.length);
        }

        $('#pills-rooms .chat-item').removeClass('has-unread-messages');

        $.each(unread_rooms, function (index, room) {
            var selector = '#pills-rooms .chat-item[rel="room-' + room['pk'] + '"]';
            var chat_item = $(selector);
            chat_item.addClass('has-unread-messages');
            chat_item.find('.badge').html(room['unread_messages']);
        });
    };

    socket.onopen = function (e) {
        console.log('Unread chat messages socket opened at ' + socket_endpoint);
    };

    socket.onclose = function (e) {
        console.error('Unread chat messages socket closed');
        //alert('Chat error, try to reload the page');
    };

    return socket;
}

function scrollDownChat(animated, scrollItem) {
    if (scrollItem == null) {
        scrollItem = $('.chat-room .message-list-wrapper');
    }

    if (animated) {
        scrollItem.animate({scrollTop: scrollItem.prop("scrollHeight")}, 1000);
    } else {
        scrollItem.scrollTop(scrollItem[0].scrollHeight);
    }
}


function hideChatRoom(socket) {
    var chat_room_title = $('.chat-room h3');
    var messages_wrapper = $('.chat-room .message-list');

    $('.chat-room').removeClass("show");
    $('.chat-channels').addClass("show");
    messages_wrapper.html('');
    chat_room_title.html('');

    if (socket) {
        socket.close();
    }
}

function hideRoomMembers() {
    $('.chat-room-members').removeClass("show");
    $('.chat-room').removeClass("hide-left");
}

function initHideOnEsc() {
    if ($('#page-chat').length) {
        $('body').on('keyup', function (e) {
            if (e.keyCode === 27) {  // esc
                hideOnEsc();
            }
        });
    }
}

function hideOnEsc() {
    if ($('.chat-room-members.show').length) {
        hideRoomMembers();
    } else if ($('.chat-room.show').length) {
        hideChatRoom(chat_socket);
    } else if ($('#page-chat.show').length) {
        $('#page-chat').removeClass('show');
    }
}
