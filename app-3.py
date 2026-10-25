import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from diseases import CATALOGUE, BENCHMARKS
from evidence import EVIDENCE, OVERLOAD_STUDY, GLOSSARY, CAVEAT
from model import (
    simulate, monte_carlo, decision_grid, estimate_growth, make_example_data,
    cost_of_delay, weekly_loss, apply_lever, doubling_time, days_to_capacity,
    sensitivity, run_all_diseases, run_all_benchmarks, run_benchmark,
    UNCERTAIN, SCENARIOS, OVERLOAD_MULT,
)

st.set_page_config(page_title="Emerging Disease Risk Tool", layout="wide")
st.title("Emerging Disease Risk and Decision Tool")
st.write(
    "Choose a known disease from the catalogue, or describe a new one. The tool learns from case data, "
    "simulates many plausible futures, shows how the cost of waiting grows with every day of delay, "
    "and checks itself against real outbreaks."
)


# Cached wrappers so heavy simulations only rerun when their settings change
@st.cache_data(show_spinner=False)
def run_mc(base, ranges, n_sims, k):
    return monte_carlo(base, ranges, n_sims, k)


@st.cache_data(show_spinner=False)
def run_grid(base, ranges, lever, levels, n_sims, k):
    return decision_grid(base, ranges, lever, list(levels), n_sims, k)


@st.cache_data(show_spinner=False)
def run_cost(base, ranges, lever, strength, delays, n_sims, ramp):
    return cost_of_delay(base, ranges, lever, strength, list(delays), n_sims, ramp)


@st.cache_data(show_spinner=False)
def run_all(scenario, n_sims):
    return run_all_diseases(scenario, n_sims)


@st.cache_data(show_spinner=False)
def run_all_bm(n_sims):
    return run_all_benchmarks(n_sims)


def mid(r):
    return (r[0] + r[1]) / 2


def glossary():
    with st.expander("Glossary of technical terms (click to show or hide)", expanded=False):
        for term in sorted(GLOSSARY, key=str.lower):
            st.markdown(f"**{term}**: {GLOSSARY[term]}")


def band(fig, x, lo, med, hi, name, dash=None):
    """Add a median line with a shaded 5th to 95th percentile band."""
    fig.add_trace(go.Scatter(x=x, y=hi, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x, y=lo, fill="tonexty", line=dict(width=0), name=f"{name}: 90% of futures"))
    fig.add_trace(go.Scatter(x=x, y=med, name=f"{name}: median", line=dict(dash=dash) if dash else None))


def span(values, fmt="{:,.0f}"):
    lo, med, hi = np.percentile(values, [5, 50, 95])
    return fmt.format(med), f"5th to 95th: {fmt.format(lo)} to {fmt.format(hi)}"


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
sb = st.sidebar
sb.header("Disease catalogue")
disease = sb.selectbox("Choose a disease", list(CATALOGUE))
d = CATALOGUE[disease]
unit = d["unit"]
slow = unit > 1
sb.caption("Choosing a disease loads its typical values into the sliders below. You can still change them.")


def K(name):
    # a different key per disease makes every slider reset to that disease's values
    return f"{name}|{disease}"


sb.header("1. The disease (plausible ranges)")
sb.caption("Drag either end of a range slider. A new disease is uncertain, so most inputs are ranges.")
r0_rng = sb.slider("R0: people infected per case", 0.1, 20.0, (float(d["r0"][0]), float(d["r0"][1])), 0.1, key=K("r0"))
if slow:
    inf_rng = sb.slider("Infectious period (days)", 100.0, 4000.0, (float(d["infectious"][0]), float(d["infectious"][1])), 50.0, key=K("inf"))
else:
    inf_rng = sb.slider("Infectious period (days)", 1.0, 40.0, (float(d["infectious"][0]), float(d["infectious"][1])), 0.5, key=K("inf"))
latent_rng = sb.slider("Latent period (days from infection to infectious)", 0.5, 30.0,
                       (float(d["latent"][0]), float(d["latent"][1])), 0.5, key=K("lat"))
presym = sb.slider("Share of spread before or without symptoms", 0.0, 1.0, float(d["presym"]), 0.05, key=K("pre"))
k = sb.slider("Superspreading (k): lower = more clustered", 0.05, 5.0, float(d["k"]), 0.05, key=K("k"))
route_rng = sb.slider("Route of transmission: how well distancing-type measures work (1 = fully)", 0.1, 1.0,
                      (float(d["measure_eff"][0]), float(d["measure_eff"][1])), 0.05, key=K("route"),
                      help="Airborne or water-borne spread is harder to stop by distancing alone. For a new disease the "
                           "route may be unknown, so use a wide range.")
sb.caption(f"Route: {d['route']}")

sb.header("2. Severity (plausible ranges)")
death_rng = sb.slider("Deaths per 100 infections (%)", 0.0, 100.0, (float(d["death"][0]), float(d["death"][1])), 0.05, key=K("death"))
hosp_rng = sb.slider("Needing hospital care (%)", 0.0, 100.0, (float(d["hosp"][0]), float(d["hosp"][1])), 0.5, key=K("hosp"))
disab_pct = sb.slider("Permanent disability or lifelong condition per 100 infections (%)", 0.0, 100.0, float(d["disab"]), 0.05, key=K("disab"))

sb.header("3. Population and health system")
N = sb.slider("Population", 10_000, 1_000_000, int(d["N"]), 10_000, key=K("N"))
I0 = sb.slider("Cases introduced", 1, 200, int(d["I0"]), key=K("I0"))
beds = sb.slider("Hospital beds free for this disease (per 100,000)", 0, 300, 30)
overload = sb.slider("Death-risk multiplier when hospitals are overwhelmed", 1.0, 3.0, float(OVERLOAD_MULT), 0.01,
                     help="Default 1.13 = odds ratio for in-hospital death at the highest versus lowest level of bed strain "
                          "(Emergency Medicine Journal 2023, doi 10.1136/emermed-2023-213329). See the Method tab for caveats.")
if slow:
    sim_days = sb.slider("Days to simulate", 730, 14600, int(d["sim_days"]), 365, key=K("sim"))
else:
    sim_days = sb.slider("Days to simulate", 90, 365, int(d["sim_days"]), 10, key=K("sim"))

sb.header("4. Realism")
het = sb.slider("Contact inequality (1 = everyone mixes equally)", 1, 15, int(d["het"]), key=K("het"))
resp = sb.slider("Voluntary behaviour change as cases rise", 0.0, 0.9, float(d["resp"]), 0.05, key=K("resp"))
waning = sb.slider("Immunity lasts (days, 0 = for life)", 0, 730, int(d["waning"]), 5, key=K("wan"))

sb.header("5. Current measures")
coverage = sb.slider("Vaccination coverage before the outbreak (%)", 0, 100, 0) / 100
efficacy = sb.slider("Vaccine effectiveness (%)", 0, 100, int(round(d["vax_eff"] * 100)), key=K("eff")) / 100
contact_red = sb.slider("Contact reduction (%)", 0, 90, 0) / 100
isolation = sb.slider("Symptomatic cases isolated (%)", 0, 100, 0) / 100
policy_day = sb.slider("Contact reduction and isolation start on day", 0, 3650 if slow else 90, 0)
camp_day = sb.slider("Emergency vaccination campaign starts on day (0 = none)", 0, 3650 if slow else 180, 0)
camp_cov = sb.slider("Campaign reaches (% of susceptible people)", 0, 100, 80) / 100
camp_ramp = sb.slider("Days taken to deliver the campaign", 1, 60, 14)

latent = mid(latent_rng)
base = dict(
    N=N, I0=I0, r0=mid(r0_rng), latent=latent, infectious=mid(inf_rng),
    coverage=coverage, efficacy=efficacy, contact_reduction=contact_red,
    isolation=isolation, presym=presym, policy_day=policy_day, response=resp,
    het=float(het), waning_days=waning, sim_days=sim_days,
    hosp_pct=mid(hosp_rng), death_pct=mid(death_rng), disab_pct=disab_pct,
    beds_per_100k=beds, overload_mult=overload, unit=unit, measure_eff=mid(route_rng),
    campaign_day=(camp_day if camp_day > 0 else None), campaign_coverage=camp_cov, campaign_ramp=camp_ramp,
)

# ------------------------------------------------------------------
# ABOUT THIS DISEASE
# ------------------------------------------------------------------
with st.expander(f"About: {disease}", expanded=(disease != "Custom (new disease)")):
    st.write(d["summary"])
    if d["fit"] != "n/a":
        st.write(f"**How well this model fits the disease:** {d['fit']}. {d['fit_note']}")
    st.write(f"**Route of transmission:** {d['route']}")
    table = pd.DataFrame(
        {
            "Value": [
                f"{d['r0'][0]} to {d['r0'][1]}",
                f"{d['latent'][0]:g} to {d['latent'][1]:g} days",
                d["incubation"],
                f"{d['infectious'][0]:g} to {d['infectious'][1]:g} days",
                f"{d['presym']:.0%}",
                f"{d['death'][0]:g} to {d['death'][1]:g}%",
                f"{d['hosp'][0]:g} to {d['hosp'][1]:g}%",
                f"{d['disab']:g}%",
            ]
        },
        index=["R0", "Latent period", "Incubation period (information only)", "Infectious period",
               "Spread before or without symptoms", "Deaths per 100 infections",
               "Needing hospital care", "Permanent disability or lifelong condition"],
    )
    st.table(table)
    for note in d["notes"]:
        st.markdown(f"- {note}")
    if d["sources"]:
        st.markdown("**Where to check these numbers:**")
        for s in d["sources"]:
            st.markdown(f"- {s}")
    st.caption("Values are rounded approximations. Items marked ASSUMPTION have no direct source: verify and cite before presenting.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["1. Learn from data", "2. Risk assessment", "3. Decisions", "4. Cost of waiting",
     "5. All diseases", "6. Model vs real world", "7. Method and assumptions"]
)

# ------------------------------------------------------------------
# TAB 1: LEARN FROM CASE DATA
# ------------------------------------------------------------------
fit = None
use_fit = False
with tab1:
    st.subheader("How fast is it spreading?")
    st.write(
        "Early in an outbreak, cases grow roughly exponentially. We fit that growth to daily case "
        "counts, convert it to R0, and test the method by hiding the most recent days and checking "
        "whether the forecast would have predicted them."
    )
    source = st.radio(
        "Case data", ["Example data (synthetic, for demonstration)", "Upload my own CSV"], horizontal=True
    )
    days_obs = cases_obs = None
    if source.startswith("Example"):
        days_obs, cases_obs = make_example_data()
        st.caption("This example is artificially generated. Upload real outbreak data for your final demo.")
    else:
        up = st.file_uploader("CSV with two columns: date (or day number), then new cases per day", type="csv")
        if up is not None:
            df_up = pd.read_csv(up)
            first = df_up.iloc[:, 0]
            if pd.api.types.is_numeric_dtype(first):
                days_obs = first.to_numpy(dtype=float)
            else:
                dates = pd.to_datetime(first)
                days_obs = (dates - dates.min()).dt.days.to_numpy(dtype=float)
            cases_obs = pd.to_numeric(df_up.iloc[:, 1], errors="coerce").fillna(0).to_numpy()

    if days_obs is not None:
        c1, c2 = st.columns(2)
        skip = c1.slider("Ignore the first N days (noisy start)", 0, 10, 0)
        holdout = c2.slider("Hold back the last N days to test the forecast", 0, 10, 4)

        last_day = days_obs.max()
        train = (days_obs >= days_obs.min() + skip) & (days_obs <= last_day - holdout)
        fit = estimate_growth(days_obs[train], cases_obs[train], latent, mid(inf_rng))

        if fit is None:
            st.warning("Not enough data points with cases to fit (need at least 5).")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Daily growth", f"{(np.exp(fit['r']) - 1) * 100:.0f}% per day")
            m2.metric("Doubling time", f"{fit['doubling']:.1f} days" if fit["doubling"] else "Not growing")
            m3.metric("Estimated R0", f"{fit['r0']:.1f}",
                      f"95% range {fit['r0_low']:.1f} to {fit['r0_high']:.1f}", delta_color="off")

            t_train_end = days_obs[train].max()
            t_future = np.arange(t_train_end + 1, t_train_end + 1 + holdout + 7)
            t_all = np.concatenate([days_obs[train], t_future])
            rng = np.random.default_rng(0)
            draws = rng.multivariate_normal(fit["coef"], fit["cov"], 1000)
            mu = np.exp(draws[:, 1:2] + draws[:, 0:1] * t_all[None, :])
            sims = rng.poisson(mu)
            lo, med, hi = np.percentile(sims, [2.5, 50, 97.5], axis=0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=t_all, y=hi, line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=t_all, y=lo, fill="tonexty", line=dict(width=0), name="95% prediction range"))
            fig.add_trace(go.Scatter(x=t_all, y=med, name="Model forecast"))
            fig.add_trace(go.Scatter(x=days_obs[train], y=cases_obs[train], mode="markers", name="Data used to fit"))
            held = days_obs > t_train_end
            if held.any():
                fig.add_trace(go.Scatter(x=days_obs[held], y=cases_obs[held], mode="markers",
                                         marker=dict(symbol="x", size=10), name="Held-back data"))
            fig.update_layout(xaxis_title="Day", yaxis_title="New cases per day")
            if st.checkbox("Log scale (growth looks like a straight line)"):
                fig.update_yaxes(type="log")
            st.plotly_chart(fig)

            if held.any():
                idx = np.searchsorted(t_all, days_obs[held])
                actual = cases_obs[held]
                inside = ((actual >= lo[idx]) & (actual <= hi[idx])).mean()
                mape = np.mean(np.abs(med[idx] - actual) / np.maximum(actual, 1))
                st.write(
                    f"**Backtest:** on the {int(held.sum())} held-back days, the forecast was off by "
                    f"{mape:.0%} on average and {inside:.0%} of real values fell inside the 95% range."
                )
            use_fit = st.checkbox("Use this R0 estimate (and its range) in the risk assessment", value=False)
    glossary()

# ranges used by tabs 2 to 5
r0_use = r0_rng
r0_mode = mid(r0_rng)
if use_fit and fit is not None:
    r0_use = (float(np.clip(fit["r0_low"], 0.1, 20)), float(np.clip(fit["r0_high"], 0.1, 20)))
    r0_mode = float(np.clip(fit["r0"], r0_use[0], r0_use[1]))
ranges = {
    "r0": (r0_use[0], r0_mode, r0_use[1]),
    "infectious": (inf_rng[0], mid(inf_rng), inf_rng[1]),
    "latent": (latent_rng[0], mid(latent_rng), latent_rng[1]),
    "death_pct": (death_rng[0], mid(death_rng), death_rng[1]),
    "hosp_pct": (hosp_rng[0], mid(hosp_rng), hosp_rng[1]),
    "measure_eff": (route_rng[0], mid(route_rng), route_rng[1]),
}
central = dict(base, r0=r0_mode)


def rating(p):
    if p < 0.05:
        return "LOW", st.success
    if p < 0.20:
        return "MODERATE", st.warning
    if p < 0.50:
        return "HIGH", st.error
    return "VERY HIGH", st.error


def when(days_value):
    """Format a time in days (years for slow diseases)."""
    return f"{days_value / 365.25:.1f} years" if slow else f"day {days_value:.0f}"


# ------------------------------------------------------------------
# TAB 2: RISK ASSESSMENT
# ------------------------------------------------------------------
with tab2:
    st.subheader("How likely is this to become a serious problem?")
    st.write(
        "We run many simulated futures, each with different plausible values for the uncertain "
        "facts about the disease. The share of futures that end badly is the risk."
    )
    if slow:
        st.info("This disease runs over decades, so simulations take longer.")
    n_sims = st.slider("Number of simulated futures", 50, 400, 100 if slow else 150, 50)
    if st.button("Run risk assessment", type="primary"):
        with st.spinner("Simulating..."):
            st.session_state["mc"] = run_mc(base, ranges, n_sims, k)
            st.session_state["mc_disease"] = disease

    res = st.session_state.get("mc")
    if res is None:
        st.info("Choose a disease and settings on the left, then press the button. Press it again after changing settings.")
    else:
        if st.session_state.get("mc_disease") != disease:
            st.warning(f"These results are for {st.session_state.get('mc_disease')}. Press the button to update them for {disease}.")
        df = res["df"]
        p_take = df["p_takeoff"].mean()
        p_over = df["overwhelmed"].mean()
        p_prob = (df["p_takeoff"] * df["overwhelmed"]).mean()
        label, box = rating(p_prob)
        box(f"Overall risk: **{label}**. About {p_prob:.0%} chance this disease causes a serious problem "
            f"(an introduction takes off AND hospitals are overwhelmed).")

        a, b, c, e = st.columns(4)
        a.metric("Chance introduction takes off", f"{p_take:.0%}")
        b.metric("Chance hospitals overwhelmed if it takes off", f"{p_over:.0%}")
        per100k = df["deaths"] / N * 100_000
        c.metric("Deaths per 100,000 (median)", f"{per100k.median():.0f}",
                 f"90% range {per100k.quantile(.05):.0f} to {per100k.quantile(.95):.0f}", delta_color="off")
        e.metric("Permanent disabilities (median)", f"{df['disabled'].median():,.0f}")

        st.markdown("**Peak range: when and how big is the worst point?**")
        est = df[df["established"] == 1]
        pa, pb, pc = st.columns(3)
        if len(est) >= 5:
            tv = est["peak_day"] / 365.25 if slow else est["peak_day"]
            val, rng_txt = span(tv, "{:,.1f}" if slow else "{:,.0f}")
            pa.metric("Time of peak infections (years)" if slow else "Day of peak infections", val, rng_txt, delta_color="off")
            val, rng_txt = span(est["peak_inf"] / N * 100, "{:,.1f}")
            pb.metric("Peak share of population infectious (%)", val, rng_txt, delta_color="off")
        else:
            pa.metric("Day of peak infections", "No epidemic peak")
            pb.metric("Peak share of population infectious (%)", "Outbreak dies out")
        val, rng_txt = span(df["peak_demand"] / N * 100_000, "{:,.0f}")
        pc.metric("Peak hospital demand per 100,000", val, rng_txt, delta_color="off")
        st.caption(f"An epidemic peak occurred in {len(est) / len(df):.0%} of simulated futures; the peak ranges use only those futures. "
                   "For diseases where R is below 1, most outbreaks simply die away.")

        days = res["days"]
        p5, p50, p95 = np.percentile(res["demand"], [5, 50, 95], axis=0)
        xs = days / 365.25 if slow else days
        fig = go.Figure()
        band(fig, xs, p5, p50, p95, "Hospital demand")
        fig.add_hline(y=res["capacity"], line_color="red", annotation_text="Hospital capacity")
        fig.update_layout(xaxis_title="Years" if slow else "Day", yaxis_title="People needing hospital care",
                          title="Hospital demand across simulated futures")
        st.plotly_chart(fig)

        st.markdown("**What drives the risk? (priorities for data collection)**")
        outcomes = {"Peak hospital demand": "peak_demand", "Deaths": "deaths", "Total infected": "total_infected"}
        out_label = st.selectbox("Outcome to explain", list(outcomes), key="sens_outcome_risk")
        corr = sensitivity(df, outcomes[out_label])
        order = sorted(corr, key=lambda p: -abs(corr[p]))
        sfig = go.Figure(go.Bar(x=[UNCERTAIN[p] for p in order], y=[corr[p] for p in order]))
        sfig.update_layout(yaxis_title=f"Rank correlation with {out_label.lower()}", yaxis_range=[-1, 1])
        st.plotly_chart(sfig)
        top = order[0]
        if abs(corr[top]) < 0.15:
            st.write("No single uncertain fact dominates this outcome.")
        else:
            st.write(f"The uncertain fact that matters most is **{UNCERTAIN[top].lower()}**. "
                     f"Measuring it better would reduce uncertainty the most, so collect that data first.")
        if base["contact_reduction"] == 0 and base["isolation"] == 0 and base["campaign_day"] is None:
            st.info("The route of transmission only matters once measures are applied. Set contact reduction above 0 "
                    "in the sidebar and run again to see how much it changes the picture.")
    glossary()

# ------------------------------------------------------------------
# TAB 3: DECISIONS
# ------------------------------------------------------------------
with tab3:
    st.subheader("What should we do?")
    lever_names = {"Contact reduction": "contact_reduction", "Vaccination coverage": "coverage",
                   "Case isolation": "isolation"}
    lever_label = st.radio("Intervention to test", list(lever_names), horizontal=True)
    lever = lever_names[lever_label]
    target = st.slider("Maximum acceptable chance of overwhelming hospitals (%)", 1, 50, 5, key="tgt_dec") / 100
    levels = tuple(float(x) for x in np.round(np.arange(0, 0.95, 0.1), 2))
    n_grid = 20 if slow else 60

    if st.button("Run decision analysis", type="primary"):
        with st.spinner("Testing interventions..."):
            st.session_state["grid"] = run_grid(base, ranges, lever, levels, n_grid, k)
            st.session_state["grid_lever"] = lever_label

    grid = st.session_state.get("grid")
    if grid is None:
        st.info("Press the button to compare different strengths of this intervention. "
                "To see what delay costs, open the 'Cost of waiting' tab.")
    else:
        gl = st.session_state["grid_lever"]
        gfig = go.Figure()
        gfig.add_trace(go.Scatter(x=grid["level"] * 100, y=grid["p_overwhelm"] * 100,
                                  name="Chance hospitals overwhelmed (%)"))
        gfig.add_hline(y=target * 100, line_dash="dot", annotation_text="Your acceptable risk")
        gfig.update_layout(xaxis_title=f"{gl} (%)", yaxis_title="Chance (%)")
        st.plotly_chart(gfig)

        ok = grid[grid["p_overwhelm"] <= target]
        if len(ok):
            need = ok.iloc[0]
            st.success(
                f"**Recommendation:** about **{need['level']:.0%}** {gl.lower()} keeps the chance of "
                f"overwhelming hospitals at or below {target:.0%}. Median deaths at that level: "
                f"{need['deaths_median']:,.0f}."
            )
        else:
            st.error("None of the tested strengths reaches your target on its own. Combine interventions "
                     "(change the current measures on the left) or accept a higher risk.")

        dfig = go.Figure()
        dfig.add_trace(go.Bar(x=grid["level"] * 100, y=grid["deaths_median"], name="Median deaths"))
        dfig.add_trace(go.Scatter(x=grid["level"] * 100, y=grid["deaths_p95"], name="Bad-luck case (95th percentile)"))
        dfig.update_layout(xaxis_title=f"{gl} (%)", yaxis_title="Deaths")
        st.plotly_chart(dfig)
    glossary()

# ------------------------------------------------------------------
# TAB 4: COST OF WAITING
# ------------------------------------------------------------------
LEVER_LABEL = {"contact": "Contact reduction (distancing)", "isolation": "Isolating symptomatic cases",
               "campaign": "Emergency vaccination campaign"}
with tab4:
    st.subheader("The cost of waiting")
    st.write(
        "Epidemics grow exponentially, so every day of delay means more people are already infected when action "
        "begins. This tab tests the same intervention started on different days across many plausible futures, "
        "then sets the result beside published studies."
    )
    levers = d["levers"]
    lever = st.radio("Intervention", levers, format_func=lambda x: LEVER_LABEL[x], horizontal=True, key=f"lever|{disease}")
    is_camp = lever == "campaign"
    strength = st.slider("Campaign reaches (% of susceptible people)" if is_camp else "Share of transmission cut (%)",
                         10, 95, 80 if is_camp else 50, 5, key=f"str|{disease}|{lever}") / 100
    ramp = st.slider("Days taken to deliver the campaign", 1, 60, 14, key=f"ramp|{disease}") if is_camp else 14
    target_c = st.slider("Acceptable chance of overwhelming hospitals (%)", 1, 50, 5, key="tgt_cost") / 100

    natural = simulate(apply_lever(central, lever, strength, None, ramp))
    dtime = doubling_time(central["r0"], central["latent"], central["infectious"])
    cap_day = days_to_capacity(natural)
    q1, q2, q3 = st.columns(3)
    q1.metric("Doubling time (early growth)", f"{dtime:.1f} days" if dtime else "Not growing (R0 at or below 1)")
    q2.metric("Hospitals full (no action)", when(cap_day) if cap_day is not None else "Never in this scenario")
    q3.metric("Peak infections (no action)", when(natural["peak_day"]) if natural["established"] else "No epidemic peak")
    if dtime:
        st.caption(
            f"Rule of thumb: every {dtime:.1f} days of delay doubles the number of people already infected when action starts "
            "(early phase, simple mixing). Contact inequality and behaviour change slow growth later."
        )
    if central["r0"] <= 1:
        st.info("R0 is at or below 1, so community outbreaks fade by themselves and delay costs little. "
                "The danger for diseases like this is local clusters, such as in hospitals: see the real-world comparison tab.")

    delays = [0, 180, 365, 730, 1095, 1460, 1825, 2555, 3650] if slow else [0, 7, 14, 21, 28, 35, 42, 56, 70]
    ref_delay = 1095 if slow else 28
    n_cost = 12 if slow else 40
    if st.button("Run cost-of-waiting analysis", type="primary"):
        with st.spinner("Simulating many futures for every start day..."):
            st.session_state["cost"] = run_cost(base, ranges, lever, strength, tuple(delays), n_cost, ramp)
            st.session_state["cost_meta"] = (disease, lever, strength)

    cres = st.session_state.get("cost")
    if cres is None:
        st.info("Press the button to run the analysis. It uses your sidebar settings for the disease.")
    else:
        if st.session_state.get("cost_meta") != (disease, lever, strength):
            st.warning("These results were made with other settings. Press the button to update them.")
        sm = cres["summary"]
        bl = cres["baseline"]
        xs = sm["delay"] / 365.25 if slow else sm["delay"]
        xl = "Years until measures begin" if slow else "Day measures begin"

        fig = go.Figure()
        band(fig, xs, sm["deaths_p5"], sm["deaths_med"], sm["deaths_p95"], "Deaths")
        fig.add_hline(y=bl["deaths_med"], line_dash="dot", annotation_text="No action at all (median)")
        fig.update_layout(xaxis_title=xl, yaxis_title="Deaths", title="Deaths rise the longer action is delayed")
        st.plotly_chart(fig)

        row0 = sm[sm["delay"] == 0].iloc[0]
        rowr = sm[sm["delay"] == ref_delay].iloc[0]
        ref_label = "year 3" if slow else f"day {ref_delay}"
        if row0["deaths_med"] > 0:
            ratio = rowr["deaths_med"] / row0["deaths_med"]
            st.write(
                f"Starting on day 0: about **{row0['deaths_med']:,.0f} deaths** (5th to 95th {row0['deaths_p5']:,.0f} to "
                f"{row0['deaths_p95']:,.0f}). Waiting until {ref_label}: about **{rowr['deaths_med']:,.0f}** "
                f"({ratio:.1f} times as many)."
            )
        else:
            st.write(f"Starting on day 0 prevents almost all deaths; waiting until {ref_label} gives about "
                     f"**{rowr['deaths_med']:,.0f}** deaths.")
        extra = rowr["deaths_med"] - row0["deaths_med"]
        if slow:
            st.write(f"That is about **{extra / (ref_delay / 365.25):,.0f} extra deaths per year of delay** in the first three years.")
        else:
            st.write(f"That is about **{extra / (ref_delay / 7):,.0f} extra deaths per week of delay** over the first four weeks.")

        gfig2 = go.Figure()
        gfig2.add_trace(go.Scatter(x=xs, y=sm["p_overwhelm"] * 100, name="Chance hospitals overwhelmed (%)"))
        gfig2.add_hline(y=target_c * 100, line_dash="dot", annotation_text="Your acceptable risk")
        gfig2.update_layout(xaxis_title=xl, yaxis_title="Chance (%)", title="The decision window")
        st.plotly_chart(gfig2)
        safe = []
        for _, rw in sm.iterrows():
            if rw["p_overwhelm"] <= target_c:
                safe.append(rw["delay"])
            else:
                break
        if len(safe) == len(sm):
            st.success("Every tested start day keeps the chance of overwhelmed hospitals within your acceptable risk.")
        elif safe:
            st.success(f"**Decision window:** to keep the chance of overwhelmed hospitals at or below {target_c:.0%}, "
                       f"start no later than about **{when(max(safe))}** (grid spacing is coarse, so treat this as approximate).")
        else:
            st.error("Even starting immediately does not meet your acceptable risk with this intervention alone. "
                     "Combine measures or raise the strength.")

        pfig = go.Figure()
        band(pfig, xs, sm["peak_p5"], sm["peak_med"], sm["peak_p95"], "Peak hospital demand")
        pfig.add_hline(y=cres["capacity"], line_color="red", annotation_text="Hospital capacity")
        pfig.update_layout(xaxis_title=xl, yaxis_title="Peak number needing hospital care")
        st.plotly_chart(pfig)

        wl = None if slow else weekly_loss(sm, bl["inf_med"])
        if wl is not None:
            msg = (f"**Model:** each extra week of delay in the first three weeks loses about **{wl:.0%}** of the infections "
                   "that action could have prevented.")
            if disease == "Measles" and lever == "campaign":
                msg += (" **Published (MSF measles guidelines):** each week of delay reduces cases prevented by roughly 2% to 5%. "
                        "The model loses more per week because it is a fast, fully mixed outbreak. Real outbreaks spread "
                        "through clusters, and campaigns are often not the main driver of the early curve.")
            st.write(msg)

        with st.expander("Show the numbers"):
            show = sm.copy()
            show["delay"] = show["delay"].astype(int)
            show = show.rename(columns={
                "delay": "Start day", "deaths_p5": "Deaths (5th)", "deaths_med": "Deaths (median)", "deaths_p95": "Deaths (95th)",
                "inf_med": "Infected (median)", "peak_p5": "Peak demand (5th)", "peak_med": "Peak demand (median)",
                "peak_p95": "Peak demand (95th)", "p_overwhelm": "Chance overwhelmed",
            }).round(2)
            st.dataframe(show, hide_index=True)

    st.markdown("### What published studies found")
    items = list(EVIDENCE.get(disease, []))
    if not any("Hatchett" in it["cite"] for it in items):
        items += EVIDENCE["General"]
    for it in items:
        st.markdown(f"**{it['cite']}**")
        st.markdown(f"- {it['finding']}")
        st.markdown(f"- Link: {it['link']}")
    st.caption(CAVEAT)
    glossary()

# ------------------------------------------------------------------
# TAB 5: ALL DISEASES AT A GLANCE
# ------------------------------------------------------------------
with tab5:
    st.subheader("All diseases at a glance: peak ranges and what drives the risk")
    st.write(
        "Runs every catalogue disease with its own typical values and plausible ranges, so you can compare peak size and timing, "
        "and see which uncertain fact matters most for each one. Your sidebar settings do not change this tab."
    )
    scen_key = st.radio("Scenario", list(SCENARIOS), format_func=lambda x: SCENARIOS[x], horizontal=True, key="all_scen")
    if st.button("Run all diseases", type="primary"):
        with st.spinner("Simulating five diseases..."):
            st.session_state["all"] = (scen_key, run_all(scen_key, 60))
    allres = st.session_state.get("all")
    if allres is None:
        st.info("Press the button. It takes around 15 to 30 seconds.")
    else:
        if allres[0] != scen_key:
            st.warning("These results are for the other scenario. Press the button to update them.")
        results = allres[1]
        trows, plot = [], []
        for name, rr in results.items():
            dfa, Na, ua = rr["df"], rr["N"], rr["unit"]
            esta = dfa[dfa["established"] == 1]
            if len(esta) >= 5:
                tdays = esta["peak_day"] / (365.25 if ua > 1 else 1)
                tcell = f"{np.median(tdays):,.1f} yrs ({np.percentile(tdays, 5):,.1f} to {np.percentile(tdays, 95):,.1f})" if ua > 1 else \
                    f"day {np.median(tdays):,.0f} ({np.percentile(tdays, 5):,.0f} to {np.percentile(tdays, 95):,.0f})"
                share = esta["peak_inf"] / Na * 100
                scell = f"{np.median(share):.1f}% ({np.percentile(share, 5):.1f} to {np.percentile(share, 95):.1f})"
                plot.append((name, np.percentile(share, [5, 50, 95]), np.percentile(esta["peak_day"], [5, 50, 95])))
            else:
                tcell, scell = "No epidemic peak", "Dies out"
            hd = dfa["peak_demand"] / Na * 100_000
            trows.append({
                "Disease": name,
                "Chance of taking off": f"{dfa['p_takeoff'].mean():.0%}",
                "Futures with an epidemic": f"{len(esta) / len(dfa):.0%}",
                "Time of peak: median (5th to 95th)": tcell,
                "Peak share infectious: median (5th to 95th)": scell,
                "Peak hospital demand per 100,000": f"{np.median(hd):,.0f} ({np.percentile(hd, 5):,.0f} to {np.percentile(hd, 95):,.0f})",
                "Chance hospitals overwhelmed": f"{dfa['overwhelmed'].mean():.0%}",
                "Deaths per 100,000 (median)": f"{np.median(dfa['deaths'] / Na * 100_000):,.0f}",
            })
        st.dataframe(pd.DataFrame(trows), hide_index=True)
        st.caption("HIV runs over decades with fewer simulations, and every disease uses 60 futures, so ranges are rough.")

        if plot:
            names = [p[0].split(" (")[0] for p in plot]
            med_s = np.array([p[1][1] for p in plot])
            lo_s = np.array([p[1][0] for p in plot])
            hi_s = np.array([p[1][2] for p in plot])
            f1 = go.Figure(go.Scatter(x=names, y=med_s, mode="markers", name="Median",
                                      error_y=dict(type="data", symmetric=False, array=hi_s - med_s, arrayminus=med_s - lo_s)))
            f1.update_layout(yaxis_title="Peak share of population infectious (%)", title="Peak size, 5th to 95th percentile")
            f1.update_yaxes(type="log")
            st.plotly_chart(f1)
            med_t = np.array([p[2][1] for p in plot])
            lo_t = np.array([p[2][0] for p in plot])
            hi_t = np.array([p[2][2] for p in plot])
            f2 = go.Figure(go.Scatter(x=names, y=med_t, mode="markers", name="Median",
                                      error_y=dict(type="data", symmetric=False, array=hi_t - med_t, arrayminus=med_t - lo_t)))
            f2.update_layout(yaxis_title="Days until peak infections", title="Time of peak, 5th to 95th percentile")
            f2.update_yaxes(type="log")
            st.plotly_chart(f2)

        st.markdown("### Which uncertain fact drives the risk, for each disease?")
        outcomes_all = {"Peak hospital demand": "peak_demand", "Deaths": "deaths", "Total infected": "total_infected"}
        out_all = st.selectbox("Outcome to explain", list(outcomes_all), key="sens_outcome_all")
        params = list(UNCERTAIN)
        z = [[sensitivity(rr["df"], outcomes_all[out_all], params)[p] for p in params] for rr in results.values()]
        hm = go.Figure(go.Heatmap(
            z=z, x=[UNCERTAIN[p] for p in params], y=[n.split(" (")[0] for n in results],
            zmin=-1, zmax=1, colorscale="RdBu", text=np.round(z, 2), texttemplate="%{text}",
        ))
        hm.update_layout(title=f"Rank correlation with {out_all.lower()} (darker = stronger driver)")
        st.plotly_chart(hm)
        top_rows = []
        for (name, rr), zr in zip(results.items(), z):
            j = int(np.argmax(np.abs(zr)))
            top_rows.append({"Disease": name, "Biggest driver": UNCERTAIN[params[j]] if abs(zr[j]) >= 0.15 else "None dominates",
                             "Correlation": round(zr[j], 2)})
        st.dataframe(pd.DataFrame(top_rows), hide_index=True)
        st.caption("Collect data on the biggest driver first. Route of transmission only matters in the moderate-measures scenario, "
                   "because with no measures there is nothing for it to change.")
    glossary()

# ------------------------------------------------------------------
# TAB 6: MODEL VS REAL WORLD
# ------------------------------------------------------------------
with tab6:
    st.subheader("Model versus real outbreaks")
    st.write(
        "One click compares the model with a documented real-world outbreak for each of the five catalogue diseases. "
        "Where the model is wrong, that is information: the explanations show which assumptions to improve."
    )
    if st.button("Compare model with real outbreaks (all five diseases)", type="primary"):
        with st.spinner("Running the five comparisons..."):
            st.session_state["bm_all"] = run_all_bm(150)
    bmr = st.session_state.get("bm_all")
    if bmr is None:
        st.info("Press the button. It takes around 10 to 20 seconds.")
    else:
        summary = []
        for name, r in bmr.items():
            for row in r["rows"]:
                summary.append({"Disease": name.split(" (")[0], "Real outbreak": r["title"], "Measure": row["metric"],
                                "Observed": row["observed"], "Model": row["model"], "Verdict": row["verdict"]})
        sdf = pd.DataFrame(summary)
        inside = sdf["Verdict"].str.contains("Inside|Rare in the community|plausible", case=False).sum()
        st.write(f"**Summary:** {inside} of {len(sdf)} comparisons agree with the real outbreak. "
                 "Details, explanations and sources for each disease are below.")
        st.dataframe(sdf, hide_index=True)

        for name, r in bmr.items():
            bm = BENCHMARKS[name]
            with st.expander(f"{name}: {r['title']}", expanded=(name == disease)):
                st.write(bm["context"])
                st.table(pd.DataFrame(r["rows"]).rename(columns={"metric": "Measure", "observed": "Observed",
                                                                  "model": "Model", "verdict": "Verdict"}).set_index("Measure"))
                h = r.get("hist")
                if h is not None:
                    hf = go.Figure(go.Histogram(x=h["values"], name="Model"))
                    hf.add_vline(x=h["observed"], line_color="red", annotation_text="Observed")
                    hf.update_layout(xaxis_title=h["label"], yaxis_title="Simulated futures")
                    if h.get("log"):
                        hf.update_yaxes(type="log")
                    st.plotly_chart(hf)
                if r["kind"] == "simulation":
                    st.caption(f"Assumed share of real infections reported as cases: {r['reporting']:.0%}. "
                               f"Model attack rate (share of population infected): {r['attack']:.0%}.")
                st.markdown("**Why model and reality may differ**")
                for line in bm["differences"]:
                    st.markdown(f"- {line}")
                st.markdown("**Sources to check:**")
                for s in bm["sources"]:
                    st.markdown(f"- {s}")
                if r["verify"]:
                    st.caption(r["verify"])
    glossary()

# ------------------------------------------------------------------
# TAB 7: METHOD
# ------------------------------------------------------------------
with tab7:
    st.subheader("How it works")
    st.markdown(
        """
**Disease catalogue.** Each disease stores typical values for transmissibility, timing, severity, route of transmission
and behaviour, with ranges where published estimates disagree. Choosing one fills every slider. The latent period, route
effectiveness and vaccine effectiveness are marked ASSUMPTION where no source stands behind them.

**Learning from data.** Early cases grow like exp(r x time). We fit r by regression on log(cases), giving a doubling time and
uncertainty range. For an SEIR model, R0 = (1 + r x latent period) x (1 + r x infectious period). We validate by hiding the
latest days and checking the forecast.

**Simulation (SEIR).** People move Susceptible, Exposed, Infectious, Recovered. Realism features:
- *Contact inequality:* 20% of people have many more contacts and are infected first. R0 is kept equal to the slider by rescaling.
- *Behaviour change:* contacts fall as prevalence rises.
- *Route of transmission:* contact reduction only blocks the share of spread that distancing can stop (the route slider).
- *Delayed measures:* contact reduction and isolation start on a chosen day. An emergency vaccination campaign is delivered over a chosen number of days.
- *Latent and infectious periods* are sampled from ranges. Slow diseases such as HIV use weekly time steps.

**Chance of taking off.** A few cases can fizzle out by luck. A branching process with superspreading (k) gives the chance that
n cases cause a large outbreak: q = (1 + R(1 - q)/k)^(-k), chance = 1 - q^n.

**Risk assessment and peak ranges.** Uncertain parameters are sampled from triangular distributions across many simulations.
The headline risk is the share ending with hospitals overwhelmed, weighted by the chance of taking off. Peak timing and size
are reported as the median and the 5th to 95th percentile range across futures that develop a real epidemic.

**Sensitivity.** The rank correlation between each uncertain fact and an outcome shows which fact drives the result. Route of
transmission is included, because uncertainty about it (as with early COVID-19 guidance) changes which measures work.

**Cost of waiting.** The same intervention is started on different days across the same set of plausible futures, so
differences come from the delay and not from luck. The decision window is the latest start day that keeps the chance of
overwhelmed hospitals within your acceptable risk. Published studies are listed beside the results.

**Hospital overload.** On days when hospital demand exceeds capacity, the death rate is multiplied by 1.13 by default."""
    )
    st.markdown(f"- Source: {OVERLOAD_STUDY['cite']} ({OVERLOAD_STUDY['link']})")
    st.markdown(f"- What it found: {OVERLOAD_STUDY['finding']}")
    st.markdown("- Caveats:")
    for cv in OVERLOAD_STUDY["caveats"]:
        st.markdown(f"  - {cv}")
    st.markdown(f"- Supporting review: {OVERLOAD_STUDY['support']}")
    st.markdown(
        """
**Real-world comparison.** The model is run on documented outbreaks and compared with what happened. Differences are expected
and are explained rather than hidden.

**Limitations.** Two contact groups only, no age structure, no geography, no seasonality, no treatment (so HIV is a rough
illustration). Parameters are approximate. Outputs support comparing options, not exact prediction.
"""
    )
    glossary()
