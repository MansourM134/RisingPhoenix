from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Conversation, Message
from proposal.models import Proposal

@login_required
def start_conversation_view(request: HttpRequest, proposal_id: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, id=proposal_id)

    requester = proposal.request.requester
    artisan = proposal.artisan

    if request.user != requester:
        messages.error(request, "You are not allowed to start this conversation.")
        return redirect('main:home_view')

    conversation, created = Conversation.objects.get_or_create(
        proposal=proposal,
        defaults={
            'requester': requester,
            'artisan': artisan,
        }
    )

    if created:
        messages.success(request, "Conversation started successfully.")

    return redirect('message:conversation_detail_view', conversation_id=conversation.id)


@login_required
def conversation_list_view(request: HttpRequest) -> HttpResponse:
    conversations = Conversation.objects.filter(
        Q(requester=request.user) | Q(artisan=request.user),
        is_active=True
    ).select_related(
        'proposal',
        'requester',
        'artisan'
    ).order_by('-updated_at')

    context = {
        'conversations': conversations,
    }
    return render(request, 'message/conversation_list.html', context)


@login_required
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in [conversation.requester, conversation.artisan]:
        return redirect('message:conversation_list_view')

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        image = request.FILES.get("image")

        if body or image:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body,
                image=image
            )
            return redirect('message:conversation_detail_view', conversation_id=conversation.id)

    conversation_messages = conversation.messages.select_related("sender").order_by("created_at")

    context = {
        "conversation": conversation,
        "conversation_messages": conversation_messages,
    }
    return render(request, "message/conversation_detail.html", context)


def conversation_messages_json_view(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    if request.user not in [conversation.requester, conversation.artisan]:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    messages = conversation.messages.select_related("sender").order_by("created_at")

    data = [
        {
            "id": msg.id,
            "body": msg.body,
            "sender_name": msg.sender.get_full_name() or msg.sender.username,
            "is_mine": msg.sender == request.user,
            "created_at": msg.created_at.strftime("%b %d, %Y %I:%M %p"),
            "image_url": msg.image.url if msg.image else "",
        }
        for msg in messages
    ]

    return JsonResponse({"messages": data})

