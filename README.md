# LLM AI Gateway Dashboard: Selenium Testing

![Ubuntu Tests](https://github.com/ineedaname02/software_testing/actions/workflows/test-ubuntu.yml/badge.svg)
![Windows Tests](https://github.com/ineedaname02/software_testing/actions/workflows/test-windows.yml/badge.svg)

A web dashboard for an LLM AI gateway (8 models, 6% SST, 50% batch API discount)
with an automated Selenium test suite.

## Files
- `index.html`: the web application
- `test_cases.csv`: 10 test cases with expected totals
- `run_tests.py`: Selenium test script (reads the CSV, saves results and screenshots)
- `generate_report.py`: builds `test_report.html` from `results.csv`
- `.github/workflows/`: `test-ubuntu.yml` and `test-windows.yml` (manual trigger)

## Run locally
```
python -m pip install -r requirements.txt
python -m http.server 8000
# in a second terminal
set APP_URL=http://localhost:8000/index.html
python run_tests.py
python generate_report.py
```
