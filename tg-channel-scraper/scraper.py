#!/usr/bin/env python3
"""Telegram Channel Scraper — monitor channels for keywords, export messages, analytics."""
import asyncio, json, re, logging, os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Set

logging.basicConfig(level=logging.INFO)

@dataclass
class ScrapedMessage:
    id: int
    channel: str
    text: str
    date: datetime
    sender: str = ""
    views: int = 0
    reactions: int = 0
    has_media: bool = False
    keywords_matched: List[str] = field(default_factory=list)

class ChannelScraper:
    """Scrape Telegram channels for messages matching keywords."""
    
    def __init__(self, api_id: int, api_hash: str, session: str = ""):
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        self.api_id = api_id
        self.api_hash = api_hash
        self.session = session
        self.client = None
    
    async def connect(self):
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        sess = StringSession(self.session) if self.session else "scraper_session"
        self.client = TelegramClient(sess, self.api_id, self.api_hash)
        await self.client.connect()
        return self.client
    
    async def scrape_channel(
        self,
        channel: str,
        keywords: List[str] = None,
        limit: int = 100,
        days_back: int = 7
    ) -> List[ScrapedMessage]:
        """Scrape channel for messages matching keywords."""
        results = []
        cutoff = datetime.now() - timedelta(days=days_back)
        kw_lower = [k.lower() for k in (keywords or [])]
        
        async for msg in self.client.iter_messages(channel, limit=limit):
            if msg.date < cutoff:
                break
            
            text = msg.text or ""
            matched = []
            if kw_lower:
                text_lower = text.lower()
                matched = [k for k in kw_lower if k in text_lower]
                if not matched:
                    continue
            
            scraped = ScrapedMessage(
                id=msg.id,
                channel=channel,
                text=text[:500],
                date=msg.date,
                sender=str(msg.sender_id) if msg.sender_id else "",
                views=msg.views or 0,
                reactions=sum(r.count for r in (getattr(msg.reactions, 'results', []) or [])) if msg.reactions else 0,
                has_media=bool(msg.media),
                keywords_matched=matched
            )
            results.append(scraped)
        
        logging.info(f"[{channel}] Scraped {len(results)} messages (keywords: {len(matched) if kw_lower else 'all'})")
        return results
    
    async def scrape_multiple(
        self,
        channels: List[str],
        keywords: List[str] = None,
        limit: int = 50,
        days_back: int = 7
    ) -> dict[str, List[ScrapedMessage]]:
        """Scrape multiple channels."""
        all_results = {}
        for ch in channels:
            try:
                msgs = await self.scrape_channel(ch, keywords, limit, days_back)
                all_results[ch] = msgs
            except Exception as e:
                logging.error(f"[{ch}] Error: {e}")
                all_results[ch] = []
        return all_results
    
    def export_json(self, results: dict, path: str):
        """Export to JSON."""
        data = {}
        for ch, msgs in results.items():
            data[ch] = [{
                "id": m.id, "text": m.text, "date": m.date.isoformat(),
                "sender": m.sender, "views": m.views, "reactions": m.reactions,
                "has_media": m.has_media, "keywords": m.keywords_matched
            } for m in msgs]
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Exported to {path}")
    
    def export_csv(self, results: dict, path: str):
        """Export to CSV."""
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["channel", "id", "date", "sender", "views", "reactions", "text", "keywords"])
            for ch, msgs in results.items():
                for m in msgs:
                    w.writerow([ch, m.id, m.date.isoformat(), m.sender, m.views, m.reactions, m.text[:200], ",".join(m.keywords_matched)])
        logging.info(f"Exported CSV to {path}")
    
    def analytics(self, results: dict) -> dict:
        """Generate analytics summary."""
        total = sum(len(msgs) for msgs in results.values())
        total_views = sum(m.views for msgs in results.values() for m in msgs)
        total_reactions = sum(m.reactions for msgs in results.values() for m in msgs)
        by_channel = {ch: len(msgs) for ch, msgs in results.items()}
        keyword_counts = {}
        for msgs in results.values():
            for m in msgs:
                for kw in m.keywords_matched:
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        return {
            "total_messages": total,
            "total_views": total_views,
            "total_reactions": total_reactions,
            "by_channel": by_channel,
            "keyword_counts": dict(sorted(keyword_counts.items(), key=lambda x: -x[1])),
        }
    
    async def close(self):
        if self.client:
            await self.client.disconnect()

async def main():
    # Demo — requires Telethon session
    scraper = ChannelScraper(
        api_id=2040,
        api_hash="your_api_hash",
        session="your_session_string"
    )
    # Example usage (commented — needs valid session)
    # await scraper.connect()
    # results = await scraper.scrape_multiple(
    #     channels=["channel1", "channel2"],
    #     keywords=["python", "bot", "freelance"],
    #     limit=100,
    #     days_back=7
    # )
    # scraper.export_json(results, "scraped.json")
    # print(scraper.analytics(results))
    # await scraper.close()
    print("Template ready. Set api_id, api_hash, session to start scraping.")

if __name__ == "__main__":
    asyncio.run(main())
