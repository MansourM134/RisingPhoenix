from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_contract_pdf_bytes(contract):
    from weasyprint import HTML

    proposal = contract.proposal
    project_request = proposal.request

    html_string = render_to_string('payment/contract_pdf.html', {
        'contract': contract,
        'proposal': proposal,
        'project_request': project_request,
    })

    pdf_bytes = HTML(string=html_string, base_url=settings.BASE_DIR).write_pdf()
    return pdf_bytes


def send_contract_pdf_email(contract):
    proposal = contract.proposal
    project_request = proposal.request

    pdf_bytes = generate_contract_pdf_bytes(contract)

    recipients = [
        project_request.requester.email,
        proposal.artisan.email,
    ]
    recipients = [email for email in recipients if email]

    if not recipients:
        return

    from notification.utils import _logo_data_uri, _site_url
    site_url = _site_url()
    context = {
        'contract': contract,
        'proposal': proposal,
        'project_request': project_request,
        'site_url': site_url,
        'logo': _logo_data_uri(),
    }
    html_body = render_to_string('payment/contract_email.html', context)
    plain_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=f'Your Saaf contract for "{project_request.title}" is confirmed',
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.attach_alternative(html_body, 'text/html')
    email.attach(
        f'contract-{contract.id}.pdf',
        pdf_bytes,
        'application/pdf',
    )
    email.send(fail_silently=False)