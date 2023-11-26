import streamlit as st
import sqlite3
from datetime import datetime
import qrcode
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

# Inisialisasi database SQLite
conn = sqlite3.connect('donation_app.db')
c = conn.cursor()

# Membuat tabel donations
c.execute('''
    CREATE TABLE IF NOT EXISTS donations
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT,
    amount INTEGER,
    campaign TEXT,
    payment_method TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
''')
conn.commit()

# Menambahkan akun admin (username: admin, password: password)
c.execute('''
    CREATE TABLE IF NOT EXISTS admin_accounts
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT)
''')
conn.commit()

# Cek apakah akun admin sudah ada, jika tidak, tambahkan
c.execute('SELECT * FROM admin_accounts WHERE username="admin"')
admin_account = c.fetchone()
if admin_account is None:
    c.execute('INSERT INTO admin_accounts (username, password) VALUES (?, ?)',
              ('admin', 'password'))
    conn.commit()

# Fungsi untuk menambah donasi ke database dengan informasi tambahan campaign dan metode pembayaran
def add_donation(donor_name, amount, campaign, payment_method):
    c.execute('INSERT INTO donations (donor_name, amount, campaign, payment_method) VALUES (?, ?, ?, ?)',
              (donor_name, amount, campaign, payment_method))
    conn.commit()

# Fungsi untuk menampilkan riwayat donasi
def view_donations():
    c.execute('SELECT * FROM donations ORDER BY timestamp DESC')
    donations = c.fetchall()
    return donations

# Fungsi untuk login admin
def admin_login(username, password):
    cleaned_username = username.strip()
    cleaned_password = password.strip()

    c.execute('SELECT * FROM admin_accounts WHERE username=? AND password=?', (cleaned_username, cleaned_password))
    admin_account = c.fetchone()
    return admin_account is not None

# Fungsi untuk menghapus donasi dari database berdasarkan ID
def delete_donation(donation_id):
    c.execute('DELETE FROM donations WHERE id = ?', (donation_id,))
    conn.commit()

# Fungsi untuk membuat QrCode dan menampilkan gambar QrCode
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# Halaman utama
def home():
    st.image("3.png", width=500)  # Ganti dengan path/logo yang sesuai
    st.write("Pilih peran Anda:")
    choice = st.radio("", ("Admin", "Donatur"))

    if choice == "Admin":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if admin_login(username, password):
                admin_page()
            else:
                st.warning("Login gagal. Coba lagi.")
    elif choice == "Donatur":
        donor_page()

# Halaman admin
def admin_page():
    st.title("Halaman Admin")

    st.subheader("Riwayat Donasi")
    donations = view_donations()

    # Menampilkan tabel dengan riwayat donasi
    table_data = []
    for donation in donations:
        table_data.append([donation[0], donation[1], donation[2], donation[3], donation[4], donation[5]])

    # Menambahkan tabel ke halaman admin
    df = pd.DataFrame(table_data, columns=["ID", "Donor Name", "Amount", "Campaign", "Payment Method", "Timestamp"])
    st.table(df)

   # Menambahkan form untuk menghapus donasi
    with st.form(key="delete_form"):
        # Menambahkan dropdown untuk memilih donasi yang akan dihapus
        selected_donation = st.selectbox("Pilih Donasi untuk Dihapus", df["ID"])

        # Menambahkan tombol untuk menghapus donasi berdasarkan ID
        submit_button = st.form_submit_button(label=f"Hapus Donasi #{selected_donation}")

    # Menangani aksi penghapusan setelah form disubmit
    if submit_button:
        if delete_donation(selected_donation):
            st.success(f"Donasi #{selected_donation} telah dihapus.")
        else:
            st.error(f"Gagal menghapus donasi #{selected_donation}. Silakan coba lagi.")
            
    # Menampilkan bar chart jumlah donasi per campaign
    st.subheader("Bar Chart: Jumlah Donasi per Campaign")
    bar_chart_data = df.groupby("Campaign")["Amount"].sum().reset_index()

    # Membuat bar chart menggunakan seaborn
    fig, ax = plt.subplots()
    sns.barplot(x="Campaign", y="Amount", data=bar_chart_data, ax=ax)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Jumlah Donasi")

    # Menampilkan grafik di Streamlit
    st.pyplot(fig)

    # Menambahkan tombol keluar
    if st.button("Keluar"):
        st.experimental_rerun()

# Halaman donatur
def donor_page():
    st.title("Halaman Donatur")
    donor_name = st.text_input("Nama Donatur")
    amount = st.number_input("Jumlah Donasi (Rp)", min_value=500, step=1)  # Set jumlah minimal ke Rp 500

    # Pilihan Campaign
    campaign_options = ["Kebakaran", "Bakti Sosial", "Panti Asuhan"]
    campaign = st.selectbox("Pilih Campaign", campaign_options)

    # Pilihan Metode Pembayaran
    payment_options = ["DANA", "GOPAY"]
    payment_method = st.selectbox("Pilih Metode Pembayaran", payment_options)

    # Jika metode pembayaran Qris dipilih, tampilkan gambar QrCode dan informasi
    if payment_method == "GOPAY":
        qr_data = "08517344166"  # Nomor untuk Qris
        st.image("2.jpg", width=300)
        st.info("Silakan transfer menggunakan metode GOPAY (0851-73-444-166) .")

    # Jika metode pembayaran Dana dipilih, tampilkan nomor Dana dan informasi
    elif payment_method == "DANA":
        st.image("1.jpg", width=300)
        st.info("Silakan transfer menggunakan metode DANA (0851-73-444-166) .")

    # Tombol "Donasi Sekarang"
    if amount < 500:
        st.warning("Jumlah donasi harus minimal Rp 500.")
    else:
        if st.button("Donasi Sekarang"):
            add_donation(donor_name, amount, campaign, payment_method)
            st.success(f"Terima kasih, {donor_name}! Donasi sebesar Rp {amount:,.0f} untuk campaign {campaign} "
                       f"dengan metode pembayaran {payment_method} telah diterima.")

    # Menu Bantuan
    st.sidebar.title("Bantuan")
    st.sidebar.write("Jika Anda memerlukan bantuan, silakan hubungi kami:")
    st.sidebar.write("WhatsApp: [0851-73444-166](https://wa.me/6285173444166)")
    st.sidebar.write("Email: [donasidata@gmail.com](mailto:donasidata@gmail.com)")




# Menjalankan aplikasi
if __name__ == "__main__":
    home()
