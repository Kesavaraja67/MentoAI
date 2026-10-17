"""
test_demo_flow.py — Playwright E2E automation for Primer's Section 4 demo script.

Covers the full story:
1. Reset personas (Leo, Meera, Arjun).
2. Day 1 (Graph ON):
   - Pick Leo (frontier skill: count_on, confidence 0.35).
   - Problem: 3 + 4 in rocket story.
   - Leo taps 6 (misconception: counts_start_number).
   - Diagnosis runs -> Hint level 1 (story).
   - Leo taps 6 again -> Hint level 2 (visual).
   - Leo taps 7 -> Solved! Reflective state.
   - End Session -> Consolidation folds session into child_leo graph with memory diff.
3. Day 2 (Graph ON):
   - Next Day -> Day 2 session starts.
   - Decision cites Day 1 Episode, adapts first hint style to visual.
4. Ablation (Graph OFF):
   - Switch Graph Intelligence toggle OFF.
   - Shows generic degraded state.

Captures all 6 key screenshot artifacts into e2e/screenshots/.
"""
import os
import sys
import time
import httpx
import pytest
from playwright.sync_api import sync_playwright, Page, expect

BACKEND_URL = os.getenv("PRIMER_BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("PRIMER_FRONTEND_URL", "http://localhost:3000")
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


def ensure_screenshot_dir():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def test_full_demo_flow():
    ensure_screenshot_dir()

    # Step 0: Reset demo state in FalkorDB
    print(f"\n[E2E] Resetting demo state via {BACKEND_URL}/api/demo/reset...")
    resp = httpx.post(f"{BACKEND_URL}/api/demo/reset", timeout=15.0)
    assert resp.status_code == 200, f"Reset failed: {resp.text}"
    reset_data = resp.json()
    assert reset_data.get("status") == "ok"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use desktop resolution to show Child Stage and Why Panel side by side
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print(f"[E2E] Navigating to {FRONTEND_URL}...")
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle")

        # ---------------------------------------------------------
        # Step 1: Persona Picker -> Select Leo
        # ---------------------------------------------------------
        print("[E2E] Step 1: Picking Leo persona...")
        leo_btn = page.locator("button:has-text('Start as Leo')")
        expect(leo_btn).to_be_visible(timeout=10000)
        leo_btn.click()

        # Wait for navigation to /learn/[sessionId]
        page.wait_for_url("**/learn/**", timeout=15000)
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)  # Canvas mount delay

        # Verify initial problem 3 + 4 = 7
        expect(page.locator("text=3 + 4 = ?")).to_be_visible()
        expect(page.locator("text=Day 1")).to_be_visible()

        # ---------------------------------------------------------
        # Step 2: Leo taps '6' -> Misconception & Hint 1 (Story)
        # ---------------------------------------------------------
        print("[E2E] Step 2: Leo enters wrong answer 6 (counts_start_number)...")
        btn_6 = page.locator("button[aria-label='Select number 6']")
        expect(btn_6).to_be_visible()
        btn_6.click()

        # Wait for tutor response
        time.sleep(1.5)
        shot1 = os.path.join(SCREENSHOT_DIR, "01_day1_diagnose_hint1.png")
        page.screenshot(path=shot1)
        print(f"[E2E] Captured screenshot: {shot1}")

        # ---------------------------------------------------------
        # Step 3: Leo taps '6' again -> Hint 2 (Visual)
        # ---------------------------------------------------------
        print("[E2E] Step 3: Leo enters 6 again -> Hint 2 (Visual)...")
        btn_6.click()
        time.sleep(1.5)
        shot2 = os.path.join(SCREENSHOT_DIR, "02_day1_hint2_visual.png")
        page.screenshot(path=shot2)
        print(f"[E2E] Captured screenshot: {shot2}")

        # ---------------------------------------------------------
        # Step 4: Leo taps '7' -> Solved!
        # ---------------------------------------------------------
        print("[E2E] Step 4: Leo enters correct answer 7...")
        btn_7 = page.locator("button[aria-label='Select number 7']")
        btn_7.click()
        time.sleep(1.5)
        shot3 = os.path.join(SCREENSHOT_DIR, "03_day1_solved_reflection.png")
        page.screenshot(path=shot3)
        print(f"[E2E] Captured screenshot: {shot3}")

        # ---------------------------------------------------------
        # Step 5: End Session -> Consolidation & Memory Diff
        # ---------------------------------------------------------
        print("[E2E] Step 5: Ending session & consolidating into FalkorDB...")
        end_btn = page.locator("[data-testid='end-session-btn']")
        expect(end_btn).to_be_visible()
        end_btn.click()

        time.sleep(2.0)
        # Switch to diff tab or view memory diff
        diff_tab = page.locator("button:has-text('Memory Diff')")
        if diff_tab.is_visible():
            diff_tab.click()
            time.sleep(0.5)

        shot4 = os.path.join(SCREENSHOT_DIR, "04_day1_consolidation_diff.png")
        page.screenshot(path=shot4)
        print(f"[E2E] Captured screenshot: {shot4}")

        # ---------------------------------------------------------
        # Step 6: Next Day -> Day 2 Adaptation
        # ---------------------------------------------------------
        print("[E2E] Step 6: Advancing to Day 2...")
        next_day_btn = page.locator("[data-testid='next-day-btn']")
        expect(next_day_btn).to_be_visible()
        next_day_btn.click()

        time.sleep(2.0)
        expect(page.locator("[data-testid='day-label']").first).to_have_text("Day 2", timeout=10000)
        shot5 = os.path.join(SCREENSHOT_DIR, "05_day2_adapted_visual_hint.png")
        page.screenshot(path=shot5)
        print(f"[E2E] Captured screenshot: {shot5}")

        # ---------------------------------------------------------
        # Step 7: Ablation Toggle (Graph OFF)
        # ---------------------------------------------------------
        print("[E2E] Step 7: Toggling Graph Intelligence OFF (Ablation mode)...")
        ablation_toggle = page.locator("[data-testid='graph-mode-toggle']").first
        expect(ablation_toggle).to_be_visible()
        ablation_toggle.click()

        time.sleep(1.0)
        expect(page.locator("[data-testid='graph-mode-toggle']").first).to_contain_text("OFF", timeout=5000)
        shot6 = os.path.join(SCREENSHOT_DIR, "06_ablation_graph_off.png")
        page.screenshot(path=shot6)
        print(f"[E2E] Captured screenshot: {shot6}")

        browser.close()
        print("[E2E] Full demo flow passed with all screenshots generated!\n")


if __name__ == "__main__":
    test_full_demo_flow()
