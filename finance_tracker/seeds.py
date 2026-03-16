from finance_tracker.categories import CategoryType
from finance_tracker.models import Rule

SEED_RULES: list[tuple[str, CategoryType]] = [
    # Groceries
    ("TESCO", CategoryType.GROCERIES),
    ("SAINSBURY", CategoryType.GROCERIES),
    ("ASDA", CategoryType.GROCERIES),
    ("ALDI", CategoryType.GROCERIES),
    ("LIDL", CategoryType.GROCERIES),
    ("MORRISONS", CategoryType.GROCERIES),
    ("WAITROSE", CategoryType.GROCERIES),
    ("CO-OP", CategoryType.GROCERIES),
    ("M&S FOOD", CategoryType.GROCERIES),
    # Subscriptions
    ("NETFLIX", CategoryType.SUBSCRIPTIONS),
    ("SPOTIFY", CategoryType.SUBSCRIPTIONS),
    ("DISNEY PLUS", CategoryType.SUBSCRIPTIONS),
    ("AMAZON PRIME", CategoryType.SUBSCRIPTIONS),
    ("APPLE.COM/BILL", CategoryType.SUBSCRIPTIONS),
    # Housing
    ("COUNCIL TAX", CategoryType.HOUSING),
    # Utilities
    ("BRITISH GAS", CategoryType.UTILITIES),
    ("EDF ENERGY", CategoryType.UTILITIES),
    ("OCTOPUS ENERGY", CategoryType.UTILITIES),
    ("OVO ENERGY", CategoryType.UTILITIES),
    ("SCOTTISH POWER", CategoryType.UTILITIES),
    ("BULB ENERGY", CategoryType.UTILITIES),
    ("THAMES WATER", CategoryType.UTILITIES),
    ("SEVERN TRENT", CategoryType.UTILITIES),
    ("ANGLIAN WATER", CategoryType.UTILITIES),
    ("UNITED UTILITIES", CategoryType.UTILITIES),
    ("SOUTH EAST WATER", CategoryType.UTILITIES),
    # Phone & Internet
    ("BT GROUP", CategoryType.PHONE_INTERNET),
    ("VODAFONE", CategoryType.PHONE_INTERNET),
    ("EE LIMITED", CategoryType.PHONE_INTERNET),
    ("THREE", CategoryType.PHONE_INTERNET),
    ("O2", CategoryType.PHONE_INTERNET),
    ("SKY", CategoryType.PHONE_INTERNET),
    ("VIRGIN MEDIA", CategoryType.PHONE_INTERNET),
    ("PLUSNET", CategoryType.PHONE_INTERNET),
    # Insurance
    ("AVIVA", CategoryType.INSURANCE),
    ("ADMIRAL", CategoryType.INSURANCE),
    ("DIRECT LINE", CategoryType.INSURANCE),
    ("AA INSURANCE", CategoryType.INSURANCE),
    ("RAC", CategoryType.INSURANCE),
    # Transport
    ("TFL", CategoryType.TRANSPORT),
    ("TRAINLINE", CategoryType.TRANSPORT),
    ("NATIONAL RAIL", CategoryType.TRANSPORT),
    ("UBER", CategoryType.TRANSPORT),
    # Eating out
    ("JUST EAT", CategoryType.EATING_OUT),
    ("DELIVEROO", CategoryType.EATING_OUT),
    ("UBER EATS", CategoryType.EATING_OUT),
    ("NANDOS", CategoryType.EATING_OUT),
    ("GREGGS", CategoryType.EATING_OUT),
    ("COSTA", CategoryType.EATING_OUT),
    ("STARBUCKS", CategoryType.EATING_OUT),
    ("PRET A MANGER", CategoryType.EATING_OUT),
    # Shopping
    ("AMAZON.CO.UK", CategoryType.SHOPPING),
    ("AMAZON MKTPLACE", CategoryType.SHOPPING),
    ("EBAY", CategoryType.SHOPPING),
    ("ARGOS", CategoryType.SHOPPING),
    ("JOHN LEWIS", CategoryType.SHOPPING),
    ("NEXT", CategoryType.SHOPPING),
    ("IKEA", CategoryType.SHOPPING),
    # Healthcare
    ("NHS", CategoryType.HEALTHCARE),
    ("BOOTS PHARM", CategoryType.HEALTHCARE),
]


def build_seed_rules() -> list[Rule]:
    """Create Rule objects for common UK merchants."""
    return [
        Rule(pattern=pattern, category=category, source="seed") for pattern, category in SEED_RULES
    ]
