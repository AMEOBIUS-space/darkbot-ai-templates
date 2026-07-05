import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from monitor import WalletMonitor, Wallet, Transaction


def test_add_wallet():
    mon = WalletMonitor()
    w = mon.add_wallet("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC", "Savings")
    assert w.cryptocurrency == "BTC"
    assert w.label == "Savings"
    assert len(mon.wallets) == 1


def test_add_multiple_wallets():
    mon = WalletMonitor()
    mon.add_wallet("addr1", "BTC")
    mon.add_wallet("addr2", "ETH")
    mon.add_wallet("addr3", "XMR")
    assert len(mon.wallets) == 3


def test_set_balance_threshold():
    mon = WalletMonitor()
    mon.add_wallet("addr1", "BTC")
    mon.set_balance_threshold("addr1", "BTC", 0.01)
    assert mon.balance_thresholds["BTC:addr1"] == 0.01


def test_add_transaction_incoming():
    mon = WalletMonitor()
    tx = Transaction(tx_hash="abc123", cryptocurrency="BTC", from_addr="sender",
                     to_addr="receiver", amount=0.5, fee=0.0001, confirmations=6,
                     timestamp="2026-01-01T00:00:00Z", direction="incoming")
    mon.add_transaction(tx)
    assert len(mon.transactions) == 1
    assert len(mon.alerts) == 1
    assert mon.alerts[0]["type"] == "incoming_tx"


def test_add_transaction_outgoing():
    mon = WalletMonitor()
    tx = Transaction(tx_hash="xyz", cryptocurrency="ETH", from_addr="a",
                     to_addr="b", amount=1.0, fee=0.002, confirmations=3,
                     timestamp="2026-01-01", direction="outgoing")
    mon.add_transaction(tx)
    assert len(mon.alerts) == 0  # No alert for outgoing


def test_portfolio_value():
    mon = WalletMonitor()
    mon.add_wallet("addr1", "BTC")
    mon.wallets["BTC:addr1"].balance = 0.5
    mon.add_wallet("addr2", "ETH")
    mon.wallets["ETH:addr2"].balance = 10.0

    prices = {"BTC": 50000, "ETH": 3000}
    portfolio = mon.get_portfolio_value(prices)
    assert portfolio["total_usd"] == 25000 + 30000
    assert "BTC" in portfolio["breakdown"]
    assert portfolio["breakdown"]["BTC"]["value_usd"] == 25000


def test_portfolio_empty():
    mon = WalletMonitor()
    portfolio = mon.get_portfolio_value({"BTC": 50000})
    assert portfolio["total_usd"] == 0


def test_stats():
    mon = WalletMonitor()
    mon.add_wallet("a1", "BTC")
    mon.add_wallet("a2", "ETH")
    tx = Transaction("h", "BTC", "s", "r", 1.0, 0.01, 6, "now", "incoming")
    mon.add_transaction(tx)
    stats = mon.stats()
    assert stats["wallets"] == 2
    assert stats["transactions"] == 1
    assert stats["alerts"] == 1


def test_alerts_unread():
    mon = WalletMonitor()
    tx = Transaction("h", "BTC", "s", "r", 1.0, 0.01, 6, "now", "incoming")
    mon.add_transaction(tx)
    alerts = mon.get_alerts(unread_only=True)
    assert len(alerts) == 1
    mon.mark_alerts_read()
    alerts = mon.get_alerts(unread_only=True)
    assert len(alerts) == 0


def test_decimals():
    assert WalletMonitor.DECIMALS["BTC"] == 8
    assert WalletMonitor.DECIMALS["ETH"] == 18
    assert WalletMonitor.DECIMALS["XMR"] == 12


def test_api_endpoints():
    assert "blockchain.info" in WalletMonitor.API_ENDPOINTS["BTC"]
    assert "etherscan.io" in WalletMonitor.API_ENDPOINTS["ETH"]
    assert "xmrchain" in WalletMonitor.API_ENDPOINTS["XMR"]
