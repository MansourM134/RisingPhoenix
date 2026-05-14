from django.urls import path

from . import views

app_name = 'proposal'

urlpatterns = [
    path('submit/<int:request_id>/', views.submit_proposal_view, name='submit_proposal_view'),
    path('<int:proposal_id>/edit/', views.edit_proposal_view, name='edit_proposal_view'),
    path('<int:proposal_id>/withdraw/', views.withdraw_proposal_view, name='withdraw_proposal_view'),
    path('<int:proposal_id>/accept/', views.accept_proposal_view, name='accept_proposal_view'),
    path('<int:proposal_id>/reject/', views.reject_proposal_view, name='reject_proposal_view'),
    path('mine/', views.my_proposals_view, name='my_proposals_view'),
]
