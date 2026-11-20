"""Capture verified dashboard views from a local HTTP preview."""

from __future__ import annotations

import os
import re
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
    minimum = 1 if name.endswith("Priorities") else 2
    if page.locator(".recharts-wrapper svg").count() < minimum:
        raise AssertionError(f"{name}: fewer than {minimum} rendered charts")


def contrast(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(value) / 255 for value in re.findall(r"\d+", color)[:3]]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    darker, lighter = sorted((luminance(first), luminance(second)))
    return (lighter + 0.05) / (darker + 0.05)


def check_text_contrast(page, name: str) -> None:
    colors = page.evaluate("""() => {
      const style = (selector) => getComputedStyle(document.querySelector(selector));
      return {
        background: style('body').backgroundColor,
        heading: style('.tp-intro h1').color,
        panel: style('.tp-panel').backgroundColor,
        tick: style('.recharts-cartesian-axis-tick-value').fill,
        note: style('.tp-panel .tp-note').color,
      };
    }""")
    for label, foreground, background in (
        ("heading", colors["heading"], colors["background"]),
        ("chart tick", colors["tick"], colors["panel"]),
        ("chart note", colors["note"], colors["panel"]),
    ):
        ratio = contrast(foreground, background)
        if ratio < 4.5:
            raise AssertionError(f"{name}: {label} contrast is only {ratio:.2f}:1")


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
            check_text_contrast(desktop, f"Light {label}")
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
        dark = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1, color_scheme="dark")
        dark.goto(URL, wait_until="networkidle")
        for label, slug in VIEWS:
            dark.get_by_text(label, exact=True).first.click()
            dark.wait_for_timeout(500)
            check(dark, f"Dark {label}")
            check_text_contrast(dark, f"Dark {label}")
            dark.screenshot(path=str(OUTPUT / f"{slug}-dark.png"), full_page=True)
            print(f"Captured {slug}-dark.png")
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        mobile.goto(URL, wait_until="networkidle")
        check(mobile, "Mobile overview")
        if mobile.locator("body").evaluate("element => element.scrollWidth > window.innerWidth + 2"):
            raise AssertionError("Mobile overview has horizontal overflow")
        mobile.screenshot(path=str(OUTPUT / "overview-mobile.png"), full_page=True)
        print("Captured overview-mobile.png")
        dark_mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1, color_scheme="dark")
        dark_mobile.goto(URL, wait_until="networkidle")
        check(dark_mobile, "Dark mobile overview")
        check_text_contrast(dark_mobile, "Dark mobile overview")
        if dark_mobile.locator("body").evaluate("element => element.scrollWidth > window.innerWidth + 2"):
            raise AssertionError("Dark mobile overview has horizontal overflow")
        dark_mobile.screenshot(path=str(OUTPUT / "overview-mobile-dark.png"), full_page=True)
        print("Captured overview-mobile-dark.png")
        browser.close()


if __name__ == "__main__":
    main()
