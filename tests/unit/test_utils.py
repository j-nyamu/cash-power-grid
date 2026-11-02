"""Unit tests for app/utils.py: phone/password/meter checks, formatting, translations, access rules."""
import json
import os
import unittest

from helpers import ROOT, AppTestCase, db

from app.models import Access, Activity
from app.utils import (LANGS, fmt_phone, mask_email, normalize_phone, password_ok, role_for, sha, tr,
                       valid_meter, send_email, log_act)


class PhoneTests(unittest.TestCase):
    def test_local_format_kept(self):
        self.assertEqual(normalize_phone("0788123456"), "0788123456")

    def test_spaces_and_dashes_removed(self):
        self.assertEqual(normalize_phone("0788 123-456"), "0788123456")

    def test_country_code_converted(self):
        self.assertEqual(normalize_phone("+250 788 123 456"), "0788123456")
        self.assertEqual(normalize_phone("250788123456"), "0788123456")

    def test_nine_digits_get_leading_zero(self):
        self.assertEqual(normalize_phone("788123456"), "0788123456")

    def test_all_rwanda_prefixes_accepted(self):
        for p in ("0722000000", "0733000000", "0788000000", "0799000000"):
            self.assertEqual(normalize_phone(p), p)

    def test_invalid_numbers_rejected(self):
        for p in ("12345", "0711123456", "07881234567", "", None, "abcdefghij"):
            self.assertIsNone(normalize_phone(p), p)

    def test_fmt_phone(self):
        self.assertEqual(fmt_phone("0788123456"), "0788 123 456")


class PasswordTests(unittest.TestCase):
    def test_strong_password_ok(self):
        self.assertTrue(password_ok("Str0ng!pass"))

    def test_underscore_counts_as_symbol(self):
        self.assertTrue(password_ok("Str0ng_pass"))

    def test_each_rule_required(self):
        self.assertFalse(password_ok("Sh0rt!"))        # too short
        self.assertFalse(password_ok("str0ng!pass"))   # no capital
        self.assertFalse(password_ok("STR0NG!PASS"))   # no small letter
        self.assertFalse(password_ok("Strong!pass"))   # no number
        self.assertFalse(password_ok("Str0ngpass"))    # no symbol


class SmallHelperTests(unittest.TestCase):
    def test_valid_meter_is_exactly_11_digits(self):
        self.assertTrue(valid_meter("01234567890"))
        for m in ("0123456789", "012345678901", "0123456789a", "", None):
            self.assertFalse(valid_meter(m), m)

    def test_mask_email(self):
        self.assertEqual(mask_email("alice@example.com"), "a***@example.com")
        self.assertEqual(mask_email("not-an-email"), "not-an-email")

    def test_sha_is_stable_hex(self):
        self.assertEqual(sha("abc"), sha("abc"))
        self.assertEqual(len(sha("abc")), 64)
        self.assertNotEqual(sha("abc"), sha("abd"))


class TranslationTests(unittest.TestCase):
    def test_only_english_and_kinyarwanda(self):
        self.assertEqual(set(LANGS), {"en", "rw"})

    def test_both_files_have_the_same_keys_and_no_empty_text(self):
        d = os.path.join(ROOT, "app", "translations")
        en = json.load(open(os.path.join(d, "en.json"), encoding="utf-8"))
        rw = json.load(open(os.path.join(d, "rw.json"), encoding="utf-8"))
        self.assertEqual(set(en) - set(rw), set(), "keys missing in rw.json")
        self.assertEqual(set(rw) - set(en), set(), "keys missing in en.json")
        self.assertEqual([k for k, v in en.items() if not v], [])
        self.assertEqual([k for k, v in rw.items() if not v], [])

    def test_lookup_and_fallbacks(self):
        self.assertEqual(tr("login", "en"), "Log in")
        self.assertEqual(tr("login", "rw"), "Injira")
        self.assertEqual(tr("login", "fr"), "Log in")            # unknown language -> English
        self.assertEqual(tr("no_such_key", "rw"), "no_such_key")  # unknown key -> the key itself

    def test_every_translation_key_used_in_templates_exists(self):
        import re
        en = json.load(open(os.path.join(ROOT, "app", "translations", "en.json"), encoding="utf-8"))
        tdir = os.path.join(ROOT, "app", "templates")
        missing = set()
        for name in os.listdir(tdir):
            src = open(os.path.join(tdir, name), encoding="utf-8").read()
            for key in re.findall(r"""\bt\(\s*['"]([\w.]+)['"]\s*\)""", src):
                if key not in en:
                    missing.add(f"{name}: {key}")
        self.assertEqual(missing, set())


class AccessRuleTests(AppTestCase):
    def test_role_for_owner_member_and_stranger(self):
        owner, other, stranger = (self.make_user("0788000001"), self.make_user("0788000002"),
                                  self.make_user("0788000003"))
        m = self.make_meter(owner)
        db.session.add(Access(meter_id=m.id, phone=other.phone, role="add", status="active",
                              invited_by=owner.id, created="x"))
        db.session.add(Access(meter_id=m.id, phone=stranger.phone, role="view", status="pending",
                              invited_by=owner.id, created="x"))
        db.session.commit()
        self.assertEqual(role_for(m, owner), "owner")
        self.assertEqual(role_for(m, other), "add")
        self.assertIsNone(role_for(m, stranger))  # pending invite gives no access yet

    def test_log_act_without_user(self):
        owner = self.make_user()
        m = self.make_meter(owner)
        with self.app.test_request_context():
            from flask import g
            g.user = None
            log_act(m.id, "viewed", "x")
            db.session.commit()
        a = Activity.query.one()
        self.assertIsNone(a.user_id)
        self.assertEqual(a.action, "viewed")

    def test_send_email_without_smtp_returns_false(self):
        self.assertFalse(send_email("a@b.rw", "s", "b"))


if __name__ == "__main__":
    unittest.main()
