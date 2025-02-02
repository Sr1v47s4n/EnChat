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
    # decrypt the messages
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
def chat(request, slug):
    """Retrieve all messages between the user and the selected user"""
    user = request.user
    receiver = get_object_or_404(User, slug=slug)

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
            ),  # Handle empty messages
            "timestamp": message.timestamp,  # Format timestamp
            "is_read": message.is_read,
            "read_at": (message.read_at if message.read_at else None),
        }
        for message in messages
    ]

    return render(
        request, "chat/chat.html", {"receiver": receiver, "messages": messages}
    )


@login_required
def get_messages(request, slug):
    """AJAX endpoint for getting messages"""
    user = request.user
    receiver = get_object_or_404(User, slug=slug)
    last_id = request.GET.get("last_id", 0)

    # Get messages after last_id
    messages = PrivateMessage.objects.filter(
        Q(
            Q(sender=user) & Q(receiver=receiver)
            | Q(sender=receiver) & Q(receiver=user)
        ),
        id__gt=last_id,
    ).order_by("timestamp")

    # Mark unread messages as read
    unread_messages = messages.filter(receiver=user, is_read=False)
    unread_messages.update(is_read=True, read_at=timezone.now())

    # Refresh messages to get updated read status
    messages = messages.all()

    # Serialize messages
    serialized = [
        {
            "id": m.id,
            "sender": m.sender.username,
            "message": decrypt_message(m.encrypted_message),
            "timestamp": m.timestamp,
            "is_read": m.is_read,
            "read_at": m.read_at if m.read_at else None,
        }
        for m in messages
    ]

    return JsonResponse({"messages": serialized})


@login_required
def send_message(request, slug):
    """Handle message sending via AJAX"""
    if request.method == "POST":
        receiver = get_object_or_404(User, slug=slug)
        message_text = request.POST.get("message", "").strip()

        # Create and save message

        message = PrivateMessage.objects.create(
            sender=request.user, receiver=receiver, encrypted_message=message_text
        )

        # Return created message data
        return JsonResponse(
            {
                "success": True,
                "message": {
                    "id": message.id,
                    "sender": request.user.username,
                    "message": message_text,
                    "timestamp": message.timestamp,
                    "is_read": False,
                },
            }
        )
    return JsonResponse({"success": False}, status=405)


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
