import os
import sys
import time
from playwright.sync_api import sync_playwright

PAGES = [
    ("risk_map", "/"),
    ("district_detail", "/district?district=Akola&crop=Cotton"),
    ("season_tracker", "/early-warning?district=Akola&crop=Cotton"),
    ("scenario_lab", "/scenario?district=Akola&crop=Cotton&temp=2.0&precip=-0.2"),
    ("crop_reliability", "/reliability?district=Akola"),
    ("climate_analogs", "/analogs?district=Akola&temp=2.0&precip=-0.2"),
    ("evidence", "/evidence"),
    ("privacy", "/privacy"),
    ("terms", "/terms"),
    ("not_found", "/unknown-route-test-404")
]

VIEWPORTS = [
    ("1440px", {"width": 1440, "height": 900}),
    ("390px", {"width": 390, "height": 844})
]

OUTPUT_DIR = "docs/screenshots"

def run_verification():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_url = "http://localhost:5173"
    
    console_errors = []
    page_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        for vp_name, vp_size in VIEWPORTS:
            print(f"\n--- Testing Viewport: {vp_name} ({vp_size['width']}x{vp_size['height']}) ---")
            context = browser.new_context(viewport=vp_size)
            page = context.new_page()
            
            # Listen for errors
            page.on("console", lambda msg: console_errors.append(f"[{vp_name}] {msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("pageerror", lambda err: page_errors.append(f"[{vp_name}] PageError: {str(err)}"))
            
            for page_name, route in PAGES:
                target_url = f"{base_url}{route}"
                print(f"Opening: {target_url} [{page_name}] ...")
                
                resp = page.goto(target_url, wait_until="networkidle")
                assert resp is not None, f"Failed to navigate to {target_url}"
                
                # Wait for content rendering
                time.sleep(1.0)
                
                # Capture screenshot
                shot_path = os.path.join(OUTPUT_DIR, f"{page_name}_{vp_name}.png")
                page.screenshot(path=shot_path, full_page=False)
                print(f"  -> Captured screenshot: {shot_path}")
                
            context.close()
            
        browser.close()

    print("\n--- Summary of Verification ---")
    if page_errors:
        print(f"FAILED: {len(page_errors)} page errors encountered:")
        for pe in page_errors:
            print("  *", pe)
        sys.exit(1)
        
    if console_errors:
        print(f"WARNING/ERRORS: {len(console_errors)} console errors logged:")
        for ce in console_errors:
            print("  *", ce)
        # Filter out harmless network favicon or benign warnings if any
        critical_errors = [ce for ce in console_errors if "favicon" not in ce.lower()]
        if critical_errors:
            print(f"FAILED: {len(critical_errors)} critical console errors!")
            sys.exit(1)
            
    print(f"SUCCESS: All {len(PAGES)} pages rendered cleanly at 1440px and 390px with 0 errors!")
    print(f"All screenshots saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    run_verification()
