"""Simple checks that the model behaves sensibly. Run with:  python test_model.py"""
import math
import numpy as np
import model
from model import simulate, outbreak_probability, preset_settings, apply_lever, OVERLOAD_MULT


def base(**kw):
    b, _, _ = preset_settings("Measles")
    b.update(coverage=0, efficacy=0, contact_reduction=0, isolation=0, campaign_day=None,
             response=0.0, het=1.0, waning_days=0, sim_days=600, N=100000, I0=10)
    b.update(kw)
    return b


def test_overload_default():
    assert OVERLOAD_MULT == 1.13


def test_r0_below_one_dies_out():
    r = simulate(base(r0=0.6))
    assert r["total_infected"] < 0.01 * 100000


def test_infections_never_exceed_population():
    for r0 in (2, 6, 15):
        r = simulate(base(r0=r0))
        assert r["total_infected"] <= 100000 * 1.001


def test_final_size_matches_theory():
    # homogeneous mixing, no behaviour change: z = 1 - exp(-R0 z)
    R0 = 3.0
    z = 0.5
    for _ in range(200):
        z = 1 - math.exp(-R0 * z)
    r = simulate(base(r0=R0, infectious=8.0, latent=5.0, sim_days=1200))
    assert abs(r["total_infected"] / 100000 - z) < 0.03, (r["total_infected"] / 100000, z)


def test_more_distancing_does_not_raise_deaths():
    d = [simulate(base(r0=3, contact_reduction=c, measure_eff=1.0, death_pct=1.0))["deaths"] for c in (0, 0.3, 0.6)]
    assert d[0] >= d[1] >= d[2]


def test_takeoff_probability_matches_theory():
    # k = 1 (geometric offspring): exact answer is 1 - 1/R
    assert abs(outbreak_probability(3.0, 1.0, 1) - (1 - 1 / 3)) < 0.01
    # very large k (Poisson offspring), R = 3: survival probability solves s = 1 - exp(-R s), about 0.94
    assert abs(outbreak_probability(3.0, 1000.0, 1) - 0.94) < 0.01
    # more superspreading (lower k) means a lower chance of takeoff
    assert outbreak_probability(3.0, 0.2, 1) < outbreak_probability(3.0, 5.0, 1)


def test_later_action_costs_more():
    b = base(r0=3, death_pct=1.0, measure_eff=1.0)
    early = simulate(apply_lever(b, "contact", 0.6, 10))["total_infected"]
    late = simulate(apply_lever(b, "contact", 0.6, 60))["total_infected"]
    assert late >= early


def test_peak_day_is_in_days_for_weekly_steps():
    b, _, _ = preset_settings("HIV (untreated)")
    r = simulate(b)
    assert r["peak_day"] % 7 == 0 and r["peak_day"] <= b["sim_days"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
    print("All tests passed")
