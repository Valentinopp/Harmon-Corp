import streamlit as st
import pandas as pd
from handlers import (
    EmailValidationHandler,
    PasswordValidationHandler,
    ConfirmPasswordHandler,
    EmailExistsHandler,
    SaveUserHandler,
    VerificationStatusHandler,
)
from stock_management import AdminStockManagement, ResellerStockManagement
from payment_strategy import CreditCardPayment, DigitalWalletPayment

DATA_FILE = "resellers.csv"
PRODUCT_FILE = "reseller_products.csv"
data = pd.read_csv("data_stock.csv")

# Inisialisasi session state untuk reseller
if "cart" not in st.session_state:
    st.session_state.cart = []
if "selected_payment_method" not in st.session_state:
    st.session_state.selected_payment_method = None


st.set_page_config(
    page_title="Sistem Informasi Kemitraan Reseller",
    page_icon=":busts_in_silhouette:",
    layout="wide",
)

# Sidebar logo
with st.sidebar:
    st.image("harmonCorp.jpg", width=150)

# Judul utama
st.markdown("""
    <style>
        .main-header {
            text-align: center;
            font-size: 32px;
            color: #ff4b4b;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .subheader {
            color: #555555;
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)
st.markdown('<div class="main-header">Sistem Informasi Kemitraan Reseller</div>', unsafe_allow_html=True)

# Memeriksa apakah user sudah login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    role = st.sidebar.radio("Pilih Peran", ["Reseller", "Admin", "Jasa Pengiriman"])
    action = st.sidebar.radio("Pilih Aksi", ["Registrasi", "Login"])

    if action == "Registrasi":
        st.subheader(f"Formulir Registrasi {role}")
        st.info("Setelah registrasi, akun Anda harus diverifikasi oleh admin sebelum bisa login.")
        with st.form(f"form_register_{role.lower()}"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            name = st.text_input("Nama Lengkap")
            address = st.text_area("Alamat")
            contact = st.text_input("Nomor Kontak")
            submitted = st.form_submit_button("Registrasi")

            if submitted:
                # Chain of Responsibility
                handler = (
                    EmailValidationHandler()
                    .set_next(PasswordValidationHandler())
                    .set_next(ConfirmPasswordHandler())
                    .set_next(EmailExistsHandler())
                    .set_next(SaveUserHandler())
                )

                # Buat request data
                request_data = {
                    "email": email.strip(),
                    "password": password.strip(),
                    "confirm_password": confirm_password.strip(),
                    "name": name.strip(),
                    "address": address.strip(),
                    "contact": contact.strip(),
                    "role": role.lower(),
                    "status": "unverified" if role == "Reseller" else "verified"
                }

                # Eksekusi handler
                result = handler.handle(request_data)
                if result == "Registrasi berhasil.":
                    st.success(result)
                else:
                    st.error(result)


    elif action == "Login":
        st.subheader(f"Login {role}")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                df = pd.read_csv(DATA_FILE)
                user = df[df["email"] == email].iloc[0] if email in df["email"].values else None

                if user is None or user["password"] != password or user["role"] != role.lower():
                    st.error("Email atau password salah.")
                else:
                    # Handler untuk memeriksa status verifikasi
                    handler = VerificationStatusHandler()
                    result = handler.handle({"email": email})

                    if result:
                        st.error(result)
                    else:
                        # Login berhasil jika semua validasi lolos
                        st.session_state.logged_in = True
                        st.session_state.user_data = user
                        st.success(f"Selamat datang, {user['name']}!")
                        st.rerun()

            except FileNotFoundError:
                st.error("Database pengguna tidak ditemukan.")


elif st.session_state.logged_in:
    user = st.session_state.user_data
    with st.sidebar:
        st.write(f"**PROFIL PENGGUNA**")
        st.write(f"**Nama:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Alamat:** {user['address']}")
        st.write(f"**Nomor Kontak:** {user['contact']}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.rerun()

    if user["role"] == "reseller":
        st.subheader("Produk Anda")
        try:
            df = pd.read_csv(PRODUCT_FILE)
            user_products = df[(df["email"] == user["email"]) & (df["status"] == "delivered")]
            
            if not user_products.empty:
                st.dataframe(user_products[["product_name", "quantity", "price"]])
            else:
                st.warning("Belum ada produk yang terdaftar.")
        except FileNotFoundError:
            st.error("File data produk tidak ditemukan.")

        st.subheader("Pelaporan Harian Penjualan")
        selected_product = st.selectbox("Pilih Produk", user_products['product_name'].unique())

        # Menampilkan detail produk
        product_details = user_products[user_products['product_name'] == selected_product]
        if not product_details.empty:
            max_quantity = int(product_details['quantity'].values[0])
            quantity = st.number_input("Jumlah Produk Terjual", min_value=1, max_value=max_quantity, step=1)
        else:
            st.error("Produk tidak ditemukan.")

        # Tambahkan ke tabel penjualan
        if st.button("Masukkan ke Tabel Penjualan"):
            price = product_details['price'].values[0]
            total_harga = quantity * price
            
            # Gunakan session_state.sales untuk penjualan
            if "sales" not in st.session_state:
                st.session_state.sales = []
            
            st.session_state.sales.append({"product_name": selected_product, "quantity": quantity, "total_penghasilan": total_harga})
            st.success(f"{selected_product} berhasil ditambahkan ke Tabel Penjualan.")
        
        # Tampilkan tabel penjualan
        st.subheader("Tabel Penjualan")
        if "sales" in st.session_state and st.session_state.sales:
            st.table(st.session_state.sales)

        # Submit laporan penjualan
        if st.button("Submit Laporan"):
            if "sales" in st.session_state and st.session_state.sales:
                # Mengurangi stok di DataFrame
                for item in st.session_state.sales:
                    product_name = item["product_name"]
                    qty_sold = item["quantity"]

                    # Update quantity dalam DataFrame
                    df.loc[df['product_name'] == product_name, 'quantity'] -= qty_sold

                # Simpan perubahan ke file
                df.to_csv(PRODUCT_FILE, index=False)
                st.success("Laporan berhasil disubmit dan stok telah diperbarui.")
                
                # Reset tabel penjualan setelah submit
                st.session_state.sales = []
                st.rerun()
            else:
                st.warning("Tabel Penjualan kosong. Tambahkan produk terlebih dahulu.")


        

        

        # Reseller: Memilih produk untuk dibeli
        st.subheader("Pilih Produk untuk Dipesan")

        reseller = ResellerStockManagement()
        stock_data = reseller.view_stock()  # Mendapatkan data stok
        st.dataframe(stock_data)  # Menampilkan data stok untuk reseller


        selected_product = st.selectbox("Pilih Produk", data['Item'].values)

        # Menampilkan detail produk
        product_details = data[data['Item'] == selected_product]
        # st.write(product_details)

        # Menentukan jumlah yang ingin dibeli
        quantity = st.number_input("Jumlah Produk", min_value=1, max_value=int(product_details['Quantity'].values[0]), step=1)
        if st.button("Masukkan ke Keranjang"):
            # Menambahkan produk ke keranjang
            price = product_details['Price'].values[0]
            total_harga = quantity * price
            st.session_state.cart.append({"product_name": selected_product,"price":price, "quantity": quantity, "total_harga": total_harga})
            st.success(f"{selected_product} berhasil ditambahkan ke keranjang.")

        # Menampilkan keranjang belanja
        st.write("Keranjang Anda:")
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df)

        st.subheader("Metode Pembayaran")
        payment_method = st.radio("Pilih Metode Pembayaran:", ["Kartu Kredit", "Dompet Digital"])
        if payment_method == "Kartu Kredit":
            st.session_state.selected_payment_method = CreditCardPayment()
        elif payment_method == "Dompet Digital":
            st.session_state.selected_payment_method = DigitalWalletPayment()

        # Reseller: Melakukan pembayaran
        if st.button("Lakukan Pembayaran"):
            if st.session_state.selected_payment_method:
                total_amount = sum(item["total_harga"] for item in st.session_state.cart)
                st.session_state.selected_payment_method.pay(total_amount)
                
                # Update stok setelah pembayaran
                for item in st.session_state.cart:
                    reseller.update_stock_after_payment(item["product_name"], item["quantity"])
                
                # Simpan data transaksi ke reseller_products.csv
                transaction_data = pd.DataFrame(st.session_state.cart)
                print(transaction_data)
                transaction_data["email"] = user['email']
                transaction_data["status"] = "unpacked"
                transaction_data.reindex(["email","product_name","quantity","price","status","total_harga"])

                try:
                    # Jika file sudah ada, tambahkan data baru ke dalamnya
                    existing_data = pd.read_csv("reseller_products.csv")
                    updated_data = pd.concat([existing_data, transaction_data], ignore_index=True)
                    updated_data.to_csv("reseller_products.csv", index=False)
                except FileNotFoundError:
                    # Jika file belum ada, buat file baru
                    transaction_data.to_csv("reseller_products.csv", index=False)
                
                # Kosongkan keranjang setelah pembayaran
                st.session_state.cart = []
                st.success(f"Pembayaran sebesar {total_amount} berhasil dilakukan dan transaksi telah dicatat.")
            else:
                st.warning("Pilih metode pembayaran terlebih dahulu.")



    elif user["role"] == "admin":
        st.subheader("Verifikasi Reseller")
        try:
            df = pd.read_csv(DATA_FILE)
            unverified_resellers = df[df["status"] == "unverified"]

            if not unverified_resellers.empty:
                st.write("Reseller yang perlu diverifikasi:")
                st.dataframe(unverified_resellers[["email", "name", "contact", "status"]])

                selected_reseller = st.selectbox(
                    "Pilih reseller untuk verifikasi", unverified_resellers["email"]
                )

                if st.button("Verifikasi"):
                    df.loc[df["email"] == selected_reseller, "status"] = "verified"
                    df.to_csv(DATA_FILE, index=False)
                    st.success(f"Reseller {selected_reseller} berhasil diverifikasi.")
                    st.rerun()
                    
            else:
                st.info("Tidak ada reseller yang perlu diverifikasi.")
        except FileNotFoundError:
            st.error("File data reseller tidak ditemukan.")

        admin = AdminStockManagement()

        # Admin melihat dan mengelola stok
        stock_data = admin.view_stock()  # Menampilkan data stok
        st.subheader("\nManajemen Stok")
        st.write("Data Stok untuk Admin:")
        st.dataframe(stock_data)  # Menampilkan tabel data stok

        # Admin: Tambah Stok Barang
        with st.expander("Tambah Stok Barang"):
            product_name = st.text_input("Nama Produk")
            stock_quantity = st.number_input("Jumlah Stok", min_value=0)
            price = st.number_input("Harga", min_value=0)
            if st.button("Tambah Produk"):
                if product_name and stock_quantity > 0 and price > 0:
                    response = admin.add_stock(item=product_name, quantity=stock_quantity, price=price)  # Memanggil add_stock langsung
                    st.success(response)
                    st.rerun()
                    
                else:
                    st.warning("Semua data harus diisi dengan benar!")

        # Admin: Edit Stok Barang
        with st.expander("Edit Stok Barang"):
            product_name_to_edit = st.selectbox("Pilih Produk yang akan diubah", stock_data["Item"])
            updated_quantity = st.number_input("Jumlah Stok Baru", min_value=0)
            updated_price = st.number_input("Harga Baru", min_value=0)
            if st.button("Update Produk"):
                response = admin.edit_stock(product_name_to_edit, updated_quantity, updated_price)
                st.success(response)
                st.rerun()
                
        # Admin: Hapus Stok Barang
        with st.expander("Hapus Stok Barang"):
            product_name_to_delete = st.selectbox("Pilih Produk yang akan dihapus", stock_data["Item"])
            if st.button("Hapus Produk"):
                response = admin.delete_stock(product_name_to_delete)
                st.success(response)
                st.rerun()

        # Admin melihat pengeluaran produk reseller
        total_expenditure = admin.get_total_expenditure()
        st.write(f"Jumlah Pengeluaran Produk oleh Reseller: {total_expenditure}")
        
        # Admin melihat daftar transaksi reseller
        transaction_data = admin.view_transactions()
        if not transaction_data.empty:
            st.write("Daftar Transaksi Reseller:")
            st.dataframe(transaction_data)  # Menampilkan daftar transaksi
        else:
            st.warning("Belum ada transaksi yang tercatat.")


        try:
            df = pd.read_csv(PRODUCT_FILE)
            udelivered_stock = df[df["status"] == "unpacked"]

            if not udelivered_stock.empty:
                st.write("Barang yang perlu dikirim:")
                st.dataframe(udelivered_stock[["email", "product_name", "quantity", "price", "status", "total_harga"]])

                # Pilih berdasarkan indeks
                selected_index = st.selectbox(
                    "Pilih indeks pemesanan untuk dikemas barangnya",
                    udelivered_stock.index
                )

                if st.button("Sudah Dikemas"):
                    df.loc[selected_index, "status"] = "packed"
                    df.to_csv(PRODUCT_FILE, index=False)
                    st.success(f"Barang pada indeks {selected_index} berhasil dikemas.")
                    st.rerun()

            else:
                st.info("Tidak ada barang yang perlu dikemas")
        except FileNotFoundError:
            st.error("File data barang tidak ditemukan.")

    elif user['role'] == 'jasa pengiriman':
        st.subheader("Data Pengiriman Barang Harmon Corp")
        try:
            df = pd.read_csv(PRODUCT_FILE)
            packed_stock = df[df["status"] == "packed"]

            if not packed_stock.empty:
                st.write("Barang yang perlu dikirim:")
                st.dataframe(packed_stock[["email", "product_name", "quantity", "price", "status", "total_harga"]])

                # Pilih berdasarkan indeks
                selected_index = st.selectbox(
                    "Pilih indeks pemesanan untuk dikirim barangnya",
                    packed_stock.index
                )

                if st.button("Kirim"):
                    df.loc[selected_index, "status"] = "delivered"
                    df.to_csv(PRODUCT_FILE, index=False)
                    # data.loc[len(data)] = [packed_stock["product_name", packed_stock['quantity', packed_stock['price']]]]
                    # data.to_csv("data_stock.csv", index=False)
                    st.success(f"Barang pada indeks {selected_index} berhasil dikirim.")
                    st.rerun()

            else:
                st.info("Tidak ada barang yang perlu dikirim")
        except FileNotFoundError:
            st.error("File data barang tidak ditemukan.")
                    
