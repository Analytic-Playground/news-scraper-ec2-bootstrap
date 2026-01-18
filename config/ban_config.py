# dictionaries and lists for states and keywords
# --- 1. State / Region mapping ---
state_patterns = {
    "Alabama": r"\bAlabama\b", # |\bAL\b seems to get confused with AI?
    "Alaska": r"\bAlaska\b|\bAK\b",
    "Arizona": r"\bArizona\b|\bAZ\b",
    "Arkansas": r"\bArkansas\b|\bAR\b",
    "California": r"\bCalifornia\b|\bCA\b|\bLA\b|\bNewsom\b",
    "Colorado": r"\bColorado\b|\bCO\b|\bDenver\b",
    "Connecticut": r"\bConnecticut\b|\bCT\b",
    "Delaware": r"\bDelaware\b|\bDE\b",
    "Florida": r"\bFlorida\b|\bFL\b",
    "Georgia": r"\bGeorgia\b|\bGA\b|\bAtlanta\b",
    "Hawaii": r"\bHawaii\b|\bHI\b",
    "Idaho": r"\bIdaho\b|\bID\b",
    "Illinois": r"\bIllinois\b|\bIL\b|\bChicago\b",
    "Indiana": r"\bIndiana\b", # |\bIN\b removed, this is too common of a pattern to match on
    "Iowa": r"\bIowa\b|\bIA\b",
    "Kansas": r"\bKansas\b|\bKS\b",
    "Kentucky": r"\bKentucky\b|\bKY\b",
    "Louisiana": r"\bLouisiana\b", # |\bLA\b removed, LA abbreviation since LA, CA is more common
    "Maine": r"\bMaine\b", # |\bME\b removed, unlikely to be used correctly
    "Maryland": r"\bMaryland\b|\bMD\b",
    "Massachusetts": r"\bMassachusetts\b|\bMA\b",
    "Michigan": r"\bMichigan\b|\bMI\b|\bDetroit\b",
    "Minnesota": r"\bMinnesota\b|\bMN\b",
    "Mississippi": r"\bMississippi\b|\bMS\b",
    "Missouri": r"\bMissouri\b|\bMO\b",
    "Montana": r"\bMontana\b|\bMT\b",
    "Nebraska": r"\bNebraska\b|\bNE\b",
    "Nevada": r"\bNevada\b|\bNV\b",
    "New Hampshire": r"\bNew Hampshire\b|\bNH\b",
    "New Jersey": r"\bNew Jersey\b|\bNJ\b|\bN.J.\b",
    "New Mexico": r"\bNew Mexico\b|\bNM\b",
    "New York": r"\bNew York\b|\bNY\b|\bSuffolk County\b|\bN.Y.\b",
    "North Carolina": r"\bNorth Carolina\b|\bNC\b",
    "North Dakota": r"\bNorth Dakota\b|\bND\b",
    "Ohio": r"\bOhio\b|\bOH\b",
    "Oklahoma": r"\bOklahoma\b|\bOK\b",
    "Oregon": r"\bOregon\b", # |\bOR\b removed, headlines are likely to contain the word 'or'
    "Pennsylvania": r"\bPennsylvania\b|\bPA\b",
    "Rhode Island": r"\bRhode Island\b|\bRI\b",
    "South Carolina": r"\bSouth Carolina\b|\bSC\b",
    "South Dakota": r"\bSouth Dakota\b|\bSD\b",
    "Tennessee": r"\bTennessee\b|\bTN\b",
    "Texas": r"\bTexas\b|\bTX\b|\bEl Paso\b|\bDallas\b",
    "Utah": r"\bUtah\b|\bUT\b",
    "Vermont": r"\bVermont\b|\bVT\b",
    "Virginia": r"\bVirginia\b|\bVA\b",
    "Washington": r"\bWashington\b|\bWA\b",
    "West Virginia": r"\bWest Virginia\b|\bWV\b",
    "Wisconsin": r"\bWisconsin\b|\bWI\b",
    "Wyoming": r"\bWyoming\b|\bWY\b",
    "District of Columbia": r"\bWashington DC\b|\bD\.C\.\b|\bDC\b",
    "National": r"\bTrump\b|\bwhite house\b|\bcongress\b|\bTSA\b"
}

# --- keyword → synonyms/patterns (ordered by priority) ---
keywords = {
    # abbreviations
    "AI":         [r"\bAI\b", r"\bartificial intelligence\b", r"\bopenai\b", r"\bopen ai\b"],
    "DEI":        [r"\bDEI\b", r"\bdiversity\b"],
    # drugs 
    "cannabis":   [r"\bcannabis\b", r"\bmarijuana\b", r"\bweed\b", r"\bpot\b", r"\bcannabinoids\b", r"\bTHC\b", r"\bCBD\b", r"\bhemp\b", r"\bhemp[-\s]?derived\b"],
    "kratom":     [r"\bkratom\b", r"\b7-?oh\b"],
    "vapes":      [r"\bvapes?\b", r"\bvaping\b", r"\be-?cig(?:arette)?s?\b", r"\bflavored vapes?\b"],
    "tobacco":    [r"\btobacco\b", r"\bnicotine\b"],
    "alcohol":    [r"\balcohol\b", r"\bliquor\b", r"\bbeer\b", r"\bwine\b", r"\bwhiskey\b", r"\bbourbon\b", r"\bbooze\b"],
    "drugs":      [r"\bxanax\b|\bdrug\b"],
    # health-care
    "gender-affirming care": [r"\bgender[-\s]?affirming care\b", r"\bpuberty blockers?\b", r"\bhormone therapy\b", r"\btrans\b", r"\btransgender\b", r"\bbathroom ban\b", r"\bpronouns\b"],
    "abortion":   [r"\babortion\b", r"\bmifepristone\b", r"\bplan\s?b\b"],
    "health-care":[r"\btherapy\b", r"\bhealth-care\b", r"\bhealth care\b", r"\bmental health\b"],
    "vaccines":   [r"\bvaccine\b", r"\bvaccines\b"],
    "masks":      [r"\bmask\b", r"\bmasks\b", r"\bmasked\b"],
    # technology
    "tiktok":     [r"\bTikTok\b"],
    "drones":     [r"\bdrone\b|\bdrones\b"],
    "cell phones":[r"\bcell phones?\b", r"\bcellphones?\b", r"\bsmartphones?\b", r"\bmobile phones?\b", r"\bphone\b", r"\bphones\b"],
    "voting":     [r"\bmail in voting\b", r"\bmail-in voting\b", r"\bmail-in ballots\b", r"\bmail voting\b", r"\bmail ballots\b", r"\branked choice voting\b", r"\bvoter\b"],
    # environmental
    "plastic bags":[r"\bplastic bags?\b", r"\bsingle[-\s]?use bags?\b", r"\bsingle-use carryout bags\b"],
    "burn ban":   [r"\bburn ban(s)?\b", r"\bfire bans\b|\bfire ban\b"],
    "lawn watering ban": [r"\blawn watering ban\b"],
    "pollution":  [r"\bmicroplastics\b", r"\bpfas\b", r"\bstraws?\b", r"\bEPA\b", r"\basbestos\b",r"\bpolystyrene\b"],
    "renewables": [r"\bwind\b", r"\bsolar\b", r"\bhydropower\b", r"\belectric\b"],
    "fossil fuels":[r"\boil\b", r"\bcoal\b", r"\bnatural gas\b"],
    "food waste": [r"\bfood waste\b"],
    "fireworks":    [r"\bfireworks\b"],
    # entertainment
    "sports":     [r"\bathlete(s)?\b", r"\bsports\b", r"\bmma\b", r"\bncaa\b", r"\bNBA\b", r"\bNFL\b", r"\bBill Belichick\b"],
    "drag shows": [r"\bdrag shows?\b", r"\bdrag performances?\b", r"\bdrag ban\b"],
    "gaming":     [r"\broblox\b"],
    "social media":[r"\bsocial media\b"],
    "gambling":   [r"\bgambling\b", r"\bcasino(s)?\b", r"\bsports betting\b", r"\bdraft kings\b"],
    # financial
    "financial": [r"\bSBA\b"],
    "stock trading": [r"\btrading ban\b", r"\btrading stocks\b"],
    # misc.
    "tear gas":   [r"\btear gas\b"],
    "parking":    [r"\bparking\b"],
    "food stamps":    [r"\bSNAP\b", r"\bfood stamps\b"],
    "labor rights": [r"\bnoncompete\b", r"\bnon compete\b"],
    "costmetics": [r"\bgel nail polish"],
    "lab grown meat": [r"\blab grown meat\b", r"\blab-grown meat\b"],
    "police":     [r"\bsecret police\b", r"\bice\b", r"\bban federal agents\b", r"\blaw enforcement\b", r"\bfederal agents\b"],
    "LGBQ":     [r"\blgbt\b", r"\blgbtq+\b", r"\bcolorful crosswalks\b", r"\brainbow\b", r"\bpride\b", r"\bgay\b", r"\blesbian\b"],
    "first amendment":[r"\bfirst amendment\b"],
    "real estate":[r"\bforeign buyers\b"],
    "veterans":   [r"\bveterans\b", r"\bveteran\b"],
    "religion":   [r"\bprayers\b", r"\bprayer\b", r"\bten commandments\b"],
    "housing":    [r"\brentals\b", r"\bhomeless\b"],
    "books":      [r"\bbook(s)?\b", r"\blibrary materials?\b", r"\btextbooks?\b", r"\bliterary classics\b"],
    "travel":     [r"\btravel\b", r"\btravel (?:ban|restriction|restrictions)\b", r"\bvisa(s)?\b", r"\bchecked bags\b", r"\bentry bans\b", r"\btsa\b"],
    "guns":       [r"\bguns?\b", r"\bfirearms?\b", r"\bAR-?15s?\b", r"\bassault weapon(s)?\b|\bassault weapon(s)?\b[^\w]",
                   r"\bbinary trigger ban\b", r"\bnra\b", r"\bMinnesota trigger ban\b", r"\bopen carry\b", r"\bopen-carry\b"]
}
