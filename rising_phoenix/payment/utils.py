from io import BytesIO
from textwrap import wrap

from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _draw_wrapped_text(pdf, text, x, y, max_chars=95, line_height=16):
    if not text:
        return y

    for paragraph in str(text).splitlines():
        lines = wrap(paragraph, width=max_chars) or ['']
        for line in lines:
            pdf.drawString(x, y, line)
            y -= line_height
        y -= 4
    return y


def generate_contract_pdf(contract):
    proposal = contract.proposal
    project_request = proposal.request

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 50
    y = height - 50

    pdf.setTitle(f"Contract #{contract.id}")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(x, y, f"Project Contract #{contract.id}")
    y -= 30

    pdf.setFont("Helvetica", 10)
    pdf.drawString(x, y, f"Status: {contract.status}")
    y -= 16
    pdf.drawString(x, y, f"Requester accepted at: {contract.requester_accepted_at}")
    y -= 16
    pdf.drawString(x, y, f"Artisan accepted at: {contract.artisan_accepted_at}")
    y -= 28

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x, y, "Requester")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        x, y,
        f"{project_request.requester.get_full_name() or project_request.requester.username}"
    )
    y -= 16
    pdf.drawString(x, y, f"Username: @{project_request.requester.username}")
    y -= 16
    if project_request.requester.email:
        pdf.drawString(x, y, f"Email: {project_request.requester.email}")
        y -= 24
    else:
        y -= 8

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x, y, "Artisan")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        x, y,
        f"{proposal.artisan.get_full_name() or proposal.artisan.username}"
    )
    y -= 16
    pdf.drawString(x, y, f"Username: @{proposal.artisan.username}")
    y -= 16
    if proposal.artisan.email:
        pdf.drawString(x, y, f"Email: {proposal.artisan.email}")
        y -= 24
    else:
        y -= 8

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x, y, "Request Details")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(x, y, f"Title: {project_request.title}")
    y -= 16
    pdf.drawString(x, y, f"Category: {project_request.category.name}")
    y -= 16
    if project_request.budget_max:
        pdf.drawString(x, y, f"Budget: {project_request.budget_max} SAR")
        y -= 16
    if project_request.deadline:
        pdf.drawString(x, y, f"Deadline: {project_request.deadline}")
        y -= 16

    pdf.drawString(x, y, "Description:")
    y -= 16
    y = _draw_wrapped_text(pdf, project_request.description, x + 10, y)

    y -= 10
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x, y, "Proposal Details")
    y -= 18

    pdf.setFont("Helvetica", 11)
    pdf.drawString(x, y, f"Price: {proposal.price} SAR")
    y -= 16
    pdf.drawString(x, y, f"Estimated completion: {proposal.estimated_days} day(s)")
    y -= 16
    pdf.drawString(x, y, "Proposal message:")
    y -= 16
    y = _draw_wrapped_text(pdf, proposal.message, x + 10, y)

    y -= 10
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x, y, "Payment")
    y -= 18

    pdf.setFont("Helvetica", 11)
    escrow_payment = getattr(contract, 'escrow_payment', None)
    if escrow_payment:
        pdf.drawString(x, y, f"Payment status: {escrow_payment.status}")
        y -= 16
        pdf.drawString(x, y, f"Captured: {'Yes' if escrow_payment.captured else 'No'}")
        y -= 16

    pdf.showPage()
    pdf.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def send_contract_pdf_email(contract):
    proposal = contract.proposal
    project_request = proposal.request

    pdf_bytes = generate_contract_pdf(contract)

    recipients = [project_request.requester.email, proposal.artisan.email]
    recipients = [email for email in recipients if email]

    if not recipients:
        return

    email = EmailMessage(
        subject=f"Contract #{contract.id} accepted",
        body=(
            f'The contract for "{project_request.title}" has been accepted by both parties.\n\n'
            f'Please find the contract PDF attached.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.attach(
        f'contract-{contract.id}.pdf',
        pdf_bytes,
        'application/pdf'
    )
    email.send(fail_silently=False)