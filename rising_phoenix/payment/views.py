from django.shortcuts import render, redirect, get_object_or_404
from .models import StripeCustomer, PaymentMethod
from django.conf import settings
from django.contrib import messages
import stripe
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY



def my_cards_view(request):

    cards = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'payment/my_cards.html', {'cards': cards})

def get_or_create_stripe_customer(user):
    customer_obj, created = StripeCustomer.objects.get_or_create(user=user)

    if customer_obj.stripe_customer_id:
        return customer_obj.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.username
    )
    customer_obj.stripe_customer_id = customer.id
    customer_obj.save()
    return customer.id



def add_card_view(request):

    stripe_customer_id = get_or_create_stripe_customer(request.user)
    setup_intent = stripe.SetupIntent.create(
        customer=stripe_customer_id,
        payment_method_types=['card'],
        usage='off_session'
    )

    return render(request, 'payment/add_card.html', {
        'client_secret': setup_intent.client_secret,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


def save_card_success(request):

    setup_intent_id = request.GET.get('setup_intent')
    if not setup_intent_id:
        return redirect('payment:add_card')

    setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
    payment_method_id = setup_intent.payment_method
    stripe_customer_id = setup_intent.customer
    payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

    obj, created = PaymentMethod.objects.get_or_create(
        stripe_payment_method_id=payment_method_id,
        defaults={
            'user': request.user,
            'stripe_customer_id': stripe_customer_id,
            'brand': payment_method.card.brand,
            'last4': payment_method.card.last4,
            'exp_month': payment_method.card.exp_month,
            'exp_year': payment_method.card.exp_year,
            'is_default': not PaymentMethod.objects.filter(user=request.user).exists(),
        }
    )

    return redirect('payment:my_cards')
