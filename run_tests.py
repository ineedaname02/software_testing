"""
Reads test cases from test_cases.csv, feeds each one into the web app,
compares the displayed total with the expected total, and reports
PASS / FAIL / ERROR. One failing case never stops the run.

Usage:   python run_tests.py
Config (optional environment variables):
  APP_URL            page to test      (default http://localhost/software_testing/index.html)
  HEADLESS=1         run without a visible window (for CI)
"""
import csv
import os
import sys
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_DIR = Path(__file__).resolve().parent
APP_URL = os.getenv("APP_URL", "http://localhost/software_testing/index.html")
CSV_FILE = BASE_DIR / "test_cases.csv"
SHOT_DIR = BASE_DIR / "screenshots"
RESULT_FILE = BASE_DIR / "results.csv"
WAIT_SECONDS = 8
NUM_MODELS = 8


def make_driver():
    options = Options()
    if os.getenv("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    if os.getenv("HEADLESS") == "1":
        options.add_argument("--headless=new")
    for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions",
                "--disable-popup-blocking", "--disable-notifications",
                "--window-size=1280,1000"):
        options.add_argument(arg)
    driver_path = os.getenv("CHROMEDRIVER_PATH")
    service = Service(driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


def save_shot(driver, test_id, status):
    """Save a timestamped screenshot named after the test case and its result."""
    SHOT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SHOT_DIR / f"{test_id}_{status}_{stamp}.png"
    try:
        driver.save_screenshot(str(path))
        return path.name
    except WebDriverException:
        return "(screenshot failed)"


def run_case(driver, row):
    """Feed one test case into the page. Returns (status, actual, reason)."""
    wait = WebDriverWait(driver, WAIT_SECONDS)
    driver.get(APP_URL)
    wait.until(EC.element_to_be_clickable((By.ID, "calc_button")))

    # Enter usage for each model
    for i in range(1, NUM_MODELS + 1):
        field = driver.find_element(By.ID, f"qty{i}")
        field.clear()
        field.send_keys(row[f"qty{i}"])

    # Batch toggle: click only if its state differs from what the case wants
    batch = driver.find_element(By.ID, "batch_toggle")
    if batch.is_selected() != (row["batch"].strip().lower() == "yes"):
        batch.click()

    driver.find_element(By.ID, "calc_button").click()

    # Wait for the result, bring it into view, then read the total
    total_el = wait.until(EC.visibility_of_element_located((By.ID, "total_amount")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", total_el)
    time.sleep(0.3)
    actual = total_el.text.strip()
    expected = row["expected_total"].strip()

    try:
        same = Decimal(actual) == Decimal(expected)
    except InvalidOperation:
        return "FAIL", actual, f"Total is not a valid number: '{actual}'"
    if same:
        return "PASS", actual, ""
    return "FAIL", actual, f"Expected {expected} but got {actual}"


def main():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    print(f"Loaded {len(cases)} test cases from {CSV_FILE.name}")
    print(f"Target: {APP_URL}\n")

    driver = make_driver()
    results = []
    try:
        for row in cases:
            tid, desc = row["test_id"], row["description"]
            started = time.time()
            status, actual, reason = "ERROR", "", ""
            try:
                status, actual, reason = run_case(driver, row)
            except TimeoutException:
                reason = f"Timeout after {WAIT_SECONDS}s: page or total did not appear"
            except NoSuchElementException as exc:
                reason = "Element not found: " + exc.msg.splitlines()[0]
            except Exception as exc:  # any other problem must not stop the run
                reason = f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}"

            shot = save_shot(driver, tid, status)
            secs = round(time.time() - started, 2)
            results.append([tid, desc, row["expected_total"], actual, status, reason, secs, shot])

            print(f"[{tid}] {desc}")
            print(f"       expected={row['expected_total']}  actual={actual or '-'}  ->  {status}"
                  f"  ({secs}s)")
            if reason:
                print(f"       reason: {reason}")
            print(f"       screenshot: {shot}\n", flush=True)
    finally:
        driver.quit()

    with open(RESULT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["test_id", "description", "expected", "actual",
                    "status", "reason", "seconds", "screenshot"])
        w.writerows(results)

    passed = sum(r[4] == "PASS" for r in results)
    failed = sum(r[4] == "FAIL" for r in results)
    errors = sum(r[4] == "ERROR" for r in results)
    print("=" * 50)
    print(f"SUMMARY: {len(results)} run | {passed} passed | {failed} failed | {errors} errors")
    print(f"Results saved to {RESULT_FILE.name}; screenshots in {SHOT_DIR.name}/")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
