import os

# Load .env file if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Server ────────────────────────────────────────────────────────────────
PORT = int(os.getenv("SNM_PORT", "3005"))

# ── Database ──────────────────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "supplynetwork.db")

# ── AgNet (Vendor / Supplier Network) ────────────────────────────────────
AGNET_BASE_URL = os.getenv(
    "AGNET_BASE_URL",
    "http://146.190.243.241:8303/api/v1",
)
AGNET_API_KEY = os.getenv(
    "AGNET_API_KEY",
    "HIvnNIkD0leWhchFENJDPuW2Y_K2B-LTHeas79pqfkbVQVan",
)

# ── CIS (Central Inventory System) ───────────────────────────────────────
CIS_BASE_URL = os.getenv(
    "CIS_BASE_URL",
    "http://138.197.144.135:8203/api/v1",
)
CIS_API_KEY = os.getenv(
    "CIS_API_KEY",
    "cAcMVCjdHbUTDeWk1gK3Toc6P7rG9Oy8wZ4vx1I41hxM4EbT",
)
