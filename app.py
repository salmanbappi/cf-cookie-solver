import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import undetected_chromedriver as uc

SECRET_KEY = os.environ.get("API_SECRET", "sb-anidb-solver-691")

class SolveRequest(BaseModel):
    url: str

class SolveResponse(BaseModel):
    cf_clearance: str
    user_agent: str

app = FastAPI(title="CF Cookie Solver", version="1.0.0")


def _solve_blocking(url: str) -> dict:
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")

    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        for _ in range(60):
            cookie = driver.get_cookie("cf_clearance")
            if cookie:
                ua = driver.execute_script("return navigator.userAgent")
                return {"cf_clearance": cookie["value"], "user_agent": ua}
            time.sleep(0.5)
        raise TimeoutError("cf_clearance not set after 30s")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest, x_secret: str = Header(...)):
    if x_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _solve_blocking, request.url)
        return SolveResponse(**result)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
