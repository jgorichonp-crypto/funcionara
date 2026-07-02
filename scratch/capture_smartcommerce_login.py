import asyncio
import json
from playwright.async_api import async_playwright

email = "soporte.mundoaura@gmail.com"
password = "Limoncito.3"

log_file = "scratch/capture_login.log"

def log(msg):
    print(msg)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def capture():
    # Clear log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("")

    async with async_playwright() as p:
        log("Launching Chromium...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Monitor all requests and responses
        async def handle_request(request):
            if "api" in request.url:
                log(f"\n[REQUEST] URL: {request.url}")
                log(f"Method: {request.method}")
                log(f"Headers: {json.dumps(dict(request.headers), indent=2)}")
                try:
                    post_data = request.post_data
                    if post_data:
                        log(f"Payload: {post_data}")
                except Exception as e:
                    pass

        async def handle_response(response):
            if "api" in response.url:
                log(f"[RESPONSE] URL: {response.url}")
                log(f"Status: {response.status}")
                try:
                    text = await response.text()
                    log(f"Response Body: {text[:1000]}")
                except Exception as e:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        log("Navigating to https://app.smartcommerce.lat/sign-in...")
        await page.goto("https://app.smartcommerce.lat/sign-in")
        
        # Wait for selectors
        log("Waiting for inputs...")
        await page.wait_for_selector("input[type='email']")
        
        # Fill credentials
        log("Filling credentials...")
        await page.fill("input[type='email']", email)
        await page.fill("input[type='password']", password)
        
        # Click submit button
        log("Submitting login form...")
        await page.click("button[type='submit']")
        
        # Wait a few seconds for network requests to complete
        await page.wait_for_timeout(7000)
        
        # Check localStorage
        local_storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
        log("\n[LOCAL STORAGE]")
        log(local_storage)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture())
