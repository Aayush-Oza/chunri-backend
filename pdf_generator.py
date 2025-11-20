from fpdf import FPDF

def generate_invoice(order):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Invoice #{order.id}")
    pdf.output(f"invoice_{order.id}.pdf")
