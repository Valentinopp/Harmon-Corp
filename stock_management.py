import pandas as pd
from abc import ABC, abstractmethod
from payment_strategy import CreditCardPayment, DigitalWalletPayment

# Abstract Class: StockManagement
class StockManagement(ABC):
    def manage_stock(self, item=None, quantity=None, price=None):
        self.view_stock()
        if self.can_add_stock():
            if item and quantity and price:  # Memeriksa apakah ada data untuk ditambahkan
                self.add_stock(item, quantity, price)
        if self.can_edit_stock():
            self.edit_stock()
        if self.can_delete_stock():
            self.delete_stock()

    def load_data(self):
        return pd.read_csv("data_stock.csv")

    def save_data(self, data):
        data.to_csv("data_stock.csv", index=False)

    def view_stock(self):
        print("Viewing Stock")
        data = self.load_data()
        return data  # Return data for use in Streamlit

    @abstractmethod
    def can_add_stock(self):
        pass

    @abstractmethod
    def can_edit_stock(self):
        pass

    @abstractmethod
    def can_delete_stock(self):
        pass

    def add_stock(self, item, quantity, price):
        data = self.load_data()
        new_data = pd.DataFrame({"Item": [item], "Quantity": [quantity], "Price": [price]})
        data = pd.concat([data, new_data], ignore_index=True)
        self.save_data(data)
        return "Produk berhasil ditambahkan"

    def edit_stock(self, product_name, updated_quantity, updated_price):
        data = self.load_data()
        data.loc[data["Item"] == product_name, "Quantity"] = updated_quantity
        data.loc[data["Item"] == product_name, "Price"] = updated_price
        self.save_data(data)
        return "Produk berhasil diperbarui"

    def delete_stock(self, product_name):
        data = self.load_data()
        data = data[data["Item"] != product_name]
        self.save_data(data)
        return "Produk berhasil dihapus"

    def update_stock_after_payment(self, product_name, quantity):
        data = self.load_data()
        data.loc[data["Item"] == product_name, "Quantity"] -= quantity  # Mengurangi stok berdasarkan jumlah yang dibeli
        self.save_data(data)
        print(f"Stok {product_name} telah diperbarui.")

class ResellerStockManagement(StockManagement):
    def _init_(self):
        self.cart = []
        self.transactions_file = "reseller_products.csv"  # File untuk menyimpan transaksi reseller

    def can_add_stock(self):
        return False

    def can_edit_stock(self):
        return False

    def can_delete_stock(self):
        return False

    def add_to_cart(self, product_name, quantity, total_harga):
        # Memastikan kolom total_harga dihitung dengan benar saat produk ditambahkan
        price = self.load_data().loc[self.load_data()["Item"] == product_name, "Price"].values[0]
        total_harga = price * quantity
        self.cart.append({"product_name": product_name, "quantity": quantity, "total_harga": total_harga})

    def get_cart_details(self):
        return pd.DataFrame(self.cart)  # Menampilkan keranjang belanja

    def calculate_total_amount(self):
        total_amount = 0
        for item in self.cart:
            total_amount += item["price"]  # Menggunakan total_harga yang sudah dihitung
        return total_amount

    def select_payment_method(self, payment_method, total_amount):
        payment_method.pay(total_amount)
        for item in self.cart:
            self.update_stock_after_payment(item["product_name"], item["quantity"])
        self.record_transaction()

    def update_stock_after_payment(self, product_name, quantity):
        # Contoh implementasi: Kurangi stok berdasarkan produk yang dibeli
        stock_data = pd.read_csv("data_stock.csv")  # Memuat data stok
        stock_data.loc[stock_data["Item"] == product_name, "Quantity"] -= quantity
        stock_data.to_csv("data_stock.csv", index=False)  # Simpan perubahan
        return f"Stok untuk {product_name} berhasil diperbarui."

    def record_transaction(self):
        # Menghitung total pengeluaran reseller
        total_amount = self.calculate_total_amount()

        # Membuat DataFrame transaksi dengan data keranjang
        transaction_data = pd.DataFrame(self.cart)

        # Menambahkan kolom 'total_harga' sudah dihitung di add_to_cart
        # Tidak perlu lagi menambahkan total_harga dengan apply function

        # Jika file transaksi sudah ada, tambahkan data baru ke dalamnya
        try:
            existing_data = pd.read_csv(self.transactions_file)
            new_data = pd.concat([existing_data, transaction_data], ignore_index=True)
            new_data.to_csv(self.transactions_file, index=False)
        except FileNotFoundError:
            # Jika file transaksi belum ada, buat file baru
            transaction_data.to_csv(self.transactions_file, index=False)

        print(f"Transaksi berhasil dicatat dengan total pengeluaran {total_amount}.")

class AdminStockManagement(StockManagement):
    def can_add_stock(self):
        return True

    def can_edit_stock(self):
        return True

    def can_delete_stock(self):
        return True

    def get_total_expenditure(self):
        try:
            # Membaca file transaksi yang telah disimpan oleh reseller
            transaction_data = pd.read_csv("reseller_products.csv")
            total_expenditure = transaction_data["price"].sum()
            return total_expenditure
        except FileNotFoundError:
            return 0

    def view_transactions(self):
        try:
            # Membaca file transaksi
            transaction_data = pd.read_csv("reseller_products.csv")
            return transaction_data
        except FileNotFoundError:
            return pd.DataFrame()  # Jika tidak ada transaksi

