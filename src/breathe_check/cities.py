"""The cities we study, and the role each one plays in the analysis.

Roles:
- "grap":   inside Delhi-NCR, where GRAP pollution rules apply (the "treated" group)
- "control": outside NCR but on the same Indo-Gangetic plain, with similar winter
             weather and crop-fire smoke, and no GRAP (the comparison group)
- "indore_peer": cities of a similar size and region to compare Indore with
- "indore": Indore itself
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    slug: str
    name: str
    state: str
    lat: float
    lon: float
    role: str


CITIES: tuple[City, ...] = (
    # Delhi-NCR (GRAP applies)
    City("delhi", "Delhi", "Delhi", 28.6139, 77.2090, "grap"),
    City("gurugram", "Gurugram", "Haryana", 28.4595, 77.0266, "grap"),
    City("noida", "Noida", "Uttar Pradesh", 28.5355, 77.3910, "grap"),
    City("ghaziabad", "Ghaziabad", "Uttar Pradesh", 28.6692, 77.4538, "grap"),
    City("faridabad", "Faridabad", "Haryana", 28.4089, 77.3178, "grap"),
    # Comparison cities on the same plain, no GRAP
    City("lucknow", "Lucknow", "Uttar Pradesh", 26.8467, 80.9462, "control"),
    City("kanpur", "Kanpur", "Uttar Pradesh", 26.4499, 80.3319, "control"),
    City("patna", "Patna", "Bihar", 25.5941, 85.1376, "control"),
    City("chandigarh", "Chandigarh", "Chandigarh", 30.7333, 76.7794, "control"),
    # Indore and its peers
    City("indore", "Indore", "Madhya Pradesh", 22.7196, 75.8577, "indore"),
    City("bhopal", "Bhopal", "Madhya Pradesh", 23.2599, 77.4126, "indore_peer"),
    City("jaipur", "Jaipur", "Rajasthan", 26.9124, 75.7873, "indore_peer"),
    City("nagpur", "Nagpur", "Maharashtra", 21.1458, 79.0882, "indore_peer"),
    City("ahmedabad", "Ahmedabad", "Gujarat", 23.0225, 72.5714, "indore_peer"),
    # Big cities people will look up for the run window
    City("mumbai", "Mumbai", "Maharashtra", 19.0760, 72.8777, "other"),
    City("bengaluru", "Bengaluru", "Karnataka", 12.9716, 77.5946, "other"),
    City("chennai", "Chennai", "Tamil Nadu", 13.0827, 80.2707, "other"),
    City("kolkata", "Kolkata", "West Bengal", 22.5726, 88.3639, "other"),
    City("hyderabad", "Hyderabad", "Telangana", 17.3850, 78.4867, "other"),
    City("pune", "Pune", "Maharashtra", 18.5204, 73.8567, "other"),
)

DEFAULT_CITY = "indore"

_BY_SLUG = {c.slug: c for c in CITIES}


def get_city(slug: str) -> City:
    """Look up a city by its slug, e.g. "indore"."""
    try:
        return _BY_SLUG[slug.lower()]
    except KeyError:
        known = ", ".join(sorted(_BY_SLUG))
        raise KeyError(f"Unknown city '{slug}'. Known cities: {known}") from None


def cities_with_role(role: str) -> list[City]:
    return [c for c in CITIES if c.role == role]
