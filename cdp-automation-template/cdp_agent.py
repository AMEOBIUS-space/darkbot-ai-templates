#!/usr/bin/env python3
"""CDP Browser Automation Template — anti-detection, CF bypass, Vue/React forms."""
import json, asyncio, websockets, urllib.request, logging

logging.basicConfig(level=logging.INFO)

class CDPAgent:
    """Chrome DevTools Protocol automation agent."""
    
    def __init__(self, port=9222):
        self.port = port
        self.ws = None
        self.msg_id = 0
    
    async def connect(self, tab_url_filter=None):
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=5).read())
        page_tabs = [t for t in tabs if t.get('type') == 'page']
        if tab_url_filter:
            page_tabs = [t for t in page_tabs if tab_url_filter in t.get('url', '')]
        if not page_tabs:
            raise Exception("No matching tab found")
        self.tab = page_tabs[0]
        self.ws = await websockets.connect(self.tab['webSocketDebuggerUrl'])
        return self.tab['id']
    
    async def navigate(self, url):
        await self._send("Page.navigate", {"url": url})
        await asyncio.sleep(5)
    
    async def eval_js(self, expression):
        result = await self._send("Runtime.evaluate", {
            "expression": expression, "returnByValue": True
        })
        return result.get('result', {}).get('result', {}).get('value')
    
    async def fill_input(self, selector, value):
        """Fill React/Vue input using native setter — bypasses framework state."""
        await self.eval_js(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                setter.call(el, '{value}');
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }})()
        """)
    
    async def click_element(self, selector):
        """Click via CDP mouse events — triggers real pointer events."""
        coords = await self.eval_js(f"""
            (() => {{
                const el = document.querySelector('{selector}');
                const rect = el.getBoundingClientRect();
                return JSON.stringify({{
                    x: Math.round(rect.x + rect.width/2),
                    y: Math.round(rect.y + rect.height/2)
                }});
            }})()
        """)
        if coords:
            c = json.loads(coords)
            await self._send("Input.dispatchMouseEvent", {
                "type": "mousePressed", "button": "left", "clickCount": 1,
                "x": c['x'], "y": c['y']
            })
            await self._send("Input.dispatchMouseEvent", {
                "type": "mouseReleased", "button": "left", "clickCount": 1,
                "x": c['x'], "y": c['y']
            })
    
    async def insert_text(self, text):
        """Insert text via CDP — works for React typeaheads."""
        await self._send("Input.insertText", {"text": text})
    
    async def _send(self, method, params):
        self.msg_id += 1
        await self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params}))
        return json.loads(await asyncio.wait_for(self.ws.recv(), timeout=15))
    
    async def close(self):
        if self.ws:
            await self.ws.close()

async def demo():
    agent = CDPAgent(port=9222)
    await agent.connect()
    await agent.navigate("https://example.com")
    title = await agent.eval_js("document.title")
    print(f"Page title: {title}")
    await agent.close()

if __name__ == "__main__":
    asyncio.run(demo())
