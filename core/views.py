# core/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Message
import json

@login_required
def home(request):
    users = User.objects.exclude(id=request.user.id)
    unread_counts = {
        user.id: Message.objects.filter(sender=user, receiver=request.user, is_read=False).count()
        for user in users
    }
    return render(request, 'core/home.html', {
        'users': users,
        'unread_counts': unread_counts
    })

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('timestamp')

    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    return render(request, 'core/chat.html', {
        'other_user': other_user,
        'messages': messages
    })

@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        sender = request.user
        receiver_id = request.POST.get('receiver_id')
        message_text = request.POST.get('message')

        if not receiver_id or not message_text:
            return JsonResponse({'status': 'error', 'message': 'Missing fields'})

        receiver = get_object_or_404(User, id=receiver_id)

        msg = Message.objects.create(
            sender=sender,
            receiver=receiver,
            message=message_text
        )

        return JsonResponse({
            'status': 'success',
            'message': msg.message,
            'id': msg.id,
             'timestamp': msg.timestamp.isoformat()
             
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def fetch_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('timestamp')

    data = [
        {
            'id': msg.id,
            'sender': msg.sender.id,
            'message': msg.message,
            'is_read': msg.is_read,
            'timestamp': msg.timestamp.isoformat() 
        }
        for msg in messages
    ]

    return JsonResponse({'messages': data})

@csrf_exempt
@login_required
def delete_messages(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('message_ids', [])
            Message.objects.filter(id__in=ids, sender=request.user).delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid method'})


