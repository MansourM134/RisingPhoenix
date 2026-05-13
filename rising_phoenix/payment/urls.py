from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('cards/', views.my_cards_view, name='my_cards'),
    path('cards/add/', views.add_card_view, name='add_card'),
    path('cards/success/', views.save_card_success, name='save_card_success'),
]