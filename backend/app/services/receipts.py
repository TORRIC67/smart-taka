"""Turns a completed Payment into a downloadable PDF receipt."""
from fpdf import FPDF


def build_receipt_pdf(payment, customer, provider_name: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Smart Taka", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Payment Receipt", ln=True, align="C")
    pdf.ln(8)

    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    rows = [
        ("Receipt No.", payment.order_id),
        ("Customer", customer.full_name),
        ("Phone", customer.phone),
        ("Zone", provider_name),
        ("Billing period", payment.billing_period),
        ("Amount paid", f"TZS {payment.amount:,}"),
        ("Payment date", payment.completed_at.strftime("%d %b %Y, %H:%M") if payment.completed_at else "-"),
        ("Status", payment.status.upper()),
    ]
    pdf.set_font("Helvetica", "", 12)
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(55, 9, label, border=0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 9, str(value), ln=True)

    pdf.ln(12)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, "Thank you for using Smart Taka waste collection services.", align="C")

    return bytes(pdf.output())
