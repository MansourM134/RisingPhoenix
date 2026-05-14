from django.urls import path
from . import views

app_name = 'message'

urlpatterns = [
    path('', views.conversation_list_view, name='conversation_list_view'),
    path('start/<int:proposal_id>/', views.start_conversation_view, name='start_conversation_view'),
    path('<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail_view'),
    path(
    "conversations/<int:conversation_id>/messages-json/",
    views.conversation_messages_json_view,
    name="conversation_messages_json_view",
),
]
