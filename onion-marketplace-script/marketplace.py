#!/usr/bin/env python3
"""Tor .onion Marketplace Script — vendor listings, escrow, XMR/BTC payments."""
import os, json, hashlib, time, logging
from dataclasses import dataclass, field
from typing import Optional, List

logging.basicConfig(level=logging.INFO)

@dataclass
class Listing:
    id: str
    title: str
    description: str
    price: float
    currency: str  # XMR, BTC
    vendor: str
    category: str
    ships_from: str = ""
    ships_to: str = ""
    rating: float = 0
    sales: int = 0
    created_at: float = field(default_factory=time.time)

@dataclass
class Order:
    id: str
    listing_id: str
    buyer: str
    vendor: str
    amount: float
    currency: str
    status: str = "pending"  # pending, escrow, shipped, completed, disputed
    escrow_tx: str = ""
    created_at: float = field(default_factory=time.time)

class OnionMarketplace:
    """Simple .onion marketplace backend."""
    
    def __init__(self, db_path: str = "marketplace.json"):
        self.db_path = db_path
        self.listings: List[Listing] = []
        self.orders: List[Order] = []
        self.escrow_addresses = {"XMR": "4darkbot...", "BTC": "bc1qdarkbot..."}
        self._load()
    
    def _load(self):
        try:
            with open(self.db_path) as f:
                data = json.load(f)
                self.listings = [Listing(**l) for l in data.get("listings", [])]
                self.orders = [Order(**o) for o in data.get("orders", [])]
        except FileNotFoundError:
            pass
    
    def _save(self):
        with open(self.db_path, "w") as f:
            json.dump({
                "listings": [l.__dict__ for l in self.listings],
                "orders": [o.__dict__ for o in self.orders],
            }, f, indent=2)
    
    def add_listing(self, title, desc, price, currency, vendor, category, ships_from="", ships_to="") -> Listing:
        lid = hashlib.sha256(f"{time.time()}{title}{vendor}".encode()).hexdigest()[:12]
        listing = Listing(id=lid, title=title, description=desc, price=price,
                         currency=currency, vendor=vendor, category=category,
                         ships_from=ships_from, ships_to=ships_to)
        self.listings.append(listing)
        self._save()
        logging.info(f"Listing added: {title} ({price} {currency})")
        return listing
    
    def search(self, query: str = "", category: str = "") -> List[Listing]:
        results = self.listings
        if query:
            q = query.lower()
            results = [l for l in results if q in l.title.lower() or q in l.description.lower()]
        if category:
            results = [l for l in results if l.category == category]
        return results
    
    def place_order(self, listing_id: str, buyer: str) -> Order:
        listing = next((l for l in self.listings if l.id == listing_id), None)
        if not listing:
            raise ValueError("Listing not found")
        oid = hashlib.sha256(f"{time.time()}{listing_id}{buyer}".encode()).hexdigest()[:12]
        order = Order(id=oid, listing_id=listing_id, buyer=buyer, vendor=listing.vendor,
                     amount=listing.price, currency=listing.currency, status="escrow")
        self.orders.append(order)
        self._save()
        logging.info(f"Order placed: {oid} ({listing.price} {listing.currency})")
        return order
    
    def get_escrow_address(self, currency: str) -> str:
        return self.escrow_addresses.get(currency, "")
    
    def confirm_payment(self, order_id: str, tx_hash: str):
        order = next((o for o in self.orders if o.id == order_id), None)
        if order:
            order.escrow_tx = tx_hash
            order.status = "shipped"
            self._save()
            logging.info(f"Payment confirmed for order {order_id}")
    
    def complete_order(self, order_id: str):
        order = next((o for o in self.orders if o.id == order_id), None)
        if order:
            order.status = "completed"
            self._save()
            logging.info(f"Order {order_id} completed")
    
    def stats(self) -> dict:
        return {
            "listings": len(self.listings),
            "orders": len(self.orders),
            "pending": sum(1 for o in self.orders if o.status == "pending"),
            "escrow": sum(1 for o in self.orders if o.status == "escrow"),
            "completed": sum(1 for o in self.orders if o.status == "completed"),
        }

def main():
    mp = OnionMarketplace()
    # Demo listings
    mp.add_listing("Custom Python Bot", "TG/Discord bot development", 0.5, "XMR", "darkbot", "services")
    mp.add_listing("Web Scraper Script", "Anti-detection scraper", 0.3, "XMR", "darkbot", "services")
    
    print(f"Stats: {mp.stats()}")
    print(f"Search 'bot': {[l.title for l in mp.search('bot')]}")
    
    # Place order
    order = mp.place_order(mp.listings[0].id, "buyer123")
    print(f"Order: {order.id} status={order.status}")
    print(f"Escrow: {mp.get_escrow_address('XMR')}")
    
    mp.confirm_payment(order.id, "tx123")
    print(f"After payment: {order.status}")

if __name__ == "__main__":
    main()
