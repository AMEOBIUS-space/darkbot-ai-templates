#!/usr/bin/env python3
"""Captcha Solver Template — coordinate reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile, Yandex SmartCaptcha.
Multi-strategy approach: 2Captcha API, CapSolver, local ML (optional)."""
import asyncio, time, logging, os, json, base64
from typing import Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)

@dataclass
class CaptchaResult:
    success: bool
    token: str = ""
    raw_response: dict = None
    elapsed_seconds: float = 0

class CaptchaSolver:
    """Multi-provider captcha solver with fallback."""
    
    def __init__(self, twocaptcha_key: str = "", capsolver_key: str = ""):
        self.twocaptcha_key = twocaptcha_key or os.getenv("TWOCAPTCHA_KEY", "")
        self.capsolver_key = capsolver_key or os.getenv("CAPSOLVER_KEY", "")
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> CaptchaResult:
        """Solve reCAPTCHA v2 via 2Captcha."""
        import aiohttp
        start = time.time()
        
        if not self.twocaptcha_key:
            return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
        
        async with aiohttp.ClientSession() as session:
            # Submit
            data = {
                "key": self.twocaptcha_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
            async with session.post("https://2captcha.com/in.php", data=data) as resp:
                result = await resp.json()
                if result.get("status") != 1:
                    return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
                captcha_id = result["request"]
            
            # Poll for result
            for _ in range(30):
                await asyncio.sleep(5)
                async with session.get(f"https://2captcha.com/res.php?key={self.twocaptcha_key}&action=get&id={captcha_id}&json=1") as resp:
                    result = await resp.json()
                    if result.get("status") == 1:
                        return CaptchaResult(success=True, token=result["request"], raw_response=result, elapsed_seconds=time.time() - start)
                    if "CAPCHA_NOT_READY" not in result.get("request", ""):
                        return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
        
        return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
    
    async def solve_hcaptcha(self, site_key: str, page_url: str) -> CaptchaResult:
        """Solve hCaptcha via CapSolver."""
        import aiohttp
        start = time.time()
        
        if not self.capsolver_key:
            return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
        
        async with aiohttp.ClientSession() as session:
            # Create task
            payload = {
                "clientKey": self.capsolver_key,
                "task": {
                    "type": "HCaptchaTaskProxyLess",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }
            async with session.post("https://api.capsolver.com/createTask", json=payload) as resp:
                result = await resp.json()
                if result.get("errorId"):
                    return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
                task_id = result["taskId"]
            
            # Poll
            for _ in range(30):
                await asyncio.sleep(3)
                payload = {"clientKey": self.capsolver_key, "taskId": task_id}
                async with session.post("https://api.capsolver.com/getTaskResult", json=payload) as resp:
                    result = await resp.json()
                    if result.get("status") == "ready":
                        token = result["solution"]["gRecaptchaResponse"]
                        return CaptchaResult(success=True, token=token, raw_response=result, elapsed_seconds=time.time() - start)
                    if result.get("errorId"):
                        return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
        
        return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
    
    async def solve_cloudflare_turnstile(self, site_key: str, page_url: str) -> CaptchaResult:
        """Solve Cloudflare Turnstile via CapSolver."""
        import aiohttp
        start = time.time()
        
        if not self.capsolver_key:
            return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "clientKey": self.capsolver_key,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }
            async with session.post("https://api.capsolver.com/createTask", json=payload) as resp:
                result = await resp.json()
                if result.get("errorId"):
                    return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
                task_id = result["taskId"]
            
            for _ in range(30):
                await asyncio.sleep(3)
                payload = {"clientKey": self.capsolver_key, "taskId": task_id}
                async with session.post("https://api.capsolver.com/getTaskResult", json=payload) as resp:
                    result = await resp.json()
                    if result.get("status") == "ready":
                        token = result["solution"]["token"]
                        return CaptchaResult(success=True, token=token, raw_response=result, elapsed_seconds=time.time() - start)
                    if result.get("errorId"):
                        return CaptchaResult(success=False, raw_response=result, elapsed_seconds=time.time() - start)
        
        return CaptchaResult(success=False, elapsed_seconds=time.time() - start)
    
    async def solve_yandex_smartcaptcha(self, site_key: str, page_url: str) -> CaptchaResult:
        """Solve Yandex SmartCaptcha — CDP checkbox click approach."""
        # Yandex SmartCaptcha often just needs checkbox click via CDP
        # This is a template — implement via CDP mouse events
        start = time.time()
        logging.info("Yandex SmartCaptcha: use CDP checkbox click (see cdp_agent.py template)")
        return CaptchaResult(success=False, token="CDP approach needed", elapsed_seconds=time.time() - start)

async def main():
    solver = CaptchaSolver(
        twocaptcha_key=os.getenv("TWOCAPTCHA_KEY", ""),
        capsolver_key=os.getenv("CAPSOLVER_KEY", "")
    )
    # Demo
    print("Captcha Solver template ready.")
    print("Set TWOCAPTCHA_KEY and CAPSOLVER_KEY env vars to start solving.")
    print("Supports: reCAPTCHA v2, hCaptcha, Cloudflare Turnstile, Yandex SmartCaptcha")

if __name__ == "__main__":
    asyncio.run(main())
