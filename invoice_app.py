import streamlit as st
from weasyprint import HTML
import tempfile
import os
from datetime import date

# Streamlit config
st.set_page_config("Invoice Generator", layout="centered")
st.title("🧾 Invoice Generator")

# Invoice form
with st.form("invoice_form"):
    st.header("Invoice Details")

    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Your Company Name", "Your Company Pvt Ltd")
        company_address = st.text_area("Company Address", "1234 Business Street\nCity, State - ZIP")
        gstin = st.text_input("Company GSTIN", "29ABCDE1234F1Z5")

    with col2:
        invoice_no = st.text_input("Invoice Number", "INV-20250703")
        invoice_date = st.date_input("Invoice Date", date.today())
        due_date = st.date_input("Due Date", date.today())

    st.markdown("---")
    st.header("Client Details")

    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Client Name", "Mr. Rahul Mehta")
        client_address = st.text_area("Client Address", "56 Green Park\nNew Delhi - 110016")
    with col2:
        client_phone = st.text_input("Client Phone", "+91-9123456789")
        client_gstin = st.text_input("Client GSTIN", "07ABCDE1234F1Z9")

    st.markdown("---")
    st.header("Items")
    n_items = st.number_input("Number of Items", 1, 10, 3)
    items = []
    for i in range(n_items):
        cols = st.columns(5)
        desc = cols[0].text_input(f"Description {i+1}", f"Sale Item #{i+1}")
        hsn = cols[1].text_input(f"HSN Code {i+1}", "8409")
        qty = cols[2].number_input(f"Qty {i+1}", 1, key=f"qty{i}")
        rate = cols[3].number_input(f"Rate {i+1}", 0.0, key=f"rate{i}")
        items.append((i + 1, desc, hsn, qty, rate, qty * rate))

    st.markdown("---")
    st.header("Summary")

    discount = st.number_input("Discount (₹)", 0.0)
    tax_rate = st.number_input("Tax Rate (%)", 18.0)
    shipping = st.number_input("Shipping (₹)", 0.0)
    previous_dues = st.number_input("Previous Dues (₹)", 0.0)

    payment_note = st.text_area("Payment Details", 
        "• Account Name: Your Company\n"
        "• Account No.: 9876543210\n"
        "• Bank: ABCD Bank\n"
        "• IFSC: ABCD0123456")

    submitted = st.form_submit_button("Generate Invoice")

if submitted:
    subtotal = sum(item[5] for item in items)
    tax = (subtotal - discount) * (tax_rate / 100)
    total = subtotal - discount + tax + shipping + previous_dues

    # Build table rows
    item_rows = ""
    for id_, desc, hsn, qty, rate, amount in items:
        item_rows += f"<tr><td>{id_}</td><td>{desc}</td><td>{hsn}</td><td>{qty}</td><td>₹{rate:.2f}</td><td>₹{amount:.2f}</td></tr>"

    # Load HTML template
    html_template = open("template.html", "r").read()
    html = html_template.format(
        company_name=company_name,
        company_address=company_address.replace('\n', '<br>'),
        gstin=gstin,
        invoice_no=invoice_no,
        invoice_date=invoice_date.strftime("%d %b %Y"),
        due_date=due_date.strftime("%d %b %Y"),
        client_name=client_name,
        client_address=client_address.replace('\n', '<br>'),
        client_phone=client_phone,
        client_gstin=client_gstin,
        item_rows=item_rows,
        subtotal=subtotal,
        discount=discount,
        tax_rate=tax_rate,
        tax=tax,
        shipping=shipping,
        dues=previous_dues,
        total=total,
        payment_note=payment_note.replace('\n', '<br>')
    )

    # Create and download PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        HTML(string=html).write_pdf(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.success("✅ Invoice generated successfully!")
            st.download_button("📥 Download Invoice", f.read(), file_name=f"{invoice_no}.pdf")
