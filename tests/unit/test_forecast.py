"""Unit tests for app/forecast.py: tariff blocks, calibration from receipts, run-out forecast."""
import unittest
from datetime import date, timedelta

from helpers import AppTestCase, db

from app.forecast import TARIFF, bought_this_month_before, calibration, forecast, kwh_from_rwf
from app.models import Entry


def day(n):
    """The date n days ago, as text."""
    return (date.today() - timedelta(days=n)).isoformat()


class TariffTests(AppTestCase):
    """REG blocks: 0-20 kWh @89, 20-50 @310, 50+ @369 RWF (before VAT)."""

    def test_tariff_table(self):
        self.assertEqual([p for _, p in TARIFF], [89, 310, 369])

    def test_inside_first_block_no_vat(self):
        self.assertEqual(kwh_from_rwf(890, 0, vat_pct=0), 10.0)

    def test_crosses_into_second_block_no_vat(self):
        # 20 kWh cost 1780, the other 3220 buy 3220/310 = 10.39 kWh
        self.assertEqual(kwh_from_rwf(5000, 0, vat_pct=0), 30.39)

    def test_all_three_blocks_no_vat(self):
        # 20*89 + 30*310 = 11080; the rest at 369
        self.assertEqual(kwh_from_rwf(11080 + 3690, 0, vat_pct=0), 60.0)

    def test_already_bought_this_month_starts_in_later_block(self):
        self.assertEqual(kwh_from_rwf(3100, 20, vat_pct=0), 10.0)
        self.assertEqual(kwh_from_rwf(3690, 50, vat_pct=0), 10.0)
        self.assertEqual(kwh_from_rwf(3690, 500, vat_pct=0), 10.0)

    def test_partly_used_block(self):
        # 10 kWh left in block 1 (890), rest at 310
        self.assertEqual(kwh_from_rwf(890 + 310, 10, vat_pct=0), 11.0)

    def test_vat_from_config_is_18_percent(self):
        self.assertEqual(self.app.config["VAT_PCT"], 18.0)
        self.assertEqual(kwh_from_rwf(5000, 0), 27.93)
        self.assertEqual(kwh_from_rwf(5000, 50), round(5000 / (369 * 1.18), 2))

    def test_zero_money_gives_zero_units(self):
        self.assertEqual(kwh_from_rwf(0, 0, vat_pct=0), 0.0)

    def test_more_money_never_buys_fewer_units(self):
        prev = 0
        for rwf in range(0, 30001, 500):
            k = kwh_from_rwf(rwf, 0)
            self.assertGreaterEqual(k, prev)
            prev = k


class EntryCase(AppTestCase):
    def setUp(self):
        super().setUp()
        self.u = self.make_user()
        self.m = self.make_meter(self.u)

    def add(self, kind, n_days_ago, kwh, rwf=None, estimated=0):
        e = Entry(meter_id=self.m.id, user_id=self.u.id, kind=kind, day=day(n_days_ago), rwf=rwf, kwh=kwh,
                  estimated=estimated, created="x")
        db.session.add(e)
        db.session.commit()
        return e


class BoughtThisMonthTests(EntryCase):
    def test_sums_only_purchases_of_the_same_month(self):
        first = date.today().replace(day=1)
        last_month = (first - timedelta(days=1)).isoformat()
        db.session.add_all([
            Entry(meter_id=self.m.id, user_id=self.u.id, kind="purchase", day=last_month, rwf=1, kwh=99, created="x"),
            Entry(meter_id=self.m.id, user_id=self.u.id, kind="purchase", day=first.isoformat(), rwf=1, kwh=5,
                  created="x"),
            Entry(meter_id=self.m.id, user_id=self.u.id, kind="reading", day=first.isoformat(), kwh=50, created="x"),
        ])
        db.session.commit()
        self.assertEqual(bought_this_month_before(self.m.id, date.today().isoformat()), 5)

    def test_same_day_counts_only_earlier_entries(self):
        a = self.add("purchase", 0, 10, rwf=1)
        b = self.add("purchase", 0, 7, rwf=1)
        self.assertEqual(bought_this_month_before(self.m.id, day(0), a.id), 0)
        self.assertEqual(bought_this_month_before(self.m.id, day(0), b.id), 10)


class CalibrationTests(EntryCase):
    def test_no_receipts_means_no_correction(self):
        self.assertEqual(calibration(self.m.id), (1.0, 0))

    def test_estimated_entries_are_ignored(self):
        self.add("purchase", 0, 20, rwf=5000, estimated=1)
        self.assertEqual(calibration(self.m.id), (1.0, 0))

    def test_learns_ratio_from_receipt(self):
        self.add("purchase", 0, 25.0, rwf=5000)
        f, n = calibration(self.m.id)
        self.assertEqual(n, 1)
        self.assertAlmostEqual(f, round(25.0 / 27.93, 3), places=3)

    def test_ratio_is_clamped(self):
        self.add("purchase", 0, 1.0, rwf=5000)   # absurdly low receipt
        self.assertEqual(calibration(self.m.id)[0], 0.6)

    def test_ratio_upper_clamp(self):
        self.add("purchase", 0, 100.0, rwf=5000)  # absurdly high receipt
        self.assertEqual(calibration(self.m.id)[0], 1.05)


class ForecastTests(EntryCase):
    def test_no_data_no_forecast(self):
        self.assertIsNone(forecast(self.m.id))

    def test_one_reading_is_not_enough(self):
        self.add("reading", 0, 20)
        self.assertIsNone(forecast(self.m.id))

    def test_two_readings_give_a_rate(self):
        self.add("reading", 10, 30)
        self.add("reading", 0, 20)
        fc = forecast(self.m.id)
        self.assertEqual(fc["rate"], 1.0)        # 10 kWh in 10 days
        self.assertEqual(fc["balance"], 20.0)
        self.assertEqual(fc["days"], 20.0)
        self.assertEqual(fc["spread"], 15)       # fresh reading -> +/-15%
        self.assertFalse(fc["stale"])
        self.assertFalse(fc["low"])
        self.assertEqual(fc["lo"], date.today() + timedelta(days=17))
        self.assertEqual(fc["hi"], date.today() + timedelta(days=23))
        self.assertEqual(fc["buy_by"], date.today() + timedelta(days=15))

    def test_purchase_between_readings_is_counted(self):
        self.add("reading", 10, 10)
        self.add("purchase", 5, 20, rwf=5000)
        self.add("reading", 0, 20)
        self.assertEqual(forecast(self.m.id)["rate"], 1.0)  # 10 + 20 - 20 = 10 kWh in 10 days

    def test_purchase_after_last_reading_adds_to_balance(self):
        self.add("reading", 10, 30)
        self.add("reading", 0, 20)
        self.add("purchase", 0, 15, rwf=5000)
        self.assertEqual(forecast(self.m.id)["balance"], 35.0)

    def test_old_reading_lowers_balance_and_widens_range(self):
        self.add("reading", 20, 40)
        self.add("reading", 10, 30)
        fc = forecast(self.m.id)
        self.assertEqual(fc["age"], 10)
        self.assertEqual(fc["balance"], 20.0)    # 30 - 1 kWh/day * 10 days
        self.assertTrue(fc["stale"])
        self.assertEqual(fc["spread"], 45)       # 15 + 3*10

    def test_spread_never_above_50(self):
        self.add("reading", 60, 100)
        self.add("reading", 30, 90)
        self.assertEqual(forecast(self.m.id)["spread"], 50)

    def test_low_balance_flag(self):
        self.add("reading", 10, 12)
        self.add("reading", 0, 2)
        fc = forecast(self.m.id)
        self.assertTrue(fc["low"])
        self.assertEqual(fc["buy_by"], date.today())

    def test_uses_average_of_last_three_rates(self):
        for n, kwh in [(40, 100), (30, 90), (20, 70), (10, 40), (0, 0)]:  # rates 1, 2, 3, 4
            self.add("reading", n, kwh)
        self.assertEqual(forecast(self.m.id)["rate"], 3.0)

    def test_fallback_rate_from_purchases_only(self):
        self.add("purchase", 20, 30, rwf=5000)
        self.add("purchase", 10, 30, rwf=5000)
        self.add("reading", 0, 30)
        self.assertEqual(forecast(self.m.id)["rate"], 3.0)  # 30 kWh used in 10 days

    def test_balance_never_negative(self):
        self.add("reading", 30, 20)
        self.add("reading", 20, 10)
        self.assertEqual(forecast(self.m.id)["balance"], 0.0)


if __name__ == "__main__":
    unittest.main()
