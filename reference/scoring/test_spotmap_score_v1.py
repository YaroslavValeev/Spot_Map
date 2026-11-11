"""Run: python -m unittest -v test_spotmap_score_v1.py"""
import unittest
from spotmap_score_v1 import compute, Observation, PROFILES

class SpotScoreTests(unittest.TestCase):
    def example(self, profile='wakesurf_v1'):
        return [Observation(d, 88, 'independent_expert') for d in PROFILES[profile]]

    def test_no_obs_is_unrated(self):
        r=compute('wakesurf_v1', [], safety_check_verified=True)
        self.assertIsNone(r.score); self.assertEqual(r.coverage,0)

    def test_single_five_stars_not_100(self):
        r=compute('wakesurf_v1', [Observation('service',100,'verified_visit')],
                  safety_check_verified=True)
        self.assertEqual(r.per_domain['service']['posterior'],73.75)
        self.assertIsNone(r.score)

    def test_expert_example(self):
        a=[90,85,88,92,80,70,75]
        obs=[Observation(d,x,'independent_expert') for d,x in zip(PROFILES['wakesurf_v1'],a)]
        r=compute('wakesurf_v1',obs,safety_check_verified=True)
        self.assertEqual(r.status,'preliminary')
        self.assertEqual(r.score,75)
        self.assertAlmostEqual(r.raw_score,74.925)

    def test_requires_safety_evidence(self):
        r=compute('wakesurf_v1',self.example(),safety_check_verified=False)
        self.assertIsNone(r.score);self.assertEqual(r.status,'unrated')

    def test_restricted(self):
        r=compute('wakesurf_v1',self.example(),safety_check_verified=True,critical_safety_issue=True)
        self.assertEqual(r.status,'restricted');self.assertIsNone(r.score)

    def test_conflict_of_interest_zero(self):
        obs=self.example(); obs.append(Observation('service',100,'verified_visit', conflict_of_interest=True))
        r=compute('wakesurf_v1',obs,safety_check_verified=True)
        self.assertEqual(r.per_domain['service']['n_eff'],3.0)

    def test_cable_profile_separate(self):
        r=compute('wakeboard_cable_v1',self.example('wakeboard_cable_v1'),safety_check_verified=True)
        self.assertIn('course_setup',r.per_domain)
        self.assertNotIn('riding_conditions',r.per_domain)

    def test_requires_two_sources_and_visits_or_audit(self):
        a=compute('wakesurf_v1',self.example(),safety_check_verified=True,
                  independent_source_groups=2,verified_visits=3)
        self.assertEqual(a.status,'verified')

    def test_duplicate_same_period_excluded(self):
        obs=self.example()
        obs += [Observation('service',100,'verified_visit',author_id='u1',period_key='2026-Q4'),
                Observation('service',0,'verified_visit',author_id='u1',period_key='2026-Q4')]
        r=compute('wakesurf_v1',obs,safety_check_verified=True)
        self.assertEqual(r.per_domain['service']['n_eff'],4.0)

    def test_missing_not_zero(self):
        r=compute('wakesurf_v1',[Observation('service',100,'independent_expert')],
                  safety_check_verified=True)
        self.assertIsNone(r.per_domain['coaching']['posterior'])
        self.assertEqual(r.coverage,0.1)

if __name__ == '__main__': unittest.main()
