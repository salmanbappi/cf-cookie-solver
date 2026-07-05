import os
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from cloakbrowser import launch_async

SECRET_KEY = os.environ.get("API_SECRET", "sb-anidb-solver-691")

class SolveRequest(BaseModel):
    url: str

class SolveResponse(BaseModel):
    cf_clearance: str
    user_agent: str

app = FastAPI(title="CF Cookie Solver", version="2.2.0")


async def _launch_browser():
    return await launch_async(
        headless=False,
        humanize=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug")
async def debug(url: str = "https://anidb.app", x_secret: str = Header(...)):
    """Debug: navigate to URL, wait 15s, return page state + all cookies."""
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    browser = await _launch_browser()
    try:
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            pass
        await asyncio.sleep(15)
        cookies = await page.context.cookies()
        title = await page.title()
        current_url = page.url
        html_snippet = (await page.content())[:2000]
        return {
            "title": title,
            "url": current_url,
            "cookies": cookies,
            "html_snippet": html_snippet,
        }
    finally:
        await browser.close()


@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest, x_secret: str = Header(...)):
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    browser = await _launch_browser()
    try:
        page = await browser.new_page()
        try:
            await page.goto(request.url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass
        context = page.context
        for _ in range(120):
            cookies = await context.cookies()
            cf = next((c for c in cookies if c["name"] == "cf_clearance"), None)
            if cf:
                ua = await page.evaluate("navigator.userAgent")
                return SolveResponse(cf_clearance=cf["value"], user_agent=ua)
            await asyncio.sleep(0.5)
        raise TimeoutError("cf_clearance not received after 60s")
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await browser.close()
