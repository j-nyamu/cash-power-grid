# Testing Cash Power Guard

## Run the tests

```bash
source .venv/bin/activate
python -m unittest discover -s tests/unit -v     # unit tests (111 tests, ~5 s)
python tests/test_no_otp.py                      # older end-to-end script, OTP off
python tests/test_app.py                         # older end-to-end script, OTP on
```

The tests need only what is already installed: Flask, Flask-SQLAlchemy and the Python standard library (`unittest`).
You can run one file or one test like this:

```bash
python -m unittest discover -s tests/unit -p test_forecast.py
cd tests/unit && python -m unittest test_auth.LoginTests.test_locked_after_five_failures_even_with_right_password
```

## How the tests work

- **Your data is safe.** Every test gets a brand-new SQLite file in a temporary folder, deleted after the test.
  `instance/cpg.db` is never opened. `CPG_DB` is pointed at a temp file before `config.py` loads.
- **No email or SMS is sent.** `CPG_SMTP_HOST` is cleared, so codes only go to the log. `DEMO_OTP` is on, so the
  tests can read the one-time code from the session the same way the demo page shows it.
- **Real requests.** Page tests go through Flask's test client, so CSRF checks, sessions, cookies, redirects and
  templates all run exactly as they do in the browser.
- **Shared setup** is in `tests/unit/helpers.py`:
  - `AppTestCase` builds the app per test. A test class can change settings with `CONFIG = {...}`, for example
    `{"OTP_REQUIRED": True}`.
  - `client()`, `post()` (adds the CSRF token automatically), `register()` and `signed_in()` make a logged-in user in
    one line.
  - `make_user()` and `make_meter()` write rows straight to the database, for the calculation tests.
- The app code, templates and design were **not changed** to write these tests.

## What is tested

| File | Tests | What it checks |
|---|---|---|
| `tests/unit/test_utils.py` | 20 | Rwanda phone numbers (`07…`, `+250…`, 9 digits, bad prefixes), password rules, 11-digit meter numbers, email masking, hashing; the `en`/`rw` translation files have the same keys and no empty text, and every `t('key')` used in a template exists; fallback to English; who is owner / add / view; email without SMTP |
| `tests/unit/test_forecast.py` | 27 | REG tariff blocks (20 kWh @ 89, next 30 @ 310, the rest @ 369, plus 18% VAT), starting in a later block when units were already bought this month, more money never buys fewer units; kWh bought earlier in the month; calibration from SMS receipts (ignores estimates, kept between 0.6 and 1.05); forecast: rate from readings, purchases between and after readings, average of the last 3 rates, fallback from purchases only, old readings lower the balance and widen the range (15% + 3% a day, at most 50%), low-balance flag, "buy by" date, balance never below zero |
| `tests/unit/test_auth.py` | 31 | Sign-up (creates user, `CPG-000001` ID and first meter, password stored hashed, each validation error gives 400, duplicate phone/meter, unknown account type); live `/api/check-phone` and `/api/check-meter`; login, wrong password, unknown phone, lock after 5 failures, lock expiry, failure count reset; remember this device (cookie, automatic login, expiry, logout, log out everywhere); one-time codes (6 digits, only the hash stored, single use, tied to phone + purpose, 5 tries, expiry, a new code cancels the old one, resend wait); full OTP sign-up and login flow; forgot password → code → new password (signs out remembered devices) |
| `tests/unit/test_meters_usage_members.py` | 33 | Add meter (spaces allowed, invalid or duplicate refused, default nickname); 404 / 403 on meter pages; readings and purchases (exact from receipt vs. estimated from tariff, calibration used, future or bad dates become today, zero/negative/text refused, activity log); sharing (invite stays pending until accepted, decline, accept only your own invite, view vs. add rights, unknown role becomes view, self/duplicate/bad-number invites refused, revoke, "viewed" logged at most once per 10 minutes, invite to a number that signs up later); every page loads; CSRF required on every POST; English/Kinyarwanda switch kept in the session, saved on the account and through sign-up; static files; cookie settings |

## Results (2 Nov 2026, Python 3.14.3, Flask 3.1.3, SQLAlchemy 2.1.6)

| Suite | Result |
|---|---|
| `tests/unit` (new) | **111 passed, 0 failed** in 5.3 s |
| `tests/test_no_otp.py` | **All passed** |
| `tests/test_app.py` | **Stops at `FAIL lang fr`.** Every check before it passes. The script still expects a French login page, but French was removed in commit `0cb8fca`. The app is fine; the old test is out of date. To fix it, remove `('fr', b'Se connecter'),` from the language loop near the end of the file. |

Running app check: `python run.py` serves `/`, `/login`, `/register`, `/forgot`, `/login?lang=rw` and the static files
with status 200; `/dashboard` redirects to login when signed out.

## Notes found while testing

- `requirements.txt` is empty. The working set is `Flask`, `Flask-SQLAlchemy`, `SQLAlchemy`, `PyMySQL` (only for
  MySQL). `setup.sh` installs nothing until the file is filled in.
- On macOS, port 5000 is used by AirPlay Receiver. Start the app with `PORT=5050 python run.py`.
- `tests/test_app.py` and `tests/test_no_otp.py` run when they are imported, so keep them out of
  `unittest discover`. That is why the new tests live in `tests/unit/`.
