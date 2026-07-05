#!/usr/bin/env python3
"""Crypto Payment Gateway Template — BTC, USDT, XMR, ETH acceptance for digital products."""
import asyncio, json, logging, os, hashlib, time, hmac
from dataclasses import dataclass
from typing import Optional
import aiohttp

logging.basicConfig(level=logging.INFO)

@dataclass
class Invoice:
    id: str
    amount: float
    currency: str  # BTC, USDT, ETH, XMR
    product: str
    buyer_email: str = ""
    status: str = "pending"  # pending, paid, confirmed, expired
    created_at: float = 0
    expires_at: float = 0
    tx_hash: str = ""
    confirmations: int = 0

class CryptoPaymentGateway:
    """Multi-currency crypto payment gateway for digital products."""
    
    def __init__(self, wallets: dict, webhook_url: str = ""):
        self.wallets = wallets  # {"BTC": "bc1...", "USDT": "0x...", "ETH": "0x...", "XMR": "4..."}
        self.webhook_url = webhook_url
        self.invoices: dict[str, Invoice] = {}
        self.paid_callbacks = []
    
    def on_paid(self, callback):
        """Register callback for paid invoices."""
        self.paid_callbacks.append(callback)
    
    def create_invoice(self, amount: float, currency: str, product: str, buyer_email: str = "", timeout_mins: int = 60) -> Invoice:
        """Create a new payment invoice."""
        inv_id = hashlib.sha256(f"{time.time()}{product}{amount}".encode()).hexdigest()[:16]
        now = time.time()
        invoice = Invoice(
            id=inv_id,
            amount=amount,
            currency=currency.upper(),
            product=product,
            buyer_email=buyer_email,
            created_at=now,
            expires_at=now + timeout_mins * 60
        )
        self.invoices[inv_id] = invoice
        logging.info(f"Invoice {inv_id}: {amount} {currency} for {product}")
        return invoice
    
    def get_payment_address(self, invoice: Invoice) -> str:
        """Get payment address for invoice currency."""
        return self.wallets.get(invoice.currency, "")
    
    def check_invoice(self, inv_id: str) -> dict:
        """Check invoice status."""
        inv = self.invoices.get(inv_id)
        if not inv:
            return {"error": "Invoice not found"}
        if time.time() > inv.expires_at and inv.status == "pending":
            inv.status = "expired"
        return {
            "id": inv.id,
            "amount": inv.amount,
            "currency": inv.currency,
            "product": inv.product,
            "status": inv.status,
            "address": self.get_payment_address(inv),
            "expires_in": max(0, int(inv.expires_at - time.time())),
            "tx_hash": inv.tx_hash,
            "confirmations": inv.confirmations
        }
    
    async def verify_btc_payment(self, invoice: Invoice, api_url: str = "https://blockchain.info"):
        """Verify BTC payment via blockchain API."""
        addr = self.get_payment_address(invoice)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/rawaddr/{addr}", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                for tx in data.get("txs", []):
                    total = sum(out.get("value", 0) for out in tx.get("out", []) if addr in out.get("addr", ""))
                    if total >= invoice.amount * 1e8:  # BTC to satoshi
                        invoice.tx_hash = tx.get("hash", "")
                        invoice.confirmations = tx.get("confirmations", 0)
                        if invoice.confirmations >= 1:
                            invoice.status = "confirmed"
                        else:
                            invoice.status = "paid"
                        await self._notify_paid(invoice)
                        return True
        return False
    
    async def verify_xmr_payment(self, invoice: Invoice, monero_rpc: str = "http://localhost:18081"):
        """Verify XMR payment via Monero RPC."""
        addr = self.get_payment_address(invoice)
        # Use Monero RPC to check incoming payments
        # This is a template — implement with monero-wallet-rpc
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": "0",
                "method": "get_transfers",
                "params": {"pool": True, "in": True}
            }
            try:
                async with session.post(f"{monero_rpc}/json_rpc", json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    transfers = data.get("result", {}).get("in", [])
                    for t in transfers:
                        if t.get("amount") >= invoice.amount * 1e12:  # XMR to atomic units
                            invoice.tx_hash = t.get("txid", "")
                            invoice.status = "confirmed"
                            await self._notify_paid(invoice)
                            return True
            except Exception as e:
                logging.debug(f"XMR RPC: {e}")
        return False
    
    async def _notify_paid(self, invoice: Invoice):
        """Notify callbacks and webhook."""
        for cb in self.paid_callbacks:
            try:
                await cb(invoice) if asyncio.iscoroutinefunction(cb) else cb(invoice)
            except Exception as e:
                logging.error(f"Callback error: {e}")
        
        if self.webhook_url:
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json={
                    "invoice_id": invoice.id,
                    "amount": invoice.amount,
                    "currency": invoice.currency,
                    "product": invoice.product,
                    "tx_hash": invoice.tx_hash,
                    "status": invoice.status
                })
    
    async def check_all_pending(self):
        """Check all pending invoices."""
        for inv_id, inv in self.invoices.items():
            if inv.status == "pending":
                if inv.currency == "BTC":
                    await self.verify_btc_payment(inv)
                elif inv.currency == "XMR":
                    await self.verify_xmr_payment(inv)
    
    def export_invoices(self) -> list:
        """Export all invoices."""
        return [self.check_invoice(inv_id) for inv_id in self.invoices]

# FastAPI integration (optional)
def create_api(gateway: CryptoPaymentGateway):
    """Create FastAPI app for the gateway."""
    from fastapi import FastAPI
    app = FastAPI(title="Crypto Payment Gateway")
    
    @app.post("/invoice")
    def create_inv(amount: float, currency: str, product: str, email: str = ""):
        inv = gateway.create_invoice(amount, currency, product, email)
        return gateway.check_invoice(inv.id)
    
    @app.get("/invoice/{inv_id}")
    def check_inv(inv_id: str):
        return gateway.check_invoice(inv_id)
    
    @app.get("/invoices")
    def list_invoices():
        return gateway.export_invoices()
    
    return app

async def main():
    wallets = {
        "BTC": "bc1qexample...",
        "USDT": "0xExample...",
        "ETH": "0xExample...",
        "XMR": "4Example...",
    }
    gateway = CryptoPaymentGateway(wallets)
    
    # Create invoice
    inv = gateway.create_invoice(amount=49, currency="BTC", product="TG Bot Template")
    print(f"Invoice: {gateway.check_invoice(inv.id)}")
    
    # Register callback
    def on_paid(invoice):
        print(f"PAID: {invoice.amount} {invoice.currency} for {invoice.product}")
    gateway.on_paid(on_paid)
    
    print("Gateway ready. Use create_api() for FastAPI integration.")

if __name__ == "__main__":
    asyncio.run(main())
