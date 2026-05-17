from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('cards/', views.my_cards_view, name='my_cards'),
    path('cards/add/', views.add_card_view, name='add_card'),
    path('cards/success/', views.save_card_success, name='save_card_success'),
    path('<int:proposal_id>/checkout/', views.proposal_checkout_view, name='proposal_checkout_view'),
    path('<int:proposal_id>/checkout/confirm/', views.confirm_proposal_payment_view, name='confirm_proposal_payment_view'),
    path('contract/<int:contract_id>/artisan/review/',views.artisan_contract_review_view,name='artisan_contract_review_view'),
    path('contract/<int:contract_id>/artisan/accept/',views.artisan_accept_contract_view,name='artisan_accept_contract_view'),

]