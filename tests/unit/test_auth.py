"""Unit tests for app/auth.py: sign-up, login, lockout, one-time codes, forgot password, remembered devices."""
import unittest
from datetime import timedelta

from helpers import PW, AppTestCase, db

from app.auth import check_otp, issue_otp
from app.models import Device, Meter, Otp, User
from app.utils import iso, now


class SignupTests(AppTestCase):
    def test_signup_creates_user_meter_and_id(self):
        c = self.client()
        r = self.register(c)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.location.endswith("/welcome"))
        u = User.query.one()
        self.assertEqual(u.uid, "CPG-000001")
        self.assertNotEqual(u.pw_hash, PW)  # stored hashed
        self.assertEqual(Meter.query.one().owner_id, u.id)
        self.assertIn(b"CPG-000001", c.get("/welcome").data)

    def test_validation_errors_return_400(self):
        cases = {
            "short name": dict(name="Al"),
            "bad phone": dict(phone="12345"),
            "bad email": dict(email="nope"),
            "bad meter": dict(meter_no="123"),
            "weak password": dict(password="weak", confirm="weak"),
            "passwords differ": dict(confirm="Other!pass1"),
            "terms not ticked": dict(terms=""),
        }
        for label, bad in cases.items():
            with self.subTest(label):
                r = self.register(self.client(), **bad)
                self.assertEqual(r.status_code, 400)
        self.assertEqual(User.query.count(), 0)

    def test_duplicate_phone_and_meter_rejected(self):
        self.register(self.client())
        r = self.register(self.client(), phone="+250 788 123 456", meter="09999999999")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already has an account", r.data)
        r = self.register(self.client(), phone="0788999999")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already registered", r.data)

    def test_unknown_account_type_becomes_household(self):
        self.register(self.client(), acct_type="hacker")
        self.assertEqual(User.query.one().acct_type, "household")

    def test_live_check_apis(self):
        self.register(self.client())
        c = self.client()
        self.assertTrue(c.get("/api/check-phone?phone=0788%20123%20456").json["exists"])
        self.assertFalse(c.get("/api/check-phone?phone=12345").json["ok"])
        self.assertTrue(c.get("/api/check-phone?phone=0722000000").json["ok"])
        self.assertFalse(c.get("/api/check-meter?meter=01234567890").json["ok"])
        self.assertFalse(c.get("/api/check-meter?meter=1").json["ok"])
        self.assertTrue(c.get("/api/check-meter?meter=09999999999").json["ok"])

    def test_logged_in_user_redirected_away_from_register_and_login(self):
        c, _, _ = self.signed_in()
        self.assertEqual(c.get("/register").status_code, 302)
        self.assertEqual(c.get("/login").status_code, 302)


class LoginTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register(self.client())

    def test_right_password_logs_in(self):
        c = self.client()
        r = self.post(c, "/login", phone="0788123456", password=PW)
        self.assertTrue(r.location.endswith("/dashboard"))
        self.assertEqual(c.get("/dashboard").status_code, 200)

    def test_wrong_password_and_unknown_phone(self):
        self.assertEqual(self.post(self.client(), "/login", phone="0788123456", password="Wrong!1a").status_code, 401)
        self.assertEqual(self.post(self.client(), "/login", phone="0722000000", password=PW).status_code, 401)
        self.assertEqual(self.post(self.client(), "/login", phone="bad", password=PW).status_code, 401)

    def test_locked_after_five_failures_even_with_right_password(self):
        c = self.client()
        for _ in range(5):
            self.post(c, "/login", phone="0788123456", password="Nope!nope1")
        self.assertIsNotNone(User.query.one().locked_until)
        self.assertEqual(self.post(c, "/login", phone="0788123456", password=PW).status_code, 429)

    def test_lock_expires(self):
        u = User.query.one()
        u.locked_until = iso(now() - timedelta(minutes=1))
        db.session.commit()
        r = self.post(self.client(), "/login", phone="0788123456", password=PW)
        self.assertEqual(r.status_code, 302)

    def test_good_login_resets_failure_count(self):
        c = self.client()
        for _ in range(3):
            self.post(c, "/login", phone="0788123456", password="Nope!nope1")
        self.post(c, "/login", phone="0788123456", password=PW)
        self.assertEqual(User.query.one().failed, 0)

    def test_dashboard_needs_login(self):
        r = self.client().get("/dashboard")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.location)


class RememberDeviceTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register(self.client())

    def login(self, remember):
        c = self.client()
        kw = {"remember": "1"} if remember else {}
        r = self.post(c, "/login", phone="0788123456", password=PW, **kw)
        return c, r

    def forget_session(self, c):
        """Like closing the browser: the session goes, the long-lived cookie stays."""
        with c.session_transaction() as s:
            s.pop("uid", None)
            s.pop("device", None)

    def test_no_remember_no_cookie(self):
        _, r = self.login(False)
        self.assertNotIn("cpg_device", r.headers.get("Set-Cookie", ""))
        self.assertEqual(Device.query.count(), 0)

    def test_remember_sets_cookie_and_auto_logs_in(self):
        c, r = self.login(True)
        self.assertIn("cpg_device", r.headers.get("Set-Cookie", ""))
        self.assertEqual(Device.query.count(), 1)
        self.forget_session(c)
        self.assertEqual(c.get("/dashboard").status_code, 200)

    def test_expired_device_does_not_log_in(self):
        c, _ = self.login(True)
        Device.query.update({"expires": iso(now() - timedelta(days=1))})
        db.session.commit()
        self.forget_session(c)
        self.assertEqual(c.get("/dashboard").status_code, 302)

    def test_logout_removes_device(self):
        c, _ = self.login(True)
        self.post(c, "/logout")
        self.assertEqual(Device.query.count(), 0)
        self.assertEqual(c.get("/dashboard").status_code, 302)

    def test_logout_all_removes_every_device(self):
        a, _ = self.login(True)
        self.login(True)
        self.assertEqual(Device.query.count(), 2)
        self.post(a, "/settings/logout-all")
        self.assertEqual(Device.query.count(), 0)


class OtpFunctionTests(AppTestCase):
    """issue_otp / check_otp called directly."""

    def setUp(self):
        super().setUp()
        self.rq = self.app.test_request_context()
        self.rq.push()

    def tearDown(self):
        self.rq.pop()
        super().tearDown()

    def test_code_is_six_digits_and_only_hash_stored(self):
        code, sent = issue_otp("0788123456", "login")
        self.assertRegex(code, r"^\d{6}$")
        self.assertFalse(sent)  # no SMTP / no email -> SMS log only
        row = Otp.query.one()
        self.assertNotIn(code, row.code_hash)

    def test_right_code_works_once(self):
        code, _ = issue_otp("0788123456", "login")
        self.assertEqual(check_otp("0788123456", "login", code), (True, None))
        self.assertEqual(check_otp("0788123456", "login", code), (False, None))

    def test_code_bound_to_phone_and_purpose(self):
        code, _ = issue_otp("0788123456", "login")
        self.assertFalse(check_otp("0788123456", "reset", code)[0])
        self.assertFalse(check_otp("0722000000", "login", code)[0])

    def test_wrong_code_counts_down_then_locks(self):
        code, _ = issue_otp("0788123456", "login")
        bad = "000000" if code != "000000" else "111111"
        lefts = [check_otp("0788123456", "login", bad)[1] for _ in range(5)]
        self.assertEqual(lefts, [4, 3, 2, 1, 0])
        self.assertEqual(check_otp("0788123456", "login", code), (False, None))  # used up

    def test_expired_code_rejected(self):
        code, _ = issue_otp("0788123456", "login")
        Otp.query.update({"expires": iso(now() - timedelta(seconds=1))})
        db.session.commit()
        self.assertEqual(check_otp("0788123456", "login", code), (False, None))

    def test_new_code_cancels_old_one(self):
        old, _ = issue_otp("0788123456", "login")
        new, _ = issue_otp("0788123456", "login")
        if old != new:
            self.assertFalse(check_otp("0788123456", "login", old)[0])
        self.assertTrue(check_otp("0788123456", "login", new)[0])

    def test_resend_too_soon_is_refused(self):
        self.app.config["OTP_RESEND_SEC"] = 60
        self.assertIsNotNone(issue_otp("0788123456", "login"))
        self.assertIsNone(issue_otp("0788123456", "login"))


class OtpFlowTests(AppTestCase):
    """The full pages with the one-time code switched ON."""
    CONFIG = {"OTP_REQUIRED": True}

    def test_signup_waits_for_code(self):
        c = self.client()
        r = self.register(c)
        self.assertTrue(r.location.endswith("/otp"))
        self.assertEqual(User.query.count(), 0)          # nothing saved before the code
        self.assertEqual(self.post(c, "/otp", code="abc").status_code, 400)
        r = self.post(c, "/otp", code=self.demo_code(c))
        self.assertTrue(r.location.endswith("/welcome"))
        self.assertEqual(User.query.count(), 1)

    def test_login_needs_code(self):
        c = self.client()
        self.register(c)
        self.post(c, "/otp", code=self.demo_code(c))
        c2 = self.client()
        r = self.post(c2, "/login", phone="0788123456", password=PW)
        self.assertTrue(r.location.endswith("/otp"))
        self.assertEqual(c2.get("/dashboard").status_code, 302)
        r = self.post(c2, "/otp", code=self.demo_code(c2))
        self.assertTrue(r.location.endswith("/dashboard"))

    def test_otp_page_without_context_goes_to_login(self):
        r = self.client().get("/otp")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.location)

    def test_resend_issues_new_code(self):
        c = self.client()
        self.register(c)
        first = Otp.query.count()
        self.post(c, "/otp/resend")
        self.assertEqual(Otp.query.count(), first + 1)


class ForgotPasswordTests(AppTestCase):
    def setUp(self):
        super().setUp()
        a = self.client()
        self.register(a)
        self.post(a, "/login", phone="0788123456", password=PW, remember="1")

    def test_full_reset(self):
        c = self.client()
        r = self.post(c, "/forgot", phone="0788123456")
        self.assertTrue(r.location.endswith("/otp"))
        r = self.post(c, "/otp", code=self.demo_code(c))
        self.assertTrue(r.location.endswith("/reset"))
        self.assertEqual(self.post(c, "/reset", password="weak", confirm="weak").status_code, 200)  # stays on page
        r = self.post(c, "/reset", password="N3w!passw0rd", confirm="N3w!passw0rd")
        self.assertTrue(r.location.endswith("/login"))
        self.assertEqual(Device.query.count(), 0)  # remembered devices are signed out
        self.assertEqual(self.post(self.client(), "/login", phone="0788123456", password=PW).status_code, 401)
        self.assertEqual(self.post(self.client(), "/login", phone="0788123456",
                                   password="N3w!passw0rd").status_code, 302)

    def test_unknown_phone_stays_on_page(self):
        r = self.post(self.client(), "/forgot", phone="0722000000")
        self.assertEqual(r.status_code, 200)

    def test_reset_page_needs_verified_code(self):
        r = self.client().get("/reset")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/forgot", r.location)


if __name__ == "__main__":
    unittest.main()
