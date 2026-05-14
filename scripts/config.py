"""
Project-wide configuration constants.

Everything tunable in one place — change here, propagates everywhere.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SAMPLE_DIR = DATA_DIR / "sample"

# Make sure the data dirs exist when this module is imported
RAW_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

# ── CMS Data URLs ────────────────────────────────────────────────────────────
# These point at the 2022 reporting year for both datasets.
#
# CMS occasionally restructures their download endpoints. If a URL 404s,
# search "CMS Open Payments General Payments 2022 download" or "CMS Medicare
# Part D Prescribers by Provider 2022 download" — they're permanently public.

OPEN_PAYMENTS_URL = (
    "https://download.cms.gov/openpayments/PGYR2022_P01302025_01212025.zip"
)
# Discovered via CMS data.json catalog. Periodically re-resolve from
# https://data.cms.gov/data.json if URLs 404.
PART_D_PROVIDER_URL = (
    "https://data.cms.gov/sites/default/files/2025-11/"
    "429c776b-63ab-4976-8764-0b7f05db14bd/"
    "MUP_DPR_RY25_P04_V20_DY22_NPI.csv"
)
PART_D_PROVIDER_DRUG_URL = (
    "https://data.cms.gov/sites/default/files/2024-05/"
    "18f82097-61a6-4889-9941-9a0b6ad7523c/"
    "MUP_DPR_RY24_P04_V10_DY22_NPIBN.csv"
)

# ── Filtering Strategy ───────────────────────────────────────────────────────
# Target ~150MB total in Neon to leave headroom for future projects.

# Open Payments: keep only payments from these companies.
# Top 10 by 2022 spend — these alone account for ~60% of total industry
# physician spend and cover all therapeutic classes in our drug seed.
TRACKED_COMPANIES = [
    "ABBVIE",
    "PFIZER",
    "JOHNSON & JOHNSON",
    "MERCK",
    "BRISTOL-MYERS SQUIBB",
    "ELI LILLY",
    "NOVO NORDISK",
    "ASTRAZENECA",
    "NOVARTIS",
    "AMGEN",
]

# Minimum payment to load. Drops the vast majority of $5-$20 individual
# meal records (which are 70%+ of all Open Payments rows) while keeping
# all consulting, speaking, travel, research, and meaningful meal events.
# A "meaningful" meal payment in the pharma industry is typically $20+
# (i.e., a real meeting meal, not a passing coffee).
MIN_PAYMENT_USD = 50.0

# Part D by Drug: only load rows for drugs in our curated mapping
# (drug_company_seed.csv in dbt seeds). This list is the brand names from
# that seed file — keep in sync.
TRACKED_DRUGS = [
    # AbbVie
    "Humira",
    "Skyrizi",
    "Rinvoq",
    "Imbruvica",
    "Venclexta",
    # BMS
    "Eliquis",
    "Opdivo",
    "Revlimid",
    "Pomalyst",
    # Merck
    "Keytruda",
    "Januvia",
    "Janumet",
    # Lilly
    "Trulicity",
    "Mounjaro",
    "Verzenio",
    "Taltz",
    # Novo Nordisk
    "Ozempic",
    "Wegovy",
    "Rybelsus",
    "Victoza",
    "Tresiba",
    # Pfizer
    "Ibrance",
    "Xeljanz",
    "Vyndamax",
    "Lipitor",
    # J&J
    "Stelara",
    "Tremfya",
    "Xarelto",
    "Invokana",
    "Darzalex",
    # AstraZeneca
    "Tagrisso",
    "Farxiga",
    "Brilinta",
    "Symbicort",
    "Lynparza",
    # Novartis
    "Entresto",
    "Cosentyx",
    "Kisqali",
    "Gilenya",
    # Sanofi
    "Lantus",
    "Dupixent",
    "Toujeo",
    # GSK
    "Trelegy Ellipta",
    "Nucala",
    # Gilead
    "Biktarvy",
    "Yescarta",
    # Amgen
    "Enbrel",
    "Repatha",
    "Otezla",
    "Prolia",
    # Boehringer Ingelheim
    "Jardiance",
    "Trajenta",
    "Spiriva",
    # Takeda
    "Entyvio",
    # Regeneron
    "Eylea",
    "Praluent",
    # Biogen
    "Tecfidera",
    "Spinraza",
    # Vertex
    "Trikafta",
    # Moderna
    "Spikevax",
]

# Specialty filter for Part D Prescribers (top prescribing specialties)
TRACKED_SPECIALTIES = [
    "Cardiology",
    "Oncology",
    "Hematology / Oncology",
    "Endocrinology",
    "Rheumatology",
    "Gastroenterology",
    "Neurology",
    "Psychiatry",
    "Dermatology",
    "Pulmonology",
    "Nephrology",
    "Urology",
    "Infectious Disease",
    "Family Medicine",
    "Internal Medicine",
    "General Practice",
    "Nurse Practitioner",
    "Physician Assistant",
]

# Minimum activity threshold — drop tiny prescribers (lots of noise, no signal)
MIN_TOTAL_CLAIMS = 10
