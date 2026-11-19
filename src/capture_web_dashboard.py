"""Capture verified dashboard views from a local HTTP preview."""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dashboards" / "screenshots" / "web"
URL = os.environ.get("TRANSITPULSE_DASHBOARD_URL", "http://127.0.0.1:4173/")
CHROME = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
VIEWS = [
    ("Overview", "overview"),
    ("Line performance", "line-performance"),
    ("Diagnostics", "diagnostics"),
    ("Priorities", "priorities"),
]


def check(page, name: str) -> None:
    body = page.locator("body").inner_text()
    for error in ("Chart configuration error", "Something went wrong", "NaN", "undefined"):
        if error in body:
            raise AssertionError(f"{name}: found {error!r} in rendered page")
    minimum = 1 if name == "Priorities" else 2
    if page.locator(".recharts-wrapper svg").count() < minimum:
        raise AssertionError(f"{name}: fewer than {minimum} rendered charts")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        desktop.goto(URL, wait_until="networkidle")
        for label, slug in VIEWS:
            desktop.get_by_text(label, exact=True).first.click()
            desktop.wait_for_timeout(500)
            check(desktop, label)
            if label == "Overview":
                for value in ("85.40%", "+1.52 pp", "3.24B min"):
                    if value not in desktop.locator("body").inner_text():
                        raise AssertionError(f"Overview is missing {value}")
            if label == "Line performance":
                desktop.locator(".tp-panel__heading select").select_option("B")
                if "78.74%" not in desktop.locator(".tp-line-stat").inner_text():
                    raise AssertionError("Line selector did not show B's reliability")
                desktop.locator(".tp-panel__heading select").select_option("F")
            desktop.screenshot(path=str(OUTPUT / f"{slug}.png"), full_page=True)
            print(f"Captured {slug}.png")
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.goto(URL, wait_until="networkidle")
        check(mobile, "Mobile overview")
        if mobile.locator("body").evaluate("element => element.scrollWidth > window.innerWidth + 2"):
            raise AssertionError("Mobile overview has horizontal overflow")
        mobile.screenshot(path=str(OUTPUT / "overview-mobile.png"), full_page=True)
        print("Captured overview-mobile.png")
        browser.close()


if __name__ == "__main__":
    main()
