import os
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from playwright.async_api import async_playwright

SECRET_KEY = os.environ.get("API_SECRET", "sb-anidb-solver-691")

class SolveRequest(BaseModel):
    url: str

class SolveResponse(BaseModel):
    cf_clearance: str
    user_agent: str

app = FastAPI(title="CF Cookie Solver", version="1.0.0")


async def _solve(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--no-zygote",
                "--disable-setuid-sandbox",
                "--memory-pressure-off",
                "--disable-extensions",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Poll up to 45s for cf_clearance
        for _ in range(90):
            cookies = await context.cookies()
            cf = next((c for c in cookies if c["name"] == "cf_clearance"), None)
            if cf:
                ua = await page.evaluate("navigator.userAgent")
                await browser.close()
                return {"cf_clearance": cf["value"], "user_agent": ua}
            await asyncio.sleep(0.5)

        await browser.close()
        raise TimeoutError("cf_clearance not received after 45s")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest, x_secret: str = Header(...)):
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        result = await _solve(request.url)
        return SolveResponse(**result)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
