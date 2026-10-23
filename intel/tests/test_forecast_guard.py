import unittest
from datetime import datetime, timedelta, timezone

from intel.guard_forecasts import immutability_errors, validate_new_registration_times

NOW=datetime(2026,10,23,3,0,tzinfo=timezone.utc)
FC={"id":"fc-old","registered_at":"2026-10-23T02:00:00+00:00",
    "probability_yes":.65,"target_date":"2026-11-30"}
OUT={"forecast_id":"fc-old","outcome":"yes","reviewed_at":"2026-12-01T00:00:00Z"}

class ImmutabilityGuardTests(unittest.TestCase):
    def test_cannot_edit_or_remove_old_registered_prediction(self):
        a={"forecasts":[FC]}
        self.assertFalse(immutability_errors(a,{"forecasts":[FC]},"forecasts","id"))
        self.assertTrue(immutability_errors(a,{"forecasts":[]},"forecasts","id"))
        changed=dict(FC,probability_yes=.91)
        self.assertTrue(immutability_errors(a,{"forecasts":[changed]},"forecasts","id"))
        changed2=dict(FC,target_date="2027-02-01")
        self.assertTrue(immutability_errors(a,{"forecasts":[changed2]},"forecasts","id"))

    def test_old_outcome_cannot_be_rewritten(self):
        self.assertTrue(immutability_errors({"outcomes":[OUT]},
                 {"outcomes":[dict(OUT,outcome="no")]},"outcomes","forecast_id"))
        self.assertFalse(immutability_errors({"outcomes":[OUT]},
                 {"outcomes":[OUT,dict(OUT,forecast_id="fc-next")]},"outcomes","forecast_id"))

    def test_backdating_guard(self):
        old={"forecasts":[]}
        current={"forecasts":[FC]}
        self.assertEqual(validate_new_registration_times(old,current,NOW),[])
        late={"forecasts":[dict(FC,registered_at="2026-10-01T00:00:00+00:00")]}
        self.assertTrue(validate_new_registration_times(old,late,NOW))
        future={"forecasts":[dict(FC,registered_at="2026-10-25T00:00:00+00:00")]}
        self.assertTrue(validate_new_registration_times(old,future,NOW))
        self.assertEqual(validate_new_registration_times({"forecasts":[FC]},late,NOW),[])

if __name__=="__main__":
    unittest.main()
