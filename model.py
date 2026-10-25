"""
model.py (version 3): all the maths lives here. app.py (the website) imports from this file.

Model: SEIR (Susceptible -> Exposed -> Infectious -> Recovered) with
  - a latent period (infected but not yet infectious), sampled from a range
  - two contact groups (high-contact and low-contact people)
  - people cutting back contacts as cases rise (behaviour feedback)
  - policy measures that start on a chosen day (contact reduction, case isolation)
  - an emergency vaccination campaign delivered over several days
  - route of transmission: how well distancing-type measures work against the disease
  - optional waning immunity
  - hospital capacity that raises the death rate when overwhelmed (1.13x by default)
"""
import numpy as np
import pandas as pd

from diseases import CATALOGUE, BENCHMARKS

STEPS = 4            # simulation steps per time unit (more = more accurate but slower)
K_BEHAV = 0.01       # prevalence at which people have cut contacts by half of their maximum response
OVERLOAD_MULT = 1.13  # death-risk multiplier when hospitals are overwhelmed (see evidence.OVERLOAD_STUDY)

# the uncertain facts the Monte Carlo varies, with display names
UNCERTAIN = {
    "r0": "R0 (contagiousness)",
    "infectious": "Infectious period",
    "latent": "Latent period",
    "death_pct": "Death rate",
    "hosp_pct": "Hospitalisation rate",
    "measure_eff": "Route of transmission (how well distancing works)",
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def activity_groups(het, p_high=0.2):
    """Split people into high- and low-contact groups.
    het = how many times more contacts the high group has (1 = everyone the same).
    Returns activity levels, group shares and cv2 (how uneven contacts are)."""
    a_low = 1.0 / (p_high * het + 1 - p_high)
    a = np.array([het * a_low, a_low])
    share = np.array([p_high, 1 - p_high])
    cv2 = float((share * a ** 2).sum() - 1.0)
    return a, share, cv2


def policy_factor(P):
    """Fraction of transmission left after contact reduction and case isolation.
    Contact reduction only blocks the share of spread that distancing can stop (route of transmission).
    Isolation only helps with the part of transmission that happens AFTER symptoms."""
    contact = P["contact_reduction"] * P.get("measure_eff", 1.0)
    return (1 - contact) * (1 - P["isolation"] * (1 - P["presym"]))


def intro_R(P):
    """Reproduction number when the first cases arrive."""
    vacc = P["coverage"] * P["efficacy"]
    pf = policy_factor(P) if P["policy_day"] == 0 else 1.0
    return P["r0"] * (1 - vacc) * pf


def outbreak_probability(R, k, n_cases):
    """Chance that n_cases introduced cases spark a large outbreak (branching process).
    k = dispersion: small k = a few superspreaders cause most infections, so outbreaks
    often fizzle out by chance."""
    if R <= 1:
        return 0.0
    q = 0.0
    for _ in range(300):
        q = (1 + R * (1 - q) / k) ** (-k)       # q = chance one case's line dies out
    return float(1 - q ** n_cases)


def growth_rate(R0, latent, infectious):
    """Early exponential growth rate per day of an SEIR epidemic (homogeneous mixing).
    Solves (r + sigma)(r + gamma) = R0 * sigma * gamma. Returns None if R0 <= 1."""
    if R0 <= 1:
        return None
    s, g = 1.0 / latent, 1.0 / infectious
    r = (-(s + g) + np.sqrt((s + g) ** 2 - 4 * s * g * (1 - R0))) / 2
    return float(r)


def doubling_time(R0, latent, infectious):
    r = growth_rate(R0, latent, infectious)
    return float(np.log(2) / r) if r else None


def days_to_capacity(res):
    """First day on which hospital demand exceeds capacity, or None."""
    over = res["demand"] > res["capacity"]
    return int(res["days"][int(np.argmax(over))]) if over.any() else None


# ------------------------------------------------------------------
# The simulation
# ------------------------------------------------------------------
def simulate(P):
    N = P["N"]
    unit = P.get("unit", 1)                      # days per time step (1 normally, 7 for slow diseases)
    sigma = unit / P["latent"]
    gamma = unit / P["infectious"]
    omega = unit / P["waning_days"] if P["waning_days"] > 0 else 0.0

    a, share, cv2 = activity_groups(P["het"])
    beta = P["r0"] * gamma / (1 + cv2)       # keeps the overall R0 equal to the slider value

    Ng = N * share
    I = P["I0"] * share
    E = np.zeros(2)
    S = (Ng - I) * (1 - P["coverage"] * P["efficacy"])
    R = Ng - S - I

    D = int(P["sim_days"] // unit)
    dt = 1 / STEPS
    pf_full = policy_factor(P)

    camp_day = P.get("campaign_day")
    ramp_steps = max(1, int(round(P.get("campaign_ramp", 14) / unit)))
    camp_started, camp_left, camp_S0 = False, 0, None

    S_out, E_out, I_out, R_out = [S.sum()], [E.sum()], [I.sum()], [R.sum()]
    new_inf_out = [0.0]

    for step in range(1, D + 1):
        elapsed = (step - 1) * unit
        pf = pf_full if elapsed >= P["policy_day"] else 1.0

        # emergency vaccination campaign, delivered evenly over ramp_steps
        if camp_day is not None and not camp_started and elapsed >= camp_day:
            camp_started, camp_left, camp_S0 = True, ramp_steps, S.copy()
        if camp_left > 0:
            moved = np.minimum(camp_S0 * P["campaign_coverage"] * P["efficacy"] / ramp_steps, S)
            S = S - moved
            R = R + moved
            camp_left -= 1

        day_inf = 0.0
        for _ in range(STEPS):
            prevalence = I.sum() / N
            behaviour = 1 - P["response"] * prevalence / (prevalence + K_BEHAV)
            force = beta * pf * behaviour * (a * I).sum() / N
            new_inf = np.minimum(a * force * S * dt, S)
            new_exp = np.minimum(sigma * E * dt, E)
            new_rec = np.minimum(gamma * I * dt, I)
            wane = np.minimum(omega * R * dt, R)
            S = S - new_inf + wane
            E = E + new_inf - new_exp
            I = I + new_exp - new_rec
            R = R + new_rec - wane
            day_inf += new_inf.sum()
        S_out.append(S.sum()); E_out.append(E.sum()); I_out.append(I.sum()); R_out.append(R.sum())
        new_inf_out.append(day_inf)

    I_arr = np.array(I_out)
    new_inf_arr = np.array(new_inf_out)

    # Health outcomes
    demand = I_arr * P["hosp_pct"] / 100
    capacity = P["beds_per_100k"] * N / 100_000
    overloaded = demand > capacity
    mult = P.get("overload_mult", OVERLOAD_MULT)
    death_rate = np.minimum(P["death_pct"] / 100 * np.where(overloaded, mult, 1.0), 1.0)
    total_infected = P["I0"] + new_inf_arr.sum()

    return {
        "days": np.arange(D + 1) * unit,
        "S": np.array(S_out), "E": np.array(E_out), "I": I_arr, "R": np.array(R_out),
        "new_inf": new_inf_arr,
        "demand": demand,
        "capacity": capacity,
        "total_infected": total_infected,
        "deaths": float((new_inf_arr * death_rate).sum()),
        "disabled": float(total_infected * P["disab_pct"] / 100),
        "peak_demand": float(demand.max()),
        "peak_inf": float(I_arr.max()),
        "peak_day": int(I_arr.argmax() * unit),      # argmax gives a step index, so convert to days
        "established": bool(I_arr.max() > 2 * P["I0"]),   # False if the outbreak just dies away
        "overwhelmed": bool(overloaded.any()),
        "days_overwhelmed": int(overloaded.sum() * unit),
    }


# ------------------------------------------------------------------
# Uncertainty: run many simulations with different plausible parameters
# ------------------------------------------------------------------
def _triangular(rng, lo, mode, hi):
    if hi <= lo:
        return float(lo)
    mode = min(max(mode, lo), hi)
    return float(rng.triangular(lo, mode, hi))


def sample_parameters(base, ranges, n_sims, seed=1):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_sims):
        P = dict(base)
        for name, (lo, mode, hi) in ranges.items():
            P[name] = _triangular(rng, lo, mode, hi)
        out.append(P)
    return out


def monte_carlo(base, ranges, n_sims, k, seed=1):
    """ranges = {param_name: (low, most_likely, high)}. Returns a table of outcomes."""
    rows, demand_curves = [], []
    for P in sample_parameters(base, ranges, n_sims, seed):
        res = simulate(P)
        p_takeoff = outbreak_probability(intro_R(P), k, int(P["I0"]))
        rows.append({
            "r0": P["r0"], "infectious": P["infectious"], "latent": P["latent"],
            "death_pct": P["death_pct"], "hosp_pct": P["hosp_pct"], "measure_eff": P["measure_eff"],
            "total_infected": res["total_infected"], "deaths": res["deaths"],
            "disabled": res["disabled"], "peak_demand": res["peak_demand"],
            "peak_inf": res["peak_inf"], "peak_day": res["peak_day"],
            "established": float(res["established"]),
            "overwhelmed": float(res["overwhelmed"]), "p_takeoff": p_takeoff,
        })
        demand_curves.append(res["demand"].astype(np.float32))
    return {
        "df": pd.DataFrame(rows),
        "demand": np.array(demand_curves),
        "capacity": res["capacity"],
        "days": res["days"],
    }


def sensitivity(df, outcome, params=None):
    """Rank correlation (Spearman) between each uncertain fact and an outcome.
    Near +1 or -1 = that fact drives the outcome; near 0 = it barely matters."""
    out = {}
    for p in (params or list(UNCERTAIN)):
        if p not in df or df[p].nunique() < 2 or df[outcome].nunique() < 2:
            out[p] = 0.0
        else:
            out[p] = float(df[[p, outcome]].rank().corr().iloc[0, 1])
    return out


def decision_grid(base, ranges, lever, levels, n_sims, k):
    """Try different strengths of one intervention and summarise the risk at each."""
    out = []
    for lv in levels:
        P = dict(base)
        P[lever] = float(lv)
        df = monte_carlo(P, ranges, n_sims, k)["df"]
        out.append({
            "level": float(lv),
            "p_overwhelm": df["overwhelmed"].mean(),
            "p_problem": (df["p_takeoff"] * df["overwhelmed"]).mean(),
            "deaths_median": df["deaths"].median(),
            "deaths_p95": df["deaths"].quantile(0.95),
        })
    return pd.DataFrame(out)


# ------------------------------------------------------------------
# The cost of waiting
# ------------------------------------------------------------------
def apply_lever(P, lever, strength, day, ramp=14):
    """Return settings with ONE intervention started on `day` (day=None means no action at all)."""
    Q = dict(P)
    Q.update(contact_reduction=0.0, isolation=0.0, policy_day=0, campaign_day=None, campaign_coverage=0.0)
    if day is None:
        return Q
    if lever == "contact":
        Q.update(contact_reduction=strength, policy_day=day)
    elif lever == "isolation":
        Q.update(isolation=strength, policy_day=day)
    elif lever == "campaign":
        Q.update(campaign_day=day, campaign_coverage=strength, campaign_ramp=ramp)
    return Q


def _stats(results):
    deaths = np.array([r["deaths"] for r in results])
    inf = np.array([r["total_infected"] for r in results])
    peak = np.array([r["peak_demand"] for r in results])
    over = np.array([float(r["overwhelmed"]) for r in results])
    return {
        "deaths_p5": np.percentile(deaths, 5), "deaths_med": np.median(deaths), "deaths_p95": np.percentile(deaths, 95),
        "inf_med": np.median(inf),
        "peak_p5": np.percentile(peak, 5), "peak_med": np.median(peak), "peak_p95": np.percentile(peak, 95),
        "p_overwhelm": over.mean(),
    }


def cost_of_delay(base, ranges, lever, strength, delays, n_sims, ramp=14, seed=7):
    """For each start day in `delays`, run the same set of plausible futures and summarise the outcome.
    Using the same futures for every delay means differences come from the delay, not from luck."""
    samples = sample_parameters(base, ranges, n_sims, seed)
    baseline = _stats([simulate(apply_lever(P, lever, strength, None, ramp)) for P in samples])
    rows = []
    for d in delays:
        s = _stats([simulate(apply_lever(P, lever, strength, d, ramp)) for P in samples])
        s["delay"] = d
        rows.append(s)
    capacity = simulate(samples[0])["capacity"]
    return {"summary": pd.DataFrame(rows), "baseline": baseline, "capacity": capacity}


def weekly_loss(summary, baseline_inf, step=7, weeks=3):
    """Average share of preventable infections lost per extra `step` days of delay
    (looking at the first `weeks` steps). Returns None if the delay grid has no such steps."""
    inf = dict(zip(summary["delay"], summary["inf_med"]))
    losses = []
    for i in range(weeks):
        d0, d1 = i * step, (i + 1) * step
        if d0 in inf and d1 in inf:
            prevented0 = baseline_inf - inf[d0]
            prevented1 = baseline_inf - inf[d1]
            if prevented0 > 0:
                losses.append(max(0.0, (prevented0 - prevented1) / prevented0))
    return float(np.mean(losses)) if losses else None


# ------------------------------------------------------------------
# Learning from data
# ------------------------------------------------------------------
def estimate_growth(days, cases, latent, infectious):
    """Fit exponential growth to early case counts and convert it to R0.
    R0 = (1 + r * latent period) * (1 + r * infectious period) for an SEIR model."""
    days = np.asarray(days, float)
    cases = np.asarray(cases, float)
    m = cases > 0
    if m.sum() < 5:
        return None
    coef, cov = np.polyfit(days[m], np.log(cases[m]), 1, cov=True)
    r, b = float(coef[0]), float(coef[1])
    se = float(np.sqrt(cov[0, 0]))

    def r0_from(x):
        return max((1 + x * latent) * (1 + x * infectious), 0.0)

    return {
        "r": r, "b": b, "se": se, "coef": coef, "cov": cov,
        "doubling": float(np.log(2) / r) if r > 0 else None,
        "r0": r0_from(r), "r0_low": r0_from(r - 1.96 * se), "r0_high": r0_from(r + 1.96 * se),
        "n": int(m.sum()),
    }


def make_example_data(days=25, seed=3, growth=0.17, start=3):
    """SYNTHETIC data for demonstrating the app. Replace with real data."""
    rng = np.random.default_rng(seed)
    d = np.arange(days)
    return d, rng.poisson(start * np.exp(growth * d))


# ------------------------------------------------------------------
# Disease catalogue helpers
# ------------------------------------------------------------------
def _mid(r):
    return (r[0] + r[1]) / 2


def preset_settings(name):
    """Base settings and uncertainty ranges for a catalogue disease."""
    d = CATALOGUE[name]
    base = dict(
        N=d["N"], I0=d["I0"], r0=_mid(d["r0"]), latent=_mid(d["latent"]), infectious=_mid(d["infectious"]),
        coverage=0.0, efficacy=d["vax_eff"], contact_reduction=0.0, isolation=0.0, presym=d["presym"],
        policy_day=0, response=d["resp"], het=float(d["het"]), waning_days=d["waning"],
        sim_days=d["sim_days"], hosp_pct=_mid(d["hosp"]), death_pct=_mid(d["death"]),
        disab_pct=d["disab"], beds_per_100k=30, overload_mult=OVERLOAD_MULT, unit=d["unit"],
        measure_eff=_mid(d["measure_eff"]),
        campaign_day=None, campaign_coverage=0.0, campaign_ramp=14,
    )
    ranges = {
        "r0": (d["r0"][0], _mid(d["r0"]), d["r0"][1]),
        "infectious": (d["infectious"][0], _mid(d["infectious"]), d["infectious"][1]),
        "latent": (d["latent"][0], _mid(d["latent"]), d["latent"][1]),
        "death_pct": (d["death"][0], _mid(d["death"]), d["death"][1]),
        "hosp_pct": (d["hosp"][0], _mid(d["hosp"]), d["hosp"][1]),
        "measure_eff": (d["measure_eff"][0], _mid(d["measure_eff"]), d["measure_eff"][1]),
    }
    return base, ranges, d["k"]


SCENARIOS = {
    "none": "No measures (natural course)",
    "moderate": "Moderate measures (50% contact reduction from day 14, or year 1 for HIV)",
}


def run_all_diseases(scenario, n_sims=60):
    """Run the uncertainty analysis for every catalogue disease (except Custom) under one scenario."""
    out = {}
    for name in CATALOGUE:
        if name.startswith("Custom"):
            continue
        base, ranges, k = preset_settings(name)
        if scenario == "moderate":
            base.update(contact_reduction=0.5, policy_day=365 if base["unit"] > 1 else 14)
        n = n_sims if base["unit"] == 1 else max(20, n_sims // 3)
        out[name] = {"df": monte_carlo(base, ranges, n, k)["df"], "N": base["N"],
                     "capacity": base["beds_per_100k"] * base["N"] / 100_000, "unit": base["unit"]}
    return out


# ------------------------------------------------------------------
# Real-world benchmarks
# ------------------------------------------------------------------
def _verdict(obs, lo, med, hi):
    if lo <= obs <= hi:
        return "Inside model range"
    if med > obs:
        return f"Model {med / max(obs, 1e-9):.1f}x too high"
    return f"Model {obs / max(med, 1e-9):.1f}x too low"


def cluster_sizes(R_range, k_range, n_intro, n_sims, cap=5000, seed=2, min_share_size=100):
    """Simulate chains of infection started by n_intro cases (branching process with superspreading).
    Each case infects a random number of others (negative binomial, mean R, dispersion k).
    Sizes are capped at `cap` (a runaway outbreak). Also returns, for clusters of at least
    min_share_size cases (and below the cap), the share of cases traced to the 5 biggest spreaders."""
    rng = np.random.default_rng(seed)
    sizes = np.empty(n_sims)
    shares = np.full(n_sims, np.nan)
    for i in range(n_sims):
        R = _triangular(rng, R_range[0], _mid(R_range), R_range[1])
        k = _triangular(rng, k_range[0], _mid(k_range), k_range[1])
        p = k / (k + R)
        gen = n_intro
        total = n_intro
        offs = []
        while gen > 0 and total < cap:
            draws = rng.negative_binomial(k, p, size=gen)
            offs.append(draws)
            gen = int(draws.sum())
            total += gen
        sizes[i] = min(total, cap)
        if min_share_size <= total < cap and offs:
            allo = np.concatenate(offs)
            if allo.sum() > 0:
                shares[i] = np.sort(allo)[::-1][:5].sum() / allo.sum()
    return sizes, shares


def _dist_row(metric, observed, values, fmt="{:,.0f}"):
    lo, med, hi = np.percentile(values, [5, 50, 95])
    return {
        "metric": metric,
        "observed": fmt.format(observed),
        "model": f"{fmt.format(med)} (90% range {fmt.format(lo)} to {fmt.format(hi)})",
        "verdict": _verdict(observed, lo, med, hi),
    }


def run_benchmark(name, n_sims=150, reporting=None):
    """Compare the model with a documented real-world outbreak. Returns rows for a table and an optional histogram."""
    b = BENCHMARKS[name]
    d = CATALOGUE[name]
    kind = b["kind"]
    res = {"title": b["title"], "kind": kind, "rows": [], "hist": None, "verify": b.get("verify", "")}

    if kind == "simulation":
        base, ranges, k = preset_settings(name)
        for key, val in b["overrides"].items():
            if key == "r0_range":
                ranges["r0"] = (val[0], _mid(val), val[1])
            else:
                base[key] = val
                if key in ranges:
                    ranges[key] = (val, val, val)
        rep = b["reporting_default"] if reporting is None else reporting
        df = monte_carlo(base, ranges, n_sims, k)["df"]
        reported = df["total_infected"].to_numpy() * rep
        deaths = df["deaths"].to_numpy()
        res["rows"] = [
            _dist_row("Reported cases", b["observed"]["Reported cases"], reported),
            _dist_row("Deaths", b["observed"]["Deaths"], deaths),
        ]
        res["hist"] = {"values": reported, "observed": b["observed"]["Reported cases"], "label": "Reported cases"}
        res["attack"] = float(np.median(df["total_infected"]) / base["N"])
        res["reporting"] = rep

    elif kind == "cluster":
        obs = b["observed"]
        k_rng = (d["k"] * 0.4, d["k"] * 1.6)
        sc, _ = cluster_sizes(d["r0"], k_rng, 1, 2000)
        sh, top = cluster_sizes(b["hospital_R"], k_rng, 1, 2000)
        pc, ph = float((sc >= obs["cases"]).mean()), float((sh >= obs["cases"]).mean())
        verdict1 = ("Rare in the community, plausible in hospital-type settings" if pc < 0.01 <= ph
                    else ("Plausible in both" if pc >= 0.01 else "Rare in both settings"))
        res["rows"].append({
            "metric": f"Chance one introduction causes {obs['cases']} or more cases",
            "observed": "It happened (South Korea, 2015)",
            "model": f"community R {d['r0'][0]}-{d['r0'][1]}: {pc:.2%}; hospital-type R {b['hospital_R'][0]}-{b['hospital_R'][1]}: {ph:.1%}",
            "verdict": verdict1,
        })
        cfr = obs["deaths"] / obs["cases"]
        lo_d, hi_d = d["death"][0] / 100, d["death"][1] / 100
        res["rows"].append({
            "metric": "Deaths per case", "observed": f"{cfr:.0%} ({obs['deaths']} of {obs['cases']})",
            "model": f"{lo_d:.0%} to {hi_d:.0%} (catalogue range)",
            "verdict": "Inside model range" if lo_d - 1e-9 <= cfr <= hi_d else "Outside model range",
        })
        valid = top[~np.isnan(top)]
        if len(valid) >= 20:
            lo, med, hi = np.percentile(valid, [5, 50, 95])
            res["rows"].append({
                "metric": "Share of cases traced to the 5 biggest spreaders (large clusters)",
                "observed": f"{obs['top5_share']:.0%} (153 of 184)",
                "model": f"{med:.0%} (90% range {lo:.0%} to {hi:.0%}), from {len(valid)} large simulated clusters",
                "verdict": _verdict(obs["top5_share"], lo, med, hi),
            })
        res["hist"] = {"values": sh[sh > 1], "observed": obs["cases"], "label": "Cases from one introduction (hospital-type R)", "log": True}

    elif kind == "severity":
        obs = b["observed"]
        ratio = d["disab"] / 100
        implied = 1 / ratio
        lo_imp, hi_imp = 1 / obs["ratio_high"], 1 / obs["ratio_low"]
        res["rows"] = [
            {"metric": "Paralysis per infection (unvaccinated)",
             "observed": f"1 in {1 / obs['ratio_high']:,.0f} to 1 in {1 / obs['ratio_low']:,.0f} (depends on poliovirus type)",
             "model": f"1 in {implied:,.0f} (catalogue value {d['disab']}%)",
             "verdict": "Inside published range" if obs["ratio_low"] <= ratio <= obs["ratio_high"] else "Outside published range"},
            {"metric": "Infections implied by one paralytic case",
             "observed": f"{lo_imp:,.0f} to {hi_imp:,.0f}",
             "model": f"{implied:,.0f}",
             "verdict": "Inside published range" if lo_imp <= implied <= hi_imp else "Outside published range"},
        ]

    elif kind == "prevalence":
        obs = b["observed"]
        base, ranges, k = preset_settings(name)
        n = min(n_sims, 60)
        t_target, peaks, t_peak = [], [], []
        reached = 0
        for P in sample_parameters(base, ranges, n, 3):
            r = simulate(P)
            prev = r["I"] / P["N"]
            days = r["days"]
            i1 = np.argmax(prev >= obs["start"]) if (prev >= obs["start"]).any() else None
            peaks.append(prev.max())
            if i1 is not None:
                t_peak.append((days[int(prev.argmax())] - days[i1]) / 365.25)
                if (prev >= obs["target"]).any():
                    i2 = int(np.argmax(prev >= obs["target"]))
                    t_target.append((days[i2] - days[i1]) / 365.25)
                    reached += 1
        peaks = np.array(peaks)
        prow = _dist_row("Peak prevalence", obs["peak"], peaks, "{:.1%}")
        prow["model"] += f"; {len(t_peak)} of {n} futures reach {obs['start']:.1%} within {d['sim_days'] / 365.25:.0f} years"
        res["rows"].append(prow)
        if t_target:
            row = _dist_row(f"Years for prevalence to rise from {obs['start']:.1%} to {obs['target']:.1%}",
                            obs["years_to_target"], np.array(t_target), "{:.1f}")
            row["model"] += f"; {reached} of {n} futures get there"
        else:
            row = {"metric": f"Years for prevalence to rise from {obs['start']:.1%} to {obs['target']:.1%}",
                   "observed": f"{obs['years_to_target']:.1f}", "model": f"0 of {n} futures get there within {d['sim_days'] / 365.25:.0f} years",
                   "verdict": "Model far too slow"}
        res["rows"].append(row)
        res["hist"] = {"values": peaks * 100, "observed": obs["peak"] * 100, "label": "Peak prevalence (%)"}
    return res


def run_all_benchmarks(n_sims=150):
    return {name: run_benchmark(name, n_sims) for name in BENCHMARKS}
