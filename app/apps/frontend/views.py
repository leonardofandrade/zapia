from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from apps.chats.models import ChatAttachment, ChatMessage, ChatParticipant, ChatThread
from apps.subjects.models import Relationship, Subject


class DashboardView(TemplateView):
    template_name = "frontend/dashboard.html"


class SubjectsListView(TemplateView):
    template_name = "frontend/subjects_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subjects"] = Subject.objects.all().order_by("full_name")[:200]
        context["relationships"] = (
            Relationship.objects.select_related("from_subject", "to_subject")
            .all()
            .order_by("-created_at")[:200]
        )
        return context


class ChatsListView(TemplateView):
    template_name = "frontend/chats_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["threads"] = (
            ChatThread.objects.all().order_by("-created_at")[:200]
        )
        return context


class ChatDetailView(TemplateView):
    template_name = "frontend/chat_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_id = kwargs["chat_id"]
        chat = get_object_or_404(ChatThread, pk=chat_id)

        participants = {
            participant.id: participant
            for participant in ChatParticipant.objects.filter(chat=chat).all()
        }
        messages = (
            ChatMessage.objects.filter(chat=chat)
            .select_related("sender")
            .prefetch_related("attachments")
            .order_by("sequence_index")[:500]
        )
        attachments = (
            ChatAttachment.objects.filter(message__chat=chat)
            .select_related("message")
            .order_by("-created_at")[:200]
        )

        context["chat"] = chat
        context["participants"] = participants.values()
        context["messages"] = messages
        context["attachments"] = attachments
        return context
