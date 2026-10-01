"""PDF versions of admin reports - downloadable and printable from the browser's PDF viewer."""
from fpdf import FPDF


def _header(pdf: FPDF, subtitle: str) -> None:
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Smart Taka", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, subtitle, ln=True, align="C")
    pdf.ln(6)


def build_collections_report_pdf(rows, granularity: str, zone_name: str, by_provider=None) -> bytes:
    pdf = FPDF()
    _header(pdf, f"Collections report ({granularity}) - {zone_name}")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(70, 9, "Period", border=1)
    pdf.cell(60, 9, "Amount (TZS)", border=1)
    pdf.cell(50, 9, "Payments", border=1, ln=True)
    pdf.set_font("Helvetica", "", 11)
    for r in rows:
        pdf.cell(70, 9, str(r["period"]), border=1)
        pdf.cell(60, 9, f'{r["amount_tzs"]:,}', border=1)
        pdf.cell(50, 9, str(r["payments_count"]), border=1, ln=True)
    if not rows:
        pdf.cell(0, 9, "No payments in this range.", border=1, ln=True)

    if by_provider:
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "By zone", ln=True)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(110, 9, "Zone", border=1)
        pdf.cell(70, 9, "Total collected (TZS)", border=1, ln=True)
        pdf.set_font("Helvetica", "", 11)
        for b in by_provider:
            pdf.cell(110, 9, str(b["name"]), border=1)
            pdf.cell(70, 9, f'{b["total_tzs"]:,}', border=1, ln=True)

    return bytes(pdf.output())


def build_customer_statement_pdf(customer, payments, zone_name: str) -> bytes:
    pdf = FPDF()
    _header(pdf, "Customer statement")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Customer: {customer.full_name}", ln=True)
    pdf.cell(0, 7, f"Phone: {customer.phone}", ln=True)
    pdf.cell(0, 7, f"Zone: {zone_name}", ln=True)
    pdf.cell(0, 7, f"Wallet balance: TZS {customer.wallet_balance_tzs:,}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 9, "Period", border=1)
    pdf.cell(45, 9, "Amount (TZS)", border=1)
    pdf.cell(40, 9, "Status", border=1)
    pdf.cell(65, 9, "Date", border=1, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for p in payments:
        pdf.cell(40, 9, p.billing_period, border=1)
        pdf.cell(45, 9, f"{p.amount:,}", border=1)
        pdf.cell(40, 9, p.status, border=1)
        pdf.cell(65, 9, p.completed_at.strftime("%d %b %Y, %H:%M") if p.completed_at else "-", border=1, ln=True)
    if not payments:
        pdf.cell(0, 9, "No payments yet.", border=1, ln=True)

    return bytes(pdf.output())
