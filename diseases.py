"""
diseases.py : the disease catalogue and real-world benchmarks (version 3).

IMPORTANT: every number here is an approximate, rounded value. Ranges reflect real disagreement
between studies and settings. Values marked ASSUMPTION have no direct published source behind them:
replace or justify them before presenting. Check each value against the sources listed and cite them.
"""

# levers: which interventions make sense for the disease
#   contact = distancing-type measures, isolation = isolating symptomatic cases, campaign = emergency vaccination
CATALOGUE = {
    "Custom (new disease)": {
        "summary": "Start from generic settings and describe your own unknown disease.",
        "fit": "n/a", "fit_note": "",
        "route": "Unknown (this is itself an uncertain fact for a new disease)",
        "r0": (2.0, 4.0), "latent": (1.0, 5.0), "incubation": "5 days", "infectious": (3.0, 7.0),
        "presym": 0.3, "k": 0.5, "death": (0.2, 1.0), "hosp": (2.0, 8.0), "disab": 0.3,
        "het": 4, "resp": 0.3, "waning": 0, "sim_days": 180, "unit": 1, "N": 100_000, "I0": 3,
        "measure_eff": (0.5, 1.0), "vax_eff": 0.7, "levers": ["contact", "isolation", "campaign"],
        "notes": ["Generic placeholder values, not a real disease."],
        "sources": [],
    },
    "Measles": {
        "summary": "Airborne virus, one of the most contagious known. Severe complications include "
                   "pneumonia and encephalitis (brain inflammation) that can cause permanent damage.",
        "fit": "Good", "fit_note": "Well suited: acute, immunising, spreads person to person.",
        "route": "Airborne (can hang in the air for a long time, so distancing alone blocks little)",
        "r0": (12.0, 18.0), "latent": (8.0, 12.0), "incubation": "about 10 to 14 days", "infectious": (6.0, 10.0),
        "presym": 0.5, "k": 1.0, "death": (0.05, 0.3), "hosp": (10.0, 25.0), "disab": 0.05,
        "het": 3, "resp": 0.0, "waning": 0, "sim_days": 150, "unit": 1, "N": 100_000, "I0": 5,
        "measure_eff": (0.4, 0.8), "vax_eff": 0.93, "levers": ["campaign", "isolation", "contact"],
        "notes": [
            "Infectious about 4 days before the rash, so roughly half of spread is pre-symptomatic.",
            "Death rate shown is for high-income settings; it is much higher with malnutrition or poor care.",
            "k (superspreading), latent range, route effectiveness and vaccine effectiveness are ASSUMPTIONS to source.",
        ],
        "sources": [
            "Guerra et al. (2017), The basic reproduction number (R0) of measles: a systematic review, Lancet Infectious Diseases",
            "WHO measles fact sheet",
            "UKHSA and CDC Pink Book measles chapters (complications and severity)",
        ],
    },
    "Polio": {
        "summary": "Poliovirus spreads mainly through contaminated water and faeces. Most infections "
                   "cause no symptoms, but a small share cause permanent paralysis, and some of those are fatal.",
        "fit": "Moderate", "fit_note": "Most infections are silent, and sanitation changes spread. The model "
                                        "has no sanitation pathway.",
        "route": "Faecal-oral (contaminated water and hands): distancing alone blocks little, sanitation and vaccination matter",
        "r0": (4.0, 7.0), "latent": (2.0, 5.0), "incubation": "about 7 to 14 days", "infectious": (14.0, 28.0),
        "presym": 0.95, "k": 1.0, "death": (0.01, 0.1), "hosp": (0.2, 2.0), "disab": 0.5,
        "het": 3, "resp": 0.0, "waning": 0, "sim_days": 240, "unit": 1, "N": 100_000, "I0": 5,
        "measure_eff": (0.3, 0.7), "vax_eff": 0.9, "levers": ["campaign", "isolation", "contact"],
        "notes": [
            "Disability value (0.5%, about 1 in 200) is the commonly quoted figure for type 1. Type 2 is nearer 1 in 1,900 "
            "(see the real-world comparison tab).",
            "Share of spread 'before or without symptoms' is set very high because most infections are "
            "asymptomatic, so isolating symptomatic cases barely helps. Vaccination is the key tool.",
            "Latent range, route effectiveness and vaccine effectiveness are ASSUMPTIONS to source.",
        ],
        "sources": [
            "WHO poliomyelitis fact sheet",
            "CDC Pink Book, poliomyelitis chapter",
            "Nathanson & Kew (2010), From emergence to eradication: the epidemiology of poliomyelitis deconstructed, Am J Epidemiol",
        ],
    },
    "COVID-19 (original strain, no vaccine)": {
        "summary": "Respiratory coronavirus. Spreads before symptoms appear, with strong clustering "
                   "(superspreading). Severity rises steeply with age. Some survivors have long-lasting symptoms.",
        "fit": "Good", "fit_note": "Well suited for the early pandemic. Later variants, vaccines and prior "
                                    "infection changed R0 and severity, and the model has no age structure.",
        "route": "Respiratory: droplets and airborne aerosols. Early guidance stressed droplets, which understated "
                 "the airborne share, so route effectiveness is a key uncertainty",
        "r0": (2.0, 3.5), "latent": (2.0, 4.0), "incubation": "about 5 days", "infectious": (5.0, 9.0),
        "presym": 0.5, "k": 0.3, "death": (0.4, 1.0), "hosp": (2.0, 6.0), "disab": 1.0,
        "het": 4, "resp": 0.3, "waning": 365, "sim_days": 240, "unit": 1, "N": 100_000, "I0": 10,
        "measure_eff": (0.5, 1.0), "vax_eff": 0.7, "levers": ["contact", "isolation", "campaign"],
        "notes": [
            "Death rate is an average over all ages in an unvaccinated high-income population.",
            "Permanent-disability value (long COVID) is a placeholder: published estimates vary hugely.",
            "About half of spread happens before symptoms or without them.",
            "Latent range, route effectiveness and vaccine effectiveness are ASSUMPTIONS to source.",
        ],
        "sources": [
            "Li et al. (2020), Early transmission dynamics in Wuhan, NEJM",
            "Endo et al. (2020), Estimating the overdispersion in COVID-19 transmission, Wellcome Open Research",
            "Levin et al. (2020), Assessing the age specificity of infection fatality rates for COVID-19, Eur J Epidemiol",
            "Ganyani et al. (2020), Estimating the generation interval for COVID-19, Eurosurveillance",
        ],
    },
    "MERS": {
        "summary": "Middle East respiratory syndrome coronavirus. Very severe but, so far, poorly "
                   "transmissible between people outside healthcare settings. Camels are the main reservoir.",
        "fit": "Limited", "fit_note": "R below 1 means it cannot sustain a population-wide wave. Real outbreaks "
                                      "are small hospital clusters driven by superspreading. Use the cluster "
                                      "comparison in the 'Model vs real world' tab.",
        "route": "Respiratory, mostly close contact in healthcare settings; aerosol spread in hospitals has been suggested",
        "r0": (0.4, 0.9), "latent": (2.0, 6.0), "incubation": "about 5 days (2 to 14)", "infectious": (5.0, 10.0),
        "presym": 0.2, "k": 0.25, "death": (20.0, 40.0), "hosp": (50.0, 90.0), "disab": 1.0,
        "het": 4, "resp": 0.0, "waning": 0, "sim_days": 180, "unit": 1, "N": 100_000, "I0": 1,
        "measure_eff": (0.5, 1.0), "vax_eff": 0.7, "levers": ["isolation", "contact"],
        "notes": [
            "R is below 1 in the community, so the model predicts outbreaks fizzle out, as seen in reality.",
            "Hospital outbreaks can have R above 1, which is why large clusters happened (e.g. South Korea 2015).",
            "No licensed vaccine, so no vaccination lever is offered.",
            "Permanent-disability value, latent range and route effectiveness are ASSUMPTIONS with little evidence behind them.",
        ],
        "sources": [
            "WHO MERS-CoV fact sheet",
            "Cauchemez et al. (2014), MERS-CoV: quantification of the extent of the epidemic, surveillance biases, and transmissibility, Lancet Infectious Diseases",
            "Kucharski & Althaus (2015), The role of superspreading in MERS-CoV transmission, Eurosurveillance",
        ],
    },
    "HIV (untreated)": {
        "summary": "Spreads through sexual contact, blood and from mother to child. Infected people stay "
                   "infectious for years, the infection is lifelong, and without treatment it usually leads to AIDS and death.",
        "fit": "Poor", "fit_note": "HIV epidemics unfold over decades through sexual networks, and treatment "
                                   "(ART) transforms outcomes. This model runs in weekly steps over 30 years as a "
                                   "rough illustration only.",
        "route": "Sexual contact, blood and mother-to-child: 'contact reduction' here means fewer risky partnerships or "
                 "condom use, not distancing",
        "r0": (1.5, 4.0), "latent": (7.0, 21.0), "incubation": "weeks to seroconvert; about 10 years to AIDS untreated",
        "infectious": (2000.0, 3650.0),
        "presym": 0.95, "k": 0.3, "death": (70.0, 90.0), "hosp": (1.0, 3.0), "disab": 100.0,
        "het": 8, "resp": 0.0, "waning": 0, "sim_days": 10950, "unit": 7, "N": 100_000, "I0": 20,
        "measure_eff": (0.6, 1.0), "vax_eff": 0.5, "levers": ["contact", "isolation"],
        "notes": [
            "Death rate is for the untreated natural history. With effective treatment it falls to a small share.",
            "'Permanent' is set to 100% because infection is lifelong, even though treated life expectancy is near normal.",
            "Strong contact inequality (het) reflects concentrated sexual networks.",
            "Time is simulated in weekly steps so 30 years is feasible. No licensed vaccine, so no vaccination lever.",
            "Latent range and route effectiveness are ASSUMPTIONS to source.",
        ],
        "sources": [
            "UNAIDS global HIV statistics fact sheet (latest edition)",
            "WHO HIV fact sheet",
            "Anderson & May (1991), Infectious Diseases of Humans",
        ],
    },
}


# ------------------------------------------------------------------
# Real-world benchmarks. kind decides how model.run_benchmark compares:
#   simulation : run the model on the outbreak scenario, compare totals
#   cluster    : branching-process chains from one introduction (outbreaks that never become population waves)
#   severity   : check a catalogue severity value against the literature
#   prevalence : compare the speed and height of a long epidemic wave
# ------------------------------------------------------------------
BENCHMARKS = {
    "Measles": {
        "kind": "simulation",
        "title": "Samoa measles outbreak, 2019",
        "context": "Measles vaccine coverage in Samoa had fallen to roughly 31% in 2018. A large outbreak in "
                   "late 2019 caused about 5,700 reported cases and about 83 deaths, mostly in young children, "
                   "in a population of around 200,000. A mass vaccination campaign and a short national "
                   "shutdown followed.",
        "overrides": {"N": 200_000, "I0": 5, "coverage": 0.31, "efficacy": 0.93,
                      "campaign_day": 55, "campaign_coverage": 0.8, "campaign_ramp": 14,
                      "het": 3, "sim_days": 150},
        "reporting_default": 0.5,
        "observed": {"Reported cases": 5700, "Deaths": 83},
        "differences": [
            "Real mixing is far more clustered (households, schools, villages) than this model assumes.",
            "The campaign delivery period, timing and coverage are assumptions (campaign on day 55, 80% coverage, 14 days).",
            "No age structure: nearly all deaths were in very young children.",
            "The national shutdown is not modelled.",
        ],
        "sources": ["WHO and UNICEF reports on the 2019 Samoa measles outbreak", "Samoa Ministry of Health situation reports"],
        "verify": "Observed figures are from memory of published reports and were not re-checked in this version: verify them.",
    },
    "COVID-19 (original strain, no vaccine)": {
        "kind": "simulation",
        "title": "Diamond Princess cruise ship, February 2020",
        "context": "A closed population of 3,711 people. Around 700 became infected (about 19%) and 14 died "
                   "before and after cabin quarantine began. Transmission on the ship was far more intense "
                   "than in the community.",
        "overrides": {"N": 3711, "I0": 1, "coverage": 0.0, "contact_reduction": 0.7, "policy_day": 10,
                      "measure_eff": 1.0, "beds_per_100k": 100_000, "het": 3, "sim_days": 60,
                      "r0_range": (8.0, 15.0)},
        "reporting_default": 0.9,
        "observed": {"Reported cases": 712, "Deaths": 14},
        "differences": [
            "R0 on the ship is set to 8 to 15 (an estimate for close quarters), not the community value.",
            "Passengers were much older than the general population, so deaths are higher than an all-age death rate predicts.",
            "Quarantine timing and effectiveness are assumptions, not measured values.",
            "Crew and passengers mixed differently.",
        ],
        "sources": ["Mizumoto et al. (2020), Estimating the asymptomatic proportion of COVID-19 cases on board the Diamond Princess, Eurosurveillance",
                    "Russell et al. (2020), Estimating the infection and case fatality ratio for COVID-19 using age-adjusted data from the Diamond Princess, Eurosurveillance"],
        "verify": "Observed figures are from memory of published reports and were not re-checked in this version: verify them.",
    },
    "MERS": {
        "kind": "cluster",
        "title": "South Korea MERS outbreak, 2015",
        "context": "One traveller returning from the Middle East in May 2015 started a chain of hospital-based "
                   "infections. In total 186 people were infected and 38 died. Five 'super-spreading' patients "
                   "were linked to 153 of the first 184 cases (83%), according to the Korean CDC.",
        "hospital_R": (0.9, 1.3),
        "observed": {"cases": 186, "deaths": 38, "top5_share": 0.83},
        "differences": [
            "Community R is below 1, but transmission in crowded, poorly controlled hospitals was higher. "
            "The hospital-type R range (0.9 to 1.3) is an ASSUMPTION used to show the effect.",
            "The cluster model has no control measures, but Korea's tracing and quarantine shaped the final size.",
            "The first diagnosis was delayed, so few contacts were isolated early: delay is part of why it grew.",
        ],
        "sources": ["Korea Centers for Disease Control and Prevention (2015), report in Osong Public Health and Research Perspectives, as reported by The Korea Herald",
                    "J Korean Med Assoc (2015) 58(6):487-497, doi 10.5124/jkma.2015.58.6.487",
                    "Kucharski & Althaus (2015), Eurosurveillance"],
        "verify": "Case and death counts are as reported by Korean health authorities (186 cases, 38 deaths).",
    },
    "Polio": {
        "kind": "severity",
        "title": "Paralytic polio: United States (New York), 2022",
        "context": "In 2022 a vaccine-derived type 2 poliovirus caused one case of paralysis in an unvaccinated adult in "
                   "Rockland County, New York, and the virus was found in wastewater in neighbouring counties. "
                   "The CDC noted that about one in 1,900 type 2 infections in unvaccinated people is expected to cause "
                   "paralysis, and a 2024 CDC paper gave a range of 1 in 190 to 1 in 1,900 depending on poliovirus type.",
        "observed": {"ratio_low": 1 / 1900, "ratio_high": 1 / 190},
        "differences": [
            "This is not an outbreak replay: polio cannot be replayed from a fully susceptible start because most of the "
            "population was vaccinated. It tests the severity value used in the catalogue instead.",
            "The catalogue value (1 in 200) matches the type 1 end of the range. Type 2 outbreaks need a lower value.",
            "One paralytic case implies many hidden, silent infections, which is why wastewater testing matters.",
        ],
        "sources": ["CDC MMWR 2022;71(33): Public health response to a case of paralytic poliomyelitis in an unvaccinated person and detection of poliovirus in wastewater, New York, June-August 2022 (doi 10.15585/mmwr.mm7133e2)",
                    "Emerging Infectious Diseases 2024;30(11): wastewater testing for poliovirus after the 2022 New York case"],
        "verify": "Ratios are taken from the CDC sources listed.",
    },
    "HIV (untreated)": {
        "kind": "prevalence",
        "title": "Botswana adult HIV epidemic, 1990 to 2000",
        "context": "UNAIDS estimates put adult (15 to 49) HIV prevalence in Botswana at 5.7% in 1990, 20.5% in 1995 and a peak of "
                   "26.3% in 2000, before treatment programmes (from the early 2000s) brought it down slowly.",
        "observed": {"start": 0.057, "target": 0.205, "years_to_target": 5.0, "peak": 0.263, "years_to_peak": 10.0},
        "differences": [
            "The model's population is treated as one group; the real figures are for adults aged 15 to 49.",
            "Real spread was far faster than the catalogue R0 and infectious period imply: early HIV is highly infectious, "
            "and concurrent partnerships spread it quickly. This is the model's weakest comparison.",
            "No treatment, no behaviour change campaigns and no age structure.",
        ],
        "sources": ["UNAIDS estimates of adult HIV prevalence, Botswana (series as listed by the World Bank / IndexMundi)",
                    "Estimated HIV trends and program effects in Botswana, PLoS ONE 2008;3(11)"],
        "verify": "Prevalence figures are from the UNAIDS series quoted above.",
    },
}
