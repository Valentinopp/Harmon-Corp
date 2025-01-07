from abc import ABC, abstractmethod
import re
import pandas as pd

# File CSV untuk menyimpan data reseller
DATA_FILE = "resellers.csv"

class Handler(ABC):
    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def handle(self, request):
        pass

class AbstractHandler(Handler):
    def __init__(self):
        self._next_handler = None

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    def handle(self, request):
        if self._next_handler:
            return self._next_handler.handle(request)
        return None

class EmailValidationHandler(AbstractHandler):
    def handle(self, request):
        email = request.get("email")
        if not email:
            return "Email tidak boleh kosong."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Format email tidak valid."
        return super().handle(request)

class PasswordValidationHandler(AbstractHandler):
    def handle(self, request):
        password = request.get("password")
        if not password:
            return "Password tidak boleh kosong."
        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password):
            return "Password harus mengandung setidaknya 8 karakter, satu huruf besar, satu huruf kecil, dan satu angka."
        return super().handle(request)

class ConfirmPasswordHandler(AbstractHandler):
    def handle(self, request):
        if not request.get("confirm_password"):
            return "Konfirmasi password tidak boleh kosong."
        if request.get("password") != request.get("confirm_password"):
            return "Konfirmasi password tidak sesuai."
        return super().handle(request)

class EmailExistsHandler(AbstractHandler):
    def handle(self, request):
        email = request.get("email")
        if not email:
            return "Email tidak boleh kosong."
        try:
            df = pd.read_csv(DATA_FILE)
            if email in df['email'].values:
                return "Email sudah terdaftar."
        except FileNotFoundError:
            pass
        return super().handle(request)

class SaveUserHandler(AbstractHandler):
    def handle(self, request):
        for key in ["name", "address", "contact"]:
            if not request.get(key):
                return f"{key.capitalize()} tidak boleh kosong."
        user_data = {
            "email": request.get("email"),
            "password": request.get("password"),
            "name": request.get("name"),
            "address": request.get("address"),
            "contact": request.get("contact"),
            "status": request.get("status", "unverified"),
            "role": request.get("role")
        }
        try:
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, pd.DataFrame([user_data])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([user_data])
        df.to_csv(DATA_FILE, index=False)
        return "Registrasi berhasil."

class VerificationStatusHandler(AbstractHandler):
    def handle(self, request):
        email = request.get("email")
        try:
            df = pd.read_csv(DATA_FILE)
            user = df[df["email"] == email].iloc[0] if email in df["email"].values else None

            if user is not None and user["status"] != "verified":
                return "Akun Anda belum diverifikasi oleh admin."
        except FileNotFoundError:
            pass
        return super().handle(request)
