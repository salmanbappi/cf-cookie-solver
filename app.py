import os
import asyncio
import random
import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from cloakbrowser import launch_async

SECRET_KEY = os.environ.get("API_SECRET", "sb-anidb-solver-691")
WEBSHARE_KEY = os.environ.get("WEBSHARE_KEY", "")

class SolveRequest(BaseModel):
    url: str

class SolveResponse(BaseModel):
    cf_clearance: str
    user_agent: str

app = FastAPI(title="CF Cookie Solver", version="3.0.0")
PROXIES: list[str] = []


async def fetch_proxies() -> list[str]:
    if not WEBSHARE_KEY:
        return []
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page_size=25",
            headers={"Authorization": f"Token {WEBSHARE_KEY}"},
            timeout=10,
        )
        data = r.json()
        return [
            f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['port']}"
            for p in data.get("results", []) if p.get("valid")
        ]


@app.on_event("startup")
async def startup():
    global PROXIES
    PROXIES = await fetch_proxies()
    print(f"[startup] Loaded {len(PROXIES)} proxies")


async def _solve(url: str, proxy: str | None) -> dict:
    kwargs = dict(
        headless=False,
        humanize=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    if proxy:
        kwargs["proxy"] = proxy
        kwargs["geoip"] = True

    browser = await launch_async(**kwargs)
    try:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass
        for _ in range(120):
            cookies = await page.context.cookies()
            cf = next((c for c in cookies if c["name"] == "cf_clearance"), None)
            if cf:
                ua = await page.evaluate("navigator.userAgent")
                return {"cf_clearance": cf["value"], "user_agent": ua}
            await asyncio.sleep(0.5)
        raise TimeoutError("cf_clearance not received after 60s")
    finally:
        await browser.close()


@app.get("/health")
async def health():
    return {"status": "ok", "proxies": len(PROXIES)}


@app.get("/debug")
async def debug(url: str = "https://anidb.app", x_secret: str = Header(...)):
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    proxy = random.choice(PROXIES) if PROXIES else None
    browser = await launch_async(
        headless=False, humanize=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        **({"proxy": proxy, "geoip": True} if proxy else {})
    )
    try:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        await asyncio.sleep(15)
        cookies = await page.context.cookies()
        return {
            "proxy_used": proxy.split("@")[-1] if proxy else None,
            "title": await page.title(),
            "url": page.url,
            "cookies": [c["name"] for c in cookies],
            "html_snippet": (await page.content())[:1000],
        }
    finally:
        await browser.close()


@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest, x_secret: str = Header(...)):
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    proxy = random.choice(PROXIES) if PROXIES else None
    try:
        result = await _solve(request.url, proxy)
        return SolveResponse(**result)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
