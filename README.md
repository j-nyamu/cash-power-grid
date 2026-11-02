# Cash Power Guard

**Know the day your units run out.** Cash Power Guard is a web app for prepaid electricity ("cash power") users in
Rwanda. Users log each token they buy and each meter reading. The app works out how many kWh a payment buys under
REG's price blocks and estimates the date range in which the units will run out. Users can share a meter with
family, tenants or staff.

The app is available in **English** and **Kinyarwanda**.

🎨 **UI design (Figma):** [Cash Power Guard design file](https://www.figma.com/design/7B9Da3cnU6TiANi9L3uq4N/Untitled?node-id=1-40&t=eZkFcIxVDHV2V0Cr-1)

---

## Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Using a MySQL database](#using-a-mysql-database)
- [Project structure](#project-structure)
- [How the forecast works](#how-the-forecast-works)
- [Testing](#testing)
- [Design](#design)

---

## Screenshots

> Screenshots are of the running app with sample data. All files are in [`docs/screenshots/`](docs/screenshots/).

### Landing page
The home page has a live calculator: enter an amount in RWF and a daily use, and it shows the units bought and the
days of power.

![Landing page](docs/screenshots/landing.png)

### Dashboard
All of a user's meters, each with a gauge of days left. Meters close to running out show a red "Buy before" warning.
Invitations from other owners appear at the top.

![Dashboard](docs/screenshots/dashboard.png)

### Meter page
The run-out forecast, forms to log a purchase or a reading, and the full history. The owner also sees who has access
and an activity log.

![Meter page](docs/screenshots/meter.png)

### Sign up and log in

| Create account | Log in |
|---|---|
| ![Register](docs/screenshots/register.png) | ![Login](docs/screenshots/login.png) |

### Kinyarwanda, welcome and settings

| Kinyarwanda | Welcome (after sign-up) | Settings |
|---|---|---|
| ![Kinyarwanda login](docs/screenshots/login_rw.png) | ![Welcome](docs/screenshots/welcome.png) | ![Settings](docs/screenshots/settings.png) |

---

## Features

**Accounts and security**
- Sign up with name, Rwandan phone number (`07…` or `+250…`), email, meter number and password
- Each user gets an ID such as `CPG-000001`; there is one account per phone number and one owner per meter
- Strong passwords required (8+ characters with a capital letter, a small letter, a number and a symbol); passwords are stored hashed
- Account locks for 15 minutes after 5 wrong passwords
- Optional one-time code (OTP) by email or SMS at sign-up and login; required for password reset
- "Remember this device" for 30 days, plus "log out everywhere"
- CSRF protection on every form; HTTP-only, SameSite session cookies

**Meters and usage**
- Several meters per account (home, shop, rental…)
- Log a **purchase**: copy the kWh from the SMS receipt (exact), or enter only the RWF amount and the app estimates the kWh
- Log a **meter reading**: the balance shown on the meter
- **Run-out forecast**: kWh left, days left, a date range and a "buy before" date

**Sharing**
- The owner invites people by phone number, even before they have an account
- Two access levels: **view only** or **can add purchases**
- The invited person accepts or declines; the owner can remove access at any time
- The activity log shows who viewed, added, accepted or was removed

**Languages**
- English and Kinyarwanda, switchable on every page; the choice is saved on the account

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, [Flask 3](https://flask.palletsprojects.com/) |
| Database | SQLite by default, MySQL in production (SQLAlchemy 2 + Flask-SQLAlchemy, PyMySQL driver) |
| Frontend | Server-rendered Jinja2 templates, plain CSS and JavaScript (no build step) |
| Tests | Python `unittest` (no extra packages) |

---

## Getting started

### 1. Requirements

- **Python 3.10 or newer**: check with `python3 --version`
- **Git**

### 2. Get the code

```bash
git clone https://github.com/j-nyamu/cash-power-grid.git
cd cash-power-grid
```

### 3. Create a virtual environment and install packages

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install Flask Flask-SQLAlchemy PyMySQL
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install Flask Flask-SQLAlchemy PyMySQL
```

> `PyMySQL` is needed only if you use MySQL. Once `requirements.txt` lists these packages, you can use
> `pip install -r requirements.txt` or `./setup.sh` instead.

### 4. Run the app

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

> **macOS:** port 5000 is usually taken by *AirPlay Receiver*. Use another port:
> ```bash
> PORT=5050 python run.py          # then open http://127.0.0.1:5050
> ```
> On Windows PowerShell: `$env:PORT=5050; python run.py`

On first start the app creates:
- `instance/cpg.db`: the SQLite database (all tables are created automatically)
- `instance/secret_key`: a random key that keeps users logged in across restarts

Both are ignored by Git. Never commit them.

### 5. Try it

1. Click **Create account** and fill in the form. Use any valid Rwandan number such as `0788 123 456` and an
   11-digit meter number.
2. On the dashboard, open your meter.
3. Log a **meter reading** (e.g. `30` kWh), then another one on a later date. The run-out forecast appears once the
   app knows how fast you use power.
4. Log a **purchase** with or without the kWh from your receipt.
5. Invite another phone number under **People who can see these logs**.

To stop the app, press `Ctrl + C` in the terminal.

---

## Configuration

Every setting can be changed with an environment variable. The defaults are fine for local development.

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5000` | Port the app listens on |
| `CPG_DB` | `instance/cpg.db` | Path of the SQLite database file |
| `CPG_DATABASE_URL` | — | Full database URL. Overrides `CPG_DB`. Example: `mysql+pymysql://user:pass@host/cashpower` |
| `CPG_SECRET` | random, saved in `instance/secret_key` | Secret key for sessions. Set it in production |
| `CPG_OTP_REQUIRED` | `0` | `1` = ask for a one-time code at sign-up and login |
| `CPG_OTP_CHANNEL` | `email` | `email` or `sms` |
| `CPG_DEMO_OTP` | `1` when no SMTP is set | `1` = show the code on screen (development only) |
| `CPG_SMTP_HOST` | — | SMTP server for sending codes (Gmail app password, Brevo, Resend…) |
| `CPG_SMTP_PORT` | `587` | SMTP port (STARTTLS) |
| `CPG_SMTP_USER` / `CPG_SMTP_PASS` | — | SMTP login |
| `CPG_SMTP_FROM` | `CPG_SMTP_USER` | Sender address |
| `CPG_VAT_PCT` | `18` | VAT added to REG's listed prices |

Example with one-time codes switched on and sent by email:

```bash
export CPG_OTP_REQUIRED=1
export CPG_SMTP_HOST=smtp.gmail.com CPG_SMTP_USER=you@gmail.com CPG_SMTP_PASS='app-password'
python run.py
```

SMS sending is not connected yet. `send_sms()` in [`app/utils.py`](app/utils.py) only writes the message to the log,
ready for a provider such as Africa's Talking.

---

## Using a MySQL database

The SQL in [`db-schema/`](db-schema/) creates the same tables as [`app/models.py`](app/models.py) in a database called
`cashpower`.

```bash
cd db-schema
./setup.sh <mysql_user>              # local MySQL, runs 00_ … 05_ in order
# or, for a hosted server such as Aiven:
pip install pymysql sqlparse
python run_sql.py                    # asks for host, port, user and password
```

Then start the app against it:

```bash
export CPG_DATABASE_URL="mysql+pymysql://USER:PASSWORD@HOST:PORT/cashpower"
python run.py
```

---

## Project structure

```
cash-power-grid/
├── run.py                 # starts the app
├── config.py              # all settings (overridable with CPG_* variables)
├── app/
│   ├── __init__.py        # builds the Flask app, CSRF check, language choice
│   ├── models.py          # database tables: users, meters, access, entries, otps, devices, activity
│   ├── auth.py            # sign-up, login, OTP, forgot password, remember device, logout
│   ├── meters.py          # add a meter, meter page
│   ├── usage.py           # log purchases and readings
│   ├── members.py         # invite, accept/decline, remove access
│   ├── forecast.py        # tariff calculation, calibration, run-out forecast
│   ├── views.py           # landing, dashboard, settings, error pages
│   ├── utils.py           # phone/password checks, translations, email/SMS, access rules
│   ├── extensions.py      # SQLAlchemy object
│   ├── templates/         # Jinja2 pages
│   ├── static/            # style.css, app.js
│   └── translations/      # en.json, rw.json
├── db-schema/             # MySQL schema scripts
├── tests/
│   ├── unit/              # unittest suite (111 tests)
│   ├── test_app.py        # end-to-end script, OTP on
│   └── test_no_otp.py     # end-to-end script, OTP off
├── docs/screenshots/      # images used in this README
└── TESTING.md             # how the tests work, latest results
```

---

## How the forecast works

1. **Units from money.** REG residential prices (October 2025, before VAT) are applied in monthly blocks:

   | Block | Price |
   |---|---|
   | First 20 kWh of the month | 89 RWF/kWh |
   | Next 30 kWh | 310 RWF/kWh |
   | Above 50 kWh | 369 RWF/kWh |

   18% VAT is added (configurable). Units already bought this month decide which block a new payment starts in.

2. **Calibration.** When a purchase is logged with the kWh from the SMS receipt, the app compares it with what the
   tariff predicted. The middle value of those ratios, kept between 0.6 and 1.05, corrects later estimates.

3. **Daily use.** Usage between two readings = first reading + units bought in between − second reading. The average
   of the last three periods gives kWh per day. With only one reading, it falls back to the time between purchases.

4. **Run-out range.** Balance now = last reading + units bought since − daily use × days since that reading.
   Days left = balance ÷ daily use, shown as a range of ±15%. The range widens by 3% for each day since the last
   reading, up to ±50%. Readings older than 7 days are marked stale, and the app asks for a new one.

The code is in [`app/forecast.py`](app/forecast.py).

---

## Testing

```bash
python -m unittest discover -s tests/unit -v
```

There are **111 unit tests** covering validation, the tariff and forecast maths, sign-up and login, one-time codes,
remembered devices, meters, purchases and readings, sharing and permissions, CSRF and both languages. Each test uses
its own temporary database, so your data is never touched.

See **[TESTING.md](TESTING.md)** for what each test file covers and the latest results.

---

## Design

The interface was designed in Figma before it was built:

**➡️ [Open the Figma design](https://www.figma.com/design/7B9Da3cnU6TiANi9L3uq4N/Untitled?node-id=1-40&t=eZkFcIxVDHV2V0Cr-1)**

Design language used in the app:
- **Colours:** off-white background, near-black text (`#111318`), signal orange (`#D9460F`) for actions and the gauge
- **Type:** *Poppins* for text, *JetBrains Mono* for numbers, meter numbers and labels
- **Signature element:** the half-circle "days left" gauge, also used as the logo and background pattern
