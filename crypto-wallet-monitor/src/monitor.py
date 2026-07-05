"""Crypto Wallet Monitor — track BTC/ETH/XMR balances and transactions."""
import json
import time
import urllib.request
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Wallet:
    address: str
    cryptocurrency: str  # BTC, ETH, XMR
    label: str = ""
    balance: float = 0.0
    last_checked: str = ""


@dataclass
class Transaction:
    tx_hash: str
    cryptocurrency: str
    from_addr: str
    to_addr: str
    amount: float
    fee: float
    confirmations: int
    timestamp: str
    direction: str = "unknown"  # incoming, outgoing, internal


class WalletMonitor:
    """Monitor crypto wallet balances and transactions across multiple chains."""

    API_ENDPOINTS = {
        "BTC": "https://blockchain.info/rawaddr/{address}",
        "ETH": "https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest",
        "XMR": "https://xmrchain.net/api/outputs/{address}",
    }

    DECIMALS = {"BTC": 8, "ETH": 18, "XMR": 12}

    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
        self.transactions: List[Transaction] = []
        self.alerts: List[Dict] = []
        self.min_confirmations = 3
        self.balance_thresholds: Dict[str, float] = {}

    def add_wallet(self, address: str, cryptocurrency: str, label: str = "") -> Wallet:
        key = f"{cryptocurrency}:{address}"
        wallet = Wallet(address=address, cryptocurrency=cryptocurrency.upper(), label=label)
        self.wallets[key] = wallet
        return wallet

    def set_balance_threshold(self, address: str, cryptocurrency: str, min_balance: float):
        key = f"{cryptocurrency}:{address}"
        self.balance_thresholds[key] = min_balance

    def fetch_balance(self, wallet: Wallet) -> Optional[float]:
        """Fetch current balance from blockchain API."""
        try:
            url = self.API_ENDPOINTS.get(wallet.cryptocurrency, "").format(address=wallet.address)
            if not url:
                return None
            resp = urllib.request.urlopen(url, timeout=15)
            data = json.loads(resp.read())

            if wallet.cryptocurrency == "BTC":
                return data.get("final_balance", 0) / 10**8
            elif wallet.cryptocurrency == "ETH":
                return int(data.get("result", 0)) / 10**18
            elif wallet.cryptocurrency == "XMR":
                return float(data.get("balance", 0)) / 10**12
        except Exception:
            return None

    def check_all_balances(self) -> Dict[str, float]:
        """Check balances for all wallets."""
        results = {}
        for key, wallet in self.wallets.items():
            balance = self.fetch_balance(wallet)
            if balance is not None:
                old_balance = wallet.balance
                wallet.balance = balance
                wallet.last_checked = datetime.now().isoformat()
                results[key] = balance

                if old_balance != balance and old_balance > 0:
                    self.alerts.append({
                        "type": "balance_change",
                        "wallet": key,
                        "old": old_balance,
                        "new": balance,
                        "diff": balance - old_balance,
                        "timestamp": wallet.last_checked,
                    })

                threshold = self.balance_thresholds.get(key)
                if threshold and balance < threshold:
                    self.alerts.append({
                        "type": "low_balance",
                        "wallet": key,
                        "balance": balance,
                        "threshold": threshold,
                        "timestamp": wallet.last_checked,
                    })
        return results

    def add_transaction(self, tx: Transaction):
        self.transactions.append(tx)
        if tx.direction == "incoming":
            self.alerts.append({
                "type": "incoming_tx",
                "tx_hash": tx.tx_hash,
                "amount": tx.amount,
                "cryptocurrency": tx.cryptocurrency,
                "timestamp": tx.timestamp,
            })

    def get_portfolio_value(self, prices: Dict[str, float]) -> Dict:
        """Calculate portfolio value given current prices."""
        by_crypto = {}
        for wallet in self.wallets.values():
            crypto = wallet.cryptocurrency
            by_crypto.setdefault(crypto, 0)
            by_crypto[crypto] += wallet.balance

        total_usd = 0
        breakdown = {}
        for crypto, amount in by_crypto.items():
            price = prices.get(crypto, 0)
            value = amount * price
            breakdown[crypto] = {"amount": amount, "price": price, "value_usd": value}
            total_usd += value

        return {"total_usd": total_usd, "breakdown": breakdown}

    def get_alerts(self, unread_only: bool = False) -> List[Dict]:
        alerts = self.alerts
        if unread_only:
            alerts = [a for a in alerts if not a.get("read")]
        return alerts

    def mark_alerts_read(self):
        for alert in self.alerts:
            alert["read"] = True

    def stats(self) -> Dict:
        return {
            "wallets": len(self.wallets),
            "transactions": len(self.transactions),
            "alerts": len(self.alerts),
            "unread_alerts": sum(1 for a in self.alerts if not a.get("read")),
        }
