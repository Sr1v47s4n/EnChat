from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, F, Subquery, OuterRef, Max, Case, When
from django.utils import timezone
from .models import PrivateMessage
from users.models import User
from utils import encrypt_message, decrypt_message


@login_required
def conversations(request):
    """
    Retrieve unique conversations with properly formatted latest messages
    """
    user = request.user

    # Get all conversations where the user is either sender or receiver
    subquery = PrivateMessage.objects.filter(
        Q(sender=OuterRef("sender"), receiver=OuterRef("receiver"))
        | Q(sender=OuterRef("receiver"), receiver=OuterRef("sender"))
    ).order_by("-timestamp")

    # Get unique conversations with latest message
    conversations = (
        PrivateMessage.objects.filter(Q(sender=user) | Q(receiver=user))
        .annotate(
            latest_id=Subquery(subquery.values("id")[:1]),
            other_user_id=Case(
                When(sender=user, then="receiver_id"),
                default="sender_id",
            ),
        )
        .filter(id=F("latest_id"))
        .select_related("sender", "receiver")
        .order_by("sender", "receiver", "-timestamp")
        .distinct("sender", "receiver")
    )
    #decrypt the messages
    for conversation in conversations:
        conversation.encrypted_message = decrypt_message(conversation.encrypted_message)
    return render(
        request,
        "chat/conversations.html",
        {
            "conversations": conversations,
            "no_conversations": not conversations.exists(),
        },
    )


@login_required
def chat(request, receiver_id):
    """Retrieve all messages between the user and the selected user"""
    user = request.user
    receiver = get_object_or_404(User, id=receiver_id)

    messages = PrivateMessage.objects.filter(
        Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user)
    ).order_by("timestamp")
    unread_messages = messages.filter(receiver=user, is_read=False)
    unread_messages.update(is_read=True, read_at=timezone.now())
    messages = [
        {
            "id": message.id,
            "sender": message.sender.username,  # Convert to string
            "receiver": message.receiver.username,  # Convert to string
            "message": (
                decrypt_message(message.encrypted_message)
                if message.encrypted_message
                else ""
            ),  # Handle empty messages
            "timestamp": message.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # Format timestamp
            "is_read": message.is_read,
            "read_at": (
                message.read_at.strftime("%Y-%m-%d %H:%M:%S")
                if message.read_at
                else None
            ),
        }
        for message in messages
    ]

    return render(
        request, "chat/chat.html", {"receiver": receiver, "messages": messages}
    )


@login_required
def send_message(request, receiver_id):
    """Send a message to the selected user"""
    user = request.user
    receiver = User.objects.get(id=receiver_id)

    if request.method == "POST":
        message = request.POST.get(
            "message", ""
        ).strip()  # Ensure message is a string and trim spaces

        if not message:  # Check if message is empty or None
            return JsonResponse({"success": False, "error": "Message cannot be empty"})

        PrivateMessage.objects.create(
            sender=user, receiver=receiver, encrypted_message=encrypt_message(message)
        )
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def read_message(request, message_id):
    """Mark a message as read"""
    message = get_object_or_404(PrivateMessage, id=message_id)
    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    return JsonResponse({"success": True, "is_read": message.is_read})


@login_required
def delete_message(request, message_id):
    """Delete a message"""
    message = get_object_or_404(PrivateMessage, id=message_id)
    message.delete()
    return JsonResponse({"success": True})


@login_required
def search_user(request):
    """Search for a user"""
    if request.method == "POST":
        username = request.POST.get("username")
        users = User.objects.filter(username__icontains=username)
        return render(request, "chat/search_user.html", {"users": users})
    # make sure it is not returning the id of the user signed in
    users = User.objects.filter(is_private=False).exclude(id=request.user.id)
    
    return render(request, "chat/search_user.html", {"users": users})


@login_required
def get_users(request):
    """Retrieve all users"""
    users = User.objects.filter(is_private=False)
    return render(request, "chat/users.html", {"users": users})
