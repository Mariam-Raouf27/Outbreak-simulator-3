"""
evidence.py : published studies on the cost of waiting, the hospital-strain multiplier, and the glossary.

Each finding is a paraphrase of what the source reports. Check the original before you quote a number.
"""

# ------------------------------------------------------------------
# Hospital strain multiplier (1.13)
# ------------------------------------------------------------------
OVERLOAD_STUDY = {
    "cite": "Role of hospital strain in determining outcomes for people hospitalised with COVID-19 in England. "
            "Emergency Medicine Journal (2023), doi 10.1136/emermed-2023-213329",
    "finding": "Among people hospitalised with COVID-19 in England in winter 2020/21, in-hospital mortality was 23.6% in the "
               "lowest quartile of bed strain and 25.3% in the highest. After adjustment the odds ratio was 1.13 "
               "(95% CI 1.09 to 1.17). The authors call the effect relatively modest.",
    "caveats": [
        "1.13 is an odds ratio for the highest versus the lowest quartile of bed strain, not a measured jump at the "
        "moment demand passes capacity.",
        "An odds ratio is not exactly a risk multiplier. The raw death rates above differ by a factor of about 1.07.",
        "The study covered COVID-19 hospital patients in England, so applying it to other diseases and to people who "
        "never reach hospital is an extrapolation.",
        "Other work finds larger effects at the extreme: a US CDC analysis linked ICU use above 100% of capacity with many "
        "excess deaths two weeks later. Use the slider to test a higher multiplier.",
    ],
    "link": "https://doi.org/10.1136/emermed-2023-213329",
    "support": "Eriksson et al. (2017), The association between hospital capacity strain and inpatient outcomes in highly "
               "developed countries: a systematic review, J Gen Intern Med. Mortality rose during strain in 18 of 30 studies.",
}


# ------------------------------------------------------------------
# Cost-of-waiting studies
# ------------------------------------------------------------------
EVIDENCE = {
    "General": [
        {
            "cite": "Hatchett RJ, Mecher CE, Lipsitch M (2007). Public health interventions and epidemic intensity during the "
                    "1918 influenza pandemic. PNAS 104(18):7582-7587.",
            "finding": "US cities that applied several interventions early had peak death rates about 50% lower than cities "
                       "that did not. Philadelphia acted more than two weeks after its first cases and peaked at 257 excess "
                       "deaths per 100,000 in a week. St. Louis acted within about two days and peaked at 31 per 100,000, "
                       "about one eighth.",
            "link": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1849867",
        },
    ],
    "COVID-19 (original strain, no vaccine)": [
        {
            "cite": "Pei S, Kandula S, Shaman J (2020). Differential effects of intervention timing on COVID-19 spread in the "
                    "United States. Science Advances.",
            "finding": "A county-level model of the US found that if the same distancing measures had begun one week earlier "
                       "(8 March instead of mid-March), about 601,667 fewer cases and 32,335 fewer deaths would have occurred "
                       "by 3 May 2020. Two weeks earlier: about 1,041,261 fewer cases and 59,351 fewer deaths.",
            "link": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7821895",
        },
        {
            "cite": "Hatchett RJ, Mecher CE, Lipsitch M (2007), PNAS (1918 influenza, respiratory disease).",
            "finding": "Early action roughly halved peak death rates in 1918. Useful as a historical comparison for a respiratory "
                       "pandemic.",
            "link": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1849867",
        },
    ],
    "Measles": [
        {
            "cite": "MSF Medical Guidelines, Measles: the impact of outbreak response timing.",
            "finding": "Experience and analyses indicate that each additional week of delay in outbreak response vaccination "
                       "reduces the number of cases prevented by roughly 2% to 5%, and responses after the peak prevent less.",
            "link": "https://medicalguidelines.msf.org/en/node/2202",
        },
        {
            "cite": "Time is of the essence: exploring a measles outbreak response vaccination in Niamey, Niger (MSF Science Portal).",
            "finding": "A campaign that vaccinated about 57% of children aged 6 to 59 months, 23 weeks after the epidemic began, "
                       "averted a median of about 7.6% of cases. Responding within about 60 days and widening the age range "
                       "could have cut cases by up to 90%.",
            "link": "https://scienceportal.msf.org/assets/4099",
        },
        {
            "cite": "Marinovic AB, Swaan C, Wichmann O, et al. (2012). Effectiveness and timing of vaccination during school "
                    "measles outbreak. Emerging Infectious Diseases, Sept 2012.",
            "finding": "In a modelled German school outbreak, reacting within about 6 to 24 days (depending on the baseline "
                       "vaccination level) avoided large outbreaks, and reacting within 40 to 50 days still reduced outbreak size.",
            "link": "https://stacks.cdc.gov/view/cdc/18646",
        },
    ],
    "Polio": [
        {
            "cite": "Evaluation of response scenarios to potential polio outbreaks using mathematical models. Risk Analysis "
                    "2006;26(6):1541-56 (PubMed 17184396).",
            "finding": "Delay in response was found to be a crucial risk factor for large polio outbreaks, and the study "
                       "describes the trade-off between responding sooner and achieving better coverage.",
            "link": "https://pubmed.ncbi.nlm.nih.gov/17184396/",
        },
        {
            "cite": "Serotype 2 oral poliovirus vaccine (OPV2) choices and the consequences of delaying outbreak response. "
                    "Vaccine supplement (PMC11027208).",
            "finding": "Modelling delaying type 2 vaccine-derived polio outbreak response for six months (January to June 2021) "
                       "to wait for a new vaccine suggested as many as about 1,300 extra cases in the African region over "
                       "2021 to 2023.",
            "link": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11027208",
        },
    ],
    "MERS": [
        {
            "cite": "Korea Centers for Disease Control and Prevention (2015), epidemiological report in Osong Public Health and "
                    "Research Perspectives, as reported by The Korea Herald.",
            "finding": "Five super-spreaders passed the virus to 153 of the first 184 patients. At the first diagnosis only three "
                       "contacts were isolated, rising to 64 the next day and 120 after the fifth patient was diagnosed. People "
                       "not isolated soon enough infected others in other hospitals.",
            "link": "https://heraldk.com/en/?p=52263",
        },
        {
            "cite": "Current epidemiological situation of MERS-CoV clusters and implications for public health response in South "
                    "Korea. J Korean Med Assoc 2015;58(6):487-497, doi 10.5124/jkma.2015.58.6.487.",
            "finding": "Names the initial failure to confirm the diagnosis promptly and to isolate the index case, and "
                       "inadequate early contact categorisation, as key factors in the amplified spread.",
            "link": "https://search.bvsalud.org/gim/resource/en/wpr-19416",
        },
    ],
    "HIV (untreated)": [
        {
            "cite": "INSIGHT START Study Group (2015). Initiation of antiretroviral therapy in early asymptomatic HIV infection. "
                    "N Engl J Med, doi 10.1056/NEJMoa1506816.",
            "finding": "In 4,685 people with high CD4 counts, starting treatment immediately rather than deferring it cut the "
                       "risk of serious AIDS events, serious non-AIDS events or death by 57% (42 versus 96 events; hazard ratio "
                       "0.43). Serious AIDS events fell by 72%. This measures harm to the individual from delaying treatment, "
                       "not spread through the population.",
            "link": "https://natap.org/2015/IAS/IAS_84.htm",
        },
    ],
}

EVIDENCE["Custom (new disease)"] = EVIDENCE["General"]

CAVEAT = (
    "These studies cover different diseases, settings and measures from this model, so treat them as supporting evidence for "
    "the direction and rough size of the cost of delay, not as a test of this tool's exact numbers."
)


# ------------------------------------------------------------------
# Glossary
# ------------------------------------------------------------------
GLOSSARY = {
    "R0 (basic reproduction number)": "The average number of people one case infects in a population with no immunity and no measures.",
    "Rt or effective R": "The same idea at a given moment, after immunity, vaccination and measures. Below 1 the outbreak shrinks.",
    "Latent period": "Time from catching the disease until you can pass it on. You are infected but not yet infectious.",
    "Incubation period": "Time from infection until symptoms start. If it is longer than the latent period, people spread the disease "
                         "before they feel ill.",
    "Infectious period": "How long a person can pass the disease on.",
    "Pre-symptomatic spread": "Transmission from people who have not yet developed symptoms. Isolating symptomatic cases cannot stop it.",
    "SEIR model": "A model that sorts people into Susceptible, Exposed (latent), Infectious and Recovered groups and tracks how many are in each.",
    "Susceptible": "People who can still catch the disease.",
    "Doubling time": "How long it takes for cases to double during early growth. A short doubling time means little time to act.",
    "Exponential growth": "Growth by a fixed percentage each day, so numbers double again and again. Early outbreaks grow this way.",
    "Herd immunity threshold": "The share of people who must be immune to stop sustained spread: 1 minus 1 divided by R0.",
    "Superspreading (k)": "When a few cases cause most infections. A low k means very uneven spread, so many outbreaks fizzle out "
                          "but a few explode.",
    "Takeoff probability": "The chance that introduced cases start a large outbreak rather than dying out by luck.",
    "Branching process": "A model where each case infects a random number of others. Used to find the chance an outbreak dies out.",
    "Monte Carlo simulation": "Running the model many times with values drawn from plausible ranges, to see the spread of possible futures.",
    "Triangular distribution": "A simple way to sample uncertain values: they cluster around a most likely value and stay between a low and a high.",
    "Sensitivity analysis": "Checking which uncertain fact changes the result most. The biggest driver is the best place to collect better data.",
    "Rank (Spearman) correlation": "A measure from -1 to +1 of how consistently an outcome rises or falls with an input. Near 0 means little effect.",
    "Percentile range (5th to 95th)": "The span that contains the middle 90% of simulated outcomes.",
    "Contact reduction": "Measures that cut how many people meet, such as distancing or closures. For HIV it means fewer risky partnerships "
                         "or condom use.",
    "Route of transmission": "How the disease spreads (airborne, droplets, contaminated water, sexual contact). It decides how well "
                             "distancing works. COVID-19 showed how uncertainty about the route can delay the right measures.",
    "Case isolation": "Keeping people who show symptoms away from others. It only blocks spread that happens after symptoms start.",
    "Emergency vaccination campaign": "Vaccinating many people quickly after an outbreak is detected. Here it is delivered over a set "
                                      "number of days.",
    "Vaccine effectiveness": "The share of vaccinated people who are actually protected.",
    "Hospital capacity": "The number of beds available for this disease. Demand above it means hospitals are overwhelmed.",
    "Overload multiplier": "How much the death rate rises on days when hospital demand exceeds capacity. Set to 1.13 from an English "
                           "COVID-19 study (an odds ratio, so an approximation).",
    "Odds ratio": "A way of comparing the odds of an outcome between two groups. Close to a risk ratio when the outcome is rare, "
                  "less so when it is common.",
    "Latent versus incubation": "Latent period relates to when you become infectious, incubation to when you feel ill. They are often different.",
    "Cost of waiting (cost of delay)": "How much worse the outcome gets for each day or week that action is postponed.",
    "Decision window": "The latest start day at which measures still keep the chance of overwhelmed hospitals below your acceptable risk.",
    "Case fatality vs infection fatality": "Deaths per diagnosed case versus deaths per infection. The first is higher because mild "
                                           "infections go undiagnosed. This tool uses deaths per infection.",
    "Backtest": "Testing a forecast by hiding the latest data and checking whether the forecast would have predicted it.",
    "Prediction interval": "The range in which a future value is expected to fall, allowing for both uncertainty and randomness.",
    "Reporting fraction": "The share of real infections that appear in official case counts.",
    "Prevalence": "The share of the population that has the disease at a given time.",
    "Attack rate": "The share of the population infected over the whole outbreak.",
    "Waning immunity": "Protection that fades over time so people can be infected again.",
    "Contact inequality": "Some people have many more contacts than others. They are infected first, which slows the epidemic later.",
    "ART (antiretroviral therapy)": "Treatment for HIV that controls the virus and sharply lowers illness, death and onward spread.",
}
