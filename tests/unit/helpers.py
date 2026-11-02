"""Shared setup for the unit tests: a fresh throw-away database per test, plus small request helpers.

Your real database (instance/cpg.db) is never touched.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
# Must be set before config.py is imported, so the default database is a temp file, not instance/cpg.db.
os.environ["CPG_DB"] = os.path.join(tempfile.mkdtemp(), "import.db")
os.environ.pop("CPG_SMTP_HOST", None)
os.environ.pop("CPG_DATABASE_URL", None)

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Meter, User  # noqa: E402
from app.utils import iso, now  # noqa: E402

PW = "Str0ng!pass"


class AppTestCase(unittest.TestCase):
    """Each test gets its own app and empty SQLite file. Override CONFIG in a subclass to change settings."""
    CONFIG = {}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        cfg = {"TESTING": True, "OTP_RESEND_SEC": 0, "DEMO_OTP": True, "OTP_REQUIRED": False,
               "SQLALCHEMY_DATABASE_URI": "sqlite:///" + os.path.join(self.tmp.name, "t.db")}
        cfg.update(self.CONFIG)
        self.app = create_app(cfg)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.ctx.pop()
        self.tmp.cleanup()

    # ------------------------------------------------------------ request helpers
    def client(self):
        c = self.app.test_client()
        c.get("/login")  # creates the session and its CSRF token
        return c

    @staticmethod
    def csrf(c):
        """The session's CSRF token. Signing in starts a fresh session, so open a page to get a new one if needed."""
        with c.session_transaction() as s:
            if "csrf" in s:
                return s["csrf"]
        c.get("/settings")  # logged in: renders a form
        c.get("/login")     # logged out: renders a form
        with c.session_transaction() as s:
            return s["csrf"]

    def post(self, c, url, **data):
        data["csrf"] = self.csrf(c)
        return c.post(url, data=data)

    @staticmethod
    def demo_code(c):
        with c.session_transaction() as s:
            return s.get("demo_code")

    def register(self, c, name="Alice Uwase", phone="0788123456", meter="01234567890", pw=PW, **extra):
        data = dict(name=name, phone=phone, email="a@b.rw", meter_no=meter, nickname="Home",
                    password=pw, confirm=pw, terms="1", acct_type="household")
        data.update(extra)
        return self.post(c, "/register", **data)

    def signed_in(self, name="Alice Uwase", phone="0788123456", meter="01234567890"):
        """A client that has an account and is logged in (OTP off). Returns (client, user, meter)."""
        c = self.client()
        r = self.register(c, name=name, phone=phone, meter=meter)
        self.assertEqual(r.status_code, 302, r.data[:300])
        u = User.query.filter_by(phone=phone).one()
        return c, u, Meter.query.filter_by(meter_no=meter).one()

    # ------------------------------------------------------------ direct database helpers
    @staticmethod
    def make_user(phone="0788123456", name="Test User"):
        u = User(name=name, phone=phone, email="t@t.rw", acct_type="household", pw_hash="x", created=iso(now()))
        db.session.add(u)
        db.session.commit()
        return u

    @staticmethod
    def make_meter(user, meter_no="01234567890"):
        m = Meter(meter_no=meter_no, nickname="Home", owner_id=user.id, created=iso(now()))
        db.session.add(m)
        db.session.commit()
        return m
