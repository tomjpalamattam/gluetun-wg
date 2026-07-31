import asyncio
import os
import sys
from playwright.async_api import async_playwright


async def download_purevpn_wg(
    email: str,
    password: str,
    city_name: str = "Frankfurt",
    protocol: str = "WireGuard",
    device: str = "linux",
    output_path: str = "wg0.conf",
    headless: bool = False,
):
    """
    Downloads a WireGuard config from PureVPN's dashboard.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,  # headless=True gets detected and stalls; run under Xvfb instead
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        # ========== LOGIN ==========
        print("Logging in...", flush=True)
        await page.goto("https://my.purevpn.com/login", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await page.fill('input#loginId', email)
        await page.fill('input#password', password)
        await page.press('input#password', 'Enter')
        await page.wait_for_timeout(3000)

        if "oauth-callback" in page.url:
            await page.goto("https://my.purevpn.com/v2/dashboard/security-tools", wait_until="networkidle")
            await page.wait_for_timeout(2000)

        # ========== MANUAL CONFIG ==========
        print("Opening manual configuration...", flush=True)
        await page.goto("https://my.purevpn.com/v2/dashboard/manual-config", wait_until="networkidle")
        await page.wait_for_timeout(4000)

        wg_tab = await page.query_selector('button:has-text("WireGuard")')
        if wg_tab:
            is_active = await wg_tab.evaluate('el => el.classList.contains("active")')
            if not is_active:
                print("Selecting WireGuard tab...", flush=True)
                await wg_tab.click()
                await page.wait_for_timeout(2000)

        # ========== SEARCH CITY ==========
        print(f"Searching for '{city_name}'...", flush=True)
        search_input = await page.query_selector('input[type="search"]')
        await search_input.fill(city_name)
        await page.wait_for_timeout(2000)

        # ========== OPEN DOWNLOAD MODAL ==========
        print("Clicking download button...", flush=True)
        download_btn = await page.query_selector('button:has-text("Download")')
        await download_btn.click()
        await page.wait_for_timeout(2000)

        # ========== SELECT PROTOCOL ==========
        print(f"Selecting protocol: {protocol}...", flush=True)
        await page.wait_for_selector('select[name="select"]', timeout=10000)
        await page.select_option('select[name="select"]', protocol)
        await page.wait_for_timeout(1500)

        # ========== SELECT DEVICE ==========
        print(f"Selecting device: {device}...", flush=True)
        await page.wait_for_selector('select#device', timeout=10000)
        await page.select_option('select#device', device)
        await page.wait_for_timeout(1500)

        # ========== GENERATE ==========
        print("Generating configuration...", flush=True)
        generate_btn = await page.query_selector('button:has-text("Generate Configuration")')

        async with page.expect_download(timeout=30000) as download_info:
            await generate_btn.click()
            print("Waiting for config generation & download...", flush=True)

        download = await download_info.value
        await download.save_as(output_path)

        print(f"Config saved: {output_path}", flush=True)
        print(f"Suggested filename: {download.suggested_filename}", flush=True)

        await browser.close()
        return output_path


def main():
    email = os.environ.get("PUREVPN_EMAIL")
    password = os.environ.get("PUREVPN_PASSWORD")
    city_name = os.environ.get("CITY_NAME", "Frankfurt")
    protocol = os.environ.get("PROTOCOL", "WireGuard")
    device = os.environ.get("DEVICE", "linux")
    output_path = os.environ.get("OUTPUT_PATH", "/output/wg0.conf")

    if not email or not password:
        print("ERROR: PUREVPN_EMAIL and PUREVPN_PASSWORD must be set.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(
        download_purevpn_wg(
            email=email,
            password=password,
            city_name=city_name,
            protocol=protocol,
            device=device,
            output_path=output_path,
            headless=False,
        )
    )


if __name__ == "__main__":
    main()
