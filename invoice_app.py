import streamlit as st
import sqlite3, os, datetime, pandas as pd
import streamlit_authenticator as stauth
from passlib.hash import pbkdf2_sha256
from weasyprint import HTML

# ─────── CONFIG ───────
st.set_page_config("Invoice Generator", layout="wide")
os.makedirs("logos", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)

# ─────── AUTH ───────
names = ["Srinath", "John"]
usernames = ["srinath", "john123"]
hashed_passwords = [
    "$pbkdf2-sha256$29000$y5lT6r3XmtNa6x2D8F4LwQ$AA3JlaLA/Ns4TIUeLdoiE2ZuJdea7vhMNva/5rPYTlA",  # 123
    "$pbkdf2-sha256$29000$tVbKeY8RohTCWKt1zpmTcg$xK/T9moxoeOh21h5v8uW7rZkw3K2SiylZLbmZOF6HD4"   # abc
]
credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": hashed_passwords[0]},
        usernames[1]: {"name": names[1], "password": hashed_passwords[1]},
    }
}
authenticator = stauth.Authenticate(credentials, "invoice_app", "abcdef", cookie_expiry_days=1)
name, auth_status, username = authenticator.login("Login", location="main")

if auth_status:
    authenticator.logout("Logout", location="sidebar")
    st.sidebar.success(f"Welcome {name}")
elif auth_status is False:
    st.error("❌ Incorrect username or password")
    st.stop()
else:
    st.warning("🕓 Please enter your credentials")
    st.stop()

# ─────── DB ───────
conn = sqlite3.connect("clients.db", check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS clients (
                user TEXT, name TEXT, address TEXT, gstin TEXT,
                UNIQUE(user,name)
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS invoices (
                user TEXT, inv_no TEXT, date TEXT, due TEXT,
                total REAL, path TEXT)""")
conn.commit()

# ─────── Sidebar: History ───────
with st.sidebar.expander("📜 Invoice History"):
    df = pd.read_sql("SELECT inv_no,date,total FROM invoices WHERE user=?", conn, params=(username,))
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        inv = st.selectbox("Download invoice", df['inv_no'])
        path = c.execute("SELECT path FROM invoices WHERE inv_no=? AND user=?", (inv, username)).fetchone()[0]
        with open(f"pdfs/{path}", "rb") as f:
            st.download_button("📥 Download", f.read(), file_name=f"{inv}.pdf")
    else:
        st.info("No invoices yet.")

# ─────── Main Form ───────
st.title("🧾 Professional Invoice Generator")

# Business Info
st.subheader("Your Business Info")
logo = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
if logo:
    logo_path = f"logos/{logo.name}"
    open(logo_path, "wb").write(logo.read())
else:
    logo_path = ""

biz_name = st.text_input("Business Name")
biz_address = st.text_area("Address")
biz_contact = st.text_input("Contact (Phone/Email)")
biz_gstin = st.text_input("GSTIN")

# Client Info
st.subheader("Client Info")
clients = c.execute("SELECT name FROM clients WHERE user=?", (username,)).fetchall()
client_options = [x[0] for x in clients]
selected = st.selectbox("Choose Client", ["-- New --"] + client_options)
if selected != "-- New --":
    cl_name = selected
    cl_addr, cl_gst = c.execute("SELECT address, gstin FROM clients WHERE user=? AND name=?", (username, selected)).fetchone()
else:
    cl_name = st.text_input("Client Name")
    cl_addr = st.text_area("Client Address")
    cl_gst = st.text_input("Client GSTIN")
    if cl_name and st.button("➕ Save Client"):
        try:
            c.execute("INSERT INTO clients VALUES (?,?,?,?)", (username, cl_name, cl_addr, cl_gst))
            conn.commit()
            st.success("Client saved.")
        except sqlite3.IntegrityError:
            st.warning("Client already exists.")

# Invoice Details
st.subheader("Invoice Details")
inv_no = st.text_input("Invoice Number", f"INV-{datetime.date.today().strftime('%Y%m%d')}")
inv_date = st.date_input("Invoice Date", datetime.date.today())
due_date = st.date_input("Due Date", datetime.date.today() + datetime.timedelta(days=7))

# Items
st.subheader("Invoice Items")
n = st.number_input("No. of items", min_value=1, max_value=20, value=3)
items = []
for i in range(n):
    cols = st.columns([3,1,1,1])
    desc = cols[0].text_input(f"Item {i+1} Description", key=f"d{i}")
    qty = cols[1].number_input("Qty", min_value=1, key=f"q{i}")
    rate = cols[2].number_input("Rate", min_value=0.0, key=f"r{i}")
    tax = cols[3].number_input("Tax (%)", min_value=0.0, key=f"t{i}")
    items.append((desc, qty, rate, tax))

# Generate PDF
if st.button("📄 Generate Invoice"):
    # Build HTML
    rows = ""
    total = 0
    for desc, qty, rate, tax in items:
        subtotal = qty * rate
        tax_amt = subtotal * tax / 100
        total_amt = subtotal + tax_amt
        total += total_amt
        rows += f"<tr><td>{desc}</td><td>{qty}</td><td>{rate:.2f}</td><td>{tax}%</td><td>{total_amt:.2f}</td></tr>"

    logo_html = f"<img src='file://{os.path.abspath(logo_path)}' width='100'>" if logo_path else ""
    html = f"""
    <html><head><style>
    body{{font-family:Arial;margin:30px}}
    table{{width:100%;border-collapse:collapse;margin-top:20px}}
    th,td{{border:1px solid #ccc;padding:8px;text-align:center}}
    th{{background:#f2f2f2}}
    .right{{text-align:right}}
    </style></head><body>
    <table width='100%'><tr><td>{logo_html}</td><td class='right'><h2>TAX INVOICE</h2></td></tr></table>
    <p><b>{biz_name}</b><br>{biz_address}<br>{biz_contact}<br>GSTIN: {biz_gstin}</p>
    <hr>
    <p><b>Billed To:</b><br>{cl_name}<br>{cl_addr}<br>GSTIN: {cl_gst}</p>
    <p class='right'>
        Invoice #: {inv_no}<br>
        Date: {inv_date}<br>
        Due: {due_date}
    </p>
    <table>
    <tr><th>Description</th><th>Qty</th><th>Rate</th><th>Tax</th><th>Total</th></tr>
    {rows}
    </table>
    <h3 class='right'>Grand Total: ₹{total:.2f}</h3>
    <p>Thank you for your business!</p>
    </body></html>
    """

    filename = f"{username}_{inv_no}.pdf"
    HTML(string=html).write_pdf(f"pdfs/{filename}")
    c.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)",
              (username, inv_no, str(inv_date), str(due_date), total, filename))
    conn.commit()

    with open(f"pdfs/{filename}", "rb") as f:
        st.success("✅ Invoice Generated!")
        st.download_button("📥 Download Invoice", f.read(), file_name=filename)
