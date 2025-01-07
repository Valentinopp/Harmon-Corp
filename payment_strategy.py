from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    """Abstract Base Class for Payment Strategies."""
    @abstractmethod
    def pay(self, total_amount):
        pass


class CreditCardPayment(PaymentStrategy):
    """Concrete Strategy for Credit Card Payment."""
    def pay(self, total_amount):
        return f"Pembayaran menggunakan Kartu Kredit sebesar Rp{total_amount} berhasil."


class DigitalWalletPayment(PaymentStrategy):
    """Concrete Strategy for Digital Wallet Payment."""
    def pay(self, total_amount):
        return f"Pembayaran menggunakan Dompet Digital sebesar Rp{total_amount} berhasil."


class BankTransferPayment(PaymentStrategy):
    """Concrete Strategy for Bank Transfer Payment."""
    def pay(self, total_amount):
        return f"Pembayaran melalui Transfer Bank sebesar Rp{total_amount} berhasil."


# Mapping Payment Strategies
PAYMENT_METHODS = {
    "Kartu Kredit": CreditCardPayment,
    "Dompet Digital": DigitalWalletPayment,
    "Transfer Bank": BankTransferPayment,
}
