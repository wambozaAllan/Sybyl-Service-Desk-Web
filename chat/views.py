from django.http import HttpResponse
from django.template import loader

from django.shortcuts import render

from django.db.models import Q
from .models import User, DirectChatMessage, DirectChat


def direct_message_pane(request):
    return render(request, 'chat/direct_message_pane.html', {})


def search_company_chat_users(request):
    search_value = request.GET.get('searchValue')
    company_id = request.session['company_id']
    users = User.objects.filter(
        (Q(first_name__icontains=search_value) | Q(last_name__icontains=search_value)) & Q(company=company_id))

    template = loader.get_template('chat/user_search_results.html')
    context = {
        'users': users,
        'search_value': search_value,
    }

    return HttpResponse(template.render(context, request))


def direct_message_chat_room(request):
    uid = request.GET.get('uid')
    fname = request.GET.get('fname')
    username = request.GET.get('username')
    current_uid = request.user.id
    direct_chat_id = DirectChat.objects.filter((Q(sender=current_uid) & Q(receiver=uid)) | (Q(sender=uid) & Q(receiver=current_uid))).values('id').first()

    obj_msg = DirectChatMessage.objects.filter(direct_chat_id=direct_chat_id['id'])

    template = loader.get_template('chat/direct_message_chat_room.html')
    context = {
        'msg': obj_msg,
        'fullname': fname,
        'username': username,
        'uid': uid,
        'direct_chat_id': direct_chat_id['id'],
    }

    return HttpResponse(template.render(context, request))


def delete_direct_msg(request):
    chat_id = request.GET.get('chat_id')
    uid = request.GET.get('receiver_uid')
    fname = request.GET.get('receiver_fullname')
    username = request.GET.get('receiver_username')
    direct_chat_id = int(request.GET.get('direct_chat_id'))

    DirectChatMessage.objects.filter(id=int(chat_id)).delete()
    obj_msg = DirectChatMessage.objects.filter(direct_chat_id=direct_chat_id)

    template = loader.get_template('chat/direct_message_chat_room.html')
    context = {
        'msg': obj_msg,
        'fullname': fname,
        'username': username,
        'uid': uid,
        'direct_chat_id': direct_chat_id,
    }

    return HttpResponse(template.render(context, request))
