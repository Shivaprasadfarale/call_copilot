"""
Smart Keyword Generator
Generates defensible, high-intent commercial keywords based on the verified Operational Delivery Model:
1. NATIONWIDE_VIRTUAL: 100% Nationwide/online queries (Zero local city names).
2. LOCAL_IN_PERSON: 1 base hub + 9 surrounding major commercial economic engines within 25-50 miles.
3. HYBRID: Core virtual/national queries + high-ticket corporate regional hub terms.
"""

from typing import List, Dict, Any


def generate_smart_keywords(
    company_name: str,
    niche: str,
    model: str,
    base_city: str = "",
    regional_hubs: List[str] = None,
    packages: List[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Generates 10 commercial keywords tailored to the business model."""
    niche_clean = niche.lower().replace("services", "").replace("company", "").strip()
    keywords = []

    if model == "NATIONWIDE_VIRTUAL":
        # Rule: STRICT PROHIBITION ON CITY/STATE NAMES
        # Detect industry archetype from niche and company name
        full_text = f"{niche_clean} {company_name}".lower()

        is_recruiting = any(w in full_text for w in ["recruiter", "recruiting", "recruitment", "search", "talent", "headhunter", "staffing"])
        is_consulting = any(w in full_text for w in ["consulting", "consultant", "advisory", "compliance", "strategy"])

        if is_recruiting:
            # Executive Search / Recruiting / Talent Archetype (e.g. Beauty & Wellness Executive Search)
            base_niche = "beauty and wellness" if any(b in full_text for b in ["beauty", "wellness", "cosmetic", "skincare", "talent"]) else niche_clean
            templates = [
                (f"beauty executive search firm", "Retained C-Suite & VP Search", "$35,000 – $75,000 per search"),
                (f"wellness executive recruiter", "Wellness Leadership & Director Placement", "$25,000 – $60,000 per placement"),
                (f"cosmetics executive search agency", "Cosmetics & Color Brand Leadership", "$30,000 – $70,000 per search"),
                (f"beauty industry executive recruiters", "Enterprise Beauty Brand Talent Acquisition", "$25,000 – $55,000 per search"),
                (f"skincare executive recruitment firm", "Skincare & Dermatological Brand Search", "$30,000 – $65,000 per search"),
                (f"beauty and wellness executive search", "National Beauty & Wellness Retained Advisory", "$35,000 – $80,000 per search"),
                (f"personal care executive search firm", "Personal Care & CPG Executive Search", "$30,000 – $65,000 per search"),
                (f"beauty brand executive headhunters", "Indie & Luxury Brand Headhunting", "$25,000 – $60,000 retainer"),
                (f"wellness leadership recruiting firm", "VP & C-Level Wellness Recruiting", "$25,000 – $50,000 per placement"),
                (f"retained executive search beauty industry", "Full Retained Executive Placement", "$40,000 – $90,000 retainer")
            ]
        elif is_consulting:
            templates = [
                (f"national {niche_clean} consulting firm", "Corporate Advisory & Audits", "$10,000 – $35,000 contract"),
                (f"enterprise {niche_clean} consultants", "Strategic Enterprise Engagements", "$15,000 – $50,000 retainer"),
                (f"{niche_clean} advisory services", "Retained Strategic Advisory", "$5,000 – $20,000 monthly retainer"),
                (f"specialized {niche_clean} consultant online", "Specialized Project Engagements", "$7,500 – $25,000 project"),
                (f"commercial {niche_clean} management", "National Program Management", "$12,000 – $40,000 contract"),
                (f"independent {niche_clean} auditor", "Compliance & Technical Verification", "$5,000 – $15,000 per audit"),
                (f"virtual {niche_clean} consulting services", "Remote Strategic Advisory", "$5,000 – $18,000 engagement"),
                (f"{niche_clean} advisory firm nationwide", "Full Retained Advisory", "$15,000 – $60,000 contract"),
                (f"senior {niche_clean} specialist", "Expert Advisory & Case Reviews", "$8,000 – $25,000 project"),
                (f"{niche_clean} compliance and advisory", "Regulatory & Strategic Audits", "$10,000 – $30,000 engagement")
            ]
        else: # Coaching, Speakers, Programs
            templates = [
                (f"online {niche_clean} coach", "Virtual Coaching & Fundamentals", "$397 – $1,191 program"),
                (f"executive {niche_clean} coaching online", "High-Ticket Leadership Optimization", "$3,582 6-month package"),
                (f"virtual performance coach", "Performance & Consistency Programs", "$1,191 – $3,582 online program"),
                (f"corporate leadership keynote speaker", "Corporate Conferences & Keynotes", "$5,000 – $15,000 per keynote"),
                (f"online {niche_clean} coaching program", "Multi-Week Cohorts & Group Training", "$397 – $1,191 course"),
                (f"{niche_clean} coach for founders online", "Founder Mindset & Leadership", "$1,191 – $3,582 retainer"),
                (f"executive leadership keynote speaker", "Annual Summits & Corporate Keynotes", "$5,000 – $15,000 per event"),
                (f"virtual executive advisory", "Remote Executive Advisory & Retainers", "$3,582 6-month advisory"),
                (f"leadership performance coaching online", "Corporate Leadership Development", "$2,500 – $7,500 retainer"),
                (f"keynote speaker on corporate leadership", "Enterprise Headline Keynotes", "$5,000 – $15,000 per event")
            ]

        # Use packages if available to customize fee ranges
        for idx, (phrase, tag, default_fee) in enumerate(templates, 1):
            keywords.append({
                "id": idx,
                "phrase": phrase.strip(),
                "tag": tag,
                "fee_range": default_fee,
                "scenario": f"A brand founder, corporate VP, or HR leader searching nationally across the US for {phrase.strip()}."
            })

    elif model == "LOCAL_IN_PERSON":
        # Rule: 1 base hub + 9 surrounding major economic hubs within 25-50 miles
        niche_lower = f"{niche_clean} {company_name}".lower()

        if any(w in niche_lower for w in ["junk", "haul", "cleanout", "debris", "trash", "rubbish"]):
            sub_services = [
                f"commercial {niche_clean}",
                f"{niche_clean} services",
                f"estate cleanout and {niche_clean}",
                f"property cleanout services",
                f"{niche_clean} contractor",
                f"emergency {niche_clean}",
                f"heavy {niche_clean}",
                f"debris hauling and {niche_clean}",
                f"commercial property cleanouts",
                f"{niche_clean} company"
            ]
            fees = ["$1,500 – $4,500 contract", "$800 – $2,500 per cleanout", "$1,200 – $3,500 project", "$2,500 – $8,500 commercial bid", "$1,000 – $3,000 service fee", "$1,500 – $5,000 commercial contract", "$750 – $2,200 haul", "$1,800 – $4,200 property contract", "$2,000 – $6,500 retainer", "$1,000 – $3,500 verified job"]
        elif any(w in niche_lower for w in ["roof", "shingle", "gutter", "siding"]):
            sub_services = [
                f"commercial {niche_clean}",
                f"emergency {niche_clean} repair",
                f"{niche_clean} replacement contractor",
                f"residential {niche_clean} services",
                f"commercial property {niche_clean}",
                f"certified {niche_clean} company",
                f"flat {niche_clean} contractor",
                f"storm damage {niche_clean}",
                f"industrial {niche_clean} company",
                f"licensed {niche_clean} specialist"
            ]
            fees = ["$5,000 – $15,000 replacement", "$1,500 – $4,500 repair", "$8,000 – $25,000 commercial roof", "$3,500 – $12,000 project", "$5,000 – $18,000 contract", "$2,500 – $7,500 repair", "$10,000 – $35,000 flat roof", "$4,000 – $14,000 claim", "$12,000 – $45,000 contract", "$6,000 – $20,000 project"]
        elif any(w in niche_lower for w in ["plumb", "drain", "pipe", "sewer", "water heater"]):
            sub_services = [
                f"commercial {niche_clean}",
                f"emergency {niche_clean} services",
                f"licensed {niche_clean} contractor",
                f"commercial drain and {niche_clean}",
                f"24 hour {niche_clean}",
                f"industrial {niche_clean} company",
                f"sewer line and {niche_clean}",
                f"certified master {niche_clean}",
                f"commercial property {niche_clean}",
                f"reputable {niche_clean} company"
            ]
            fees = ["$1,500 – $5,000 contract", "$500 – $1,800 repair", "$2,500 – $8,500 commercial bid", "$1,200 – $3,500 cleanout", "$750 – $2,500 emergency", "$3,500 – $12,000 contract", "$2,000 – $6,500 sewer job", "$1,000 – $3,500 service fee", "$2,500 – $7,500 contract", "$1,200 – $4,000 verified project"]
        elif any(w in niche_lower for w in ["shuttle", "transport", "limo", "chauffeur", "ride"]):
            sub_services = [
                f"group {niche_clean}",
                f"airport {niche_clean} services",
                f"corporate {niche_clean}",
                f"private {niche_clean} company",
                f"event {niche_clean}",
                f"executive {niche_clean} services",
                f"group airport transportation",
                f"wedding {niche_clean}",
                f"corporate event transportation",
                f"hourly {niche_clean} service"
            ]
            fees = ["$800 – $2,500 private charter", "$450 – $1,200 airport group", "$1,500 – $4,500 corporate event", "$600 – $1,800 private group", "$1,200 – $3,500 wedding group", "$900 – $2,800 executive ride", "$500 – $1,500 airport shuttle", "$1,500 – $4,000 event charter", "$2,000 – $5,500 conference shuttle", "$750 – $2,200 charter fee"]
        elif any(w in niche_lower for w in ["law", "attorney", "lawyer", "legal"]):
            sub_services = [
                f"business litigation {niche_clean}",
                f"corporate {niche_clean} firm",
                f"commercial {niche_clean} specialist",
                f"experienced {niche_clean}",
                f"top rated {niche_clean} firm",
                f"retained corporate {niche_clean}",
                f"commercial contract {niche_clean}",
                f"business dispute {niche_clean}",
                f"premier {niche_clean} office",
                f"specialized {niche_clean} counsel"
            ]
            fees = ["$5,000 – $25,000 retainer", "$10,000 – $50,000 litigation", "$7,500 – $30,000 contract", "$5,000 – $15,000 retainer", "$8,000 – $35,000 dispute", "$10,000 – $40,000 retainer", "$4,500 – $18,000 advisory", "$12,000 – $60,000 case", "$6,000 – $20,000 fee", "$7,500 – $25,000 retainer"]
        elif any(w in niche_lower for w in ["dental", "dentist", "orthodont", "teeth"]):
            sub_services = [
                f"cosmetic {niche_clean}",
                f"emergency {niche_clean} clinic",
                f"dental implant {niche_clean}",
                f"family and cosmetic {niche_clean}",
                f"advanced {niche_clean} care",
                f"top rated {niche_clean} office",
                f"restorative {niche_clean} specialist",
                f"full mouth reconstruction {niche_clean}",
                f"pediatric and family {niche_clean}",
                f"comprehensive {niche_clean} center"
            ]
            fees = ["$3,500 – $12,000 procedure", "$500 – $1,800 emergency visit", "$4,000 – $20,000 implants", "$1,200 – $4,500 treatment", "$2,500 – $8,000 cosmetic", "$1,500 – $5,000 care", "$3,000 – $10,000 restoration", "$15,000 – $45,000 reconstruction", "$800 – $2,500 care", "$2,000 – $6,500 procedure"]
        else: # General Local Commercial Service
            sub_services = [
                f"commercial {niche_clean}",
                f"{niche_clean} services",
                f"licensed {niche_clean} contractor",
                f"emergency {niche_clean}",
                f"commercial property {niche_clean}",
                f"certified {niche_clean} company",
                f"professional {niche_clean} specialist",
                f"industrial {niche_clean} services",
                f"premier {niche_clean} company",
                f"top rated {niche_clean} contractor"
            ]
            fees = ["$2,500 – $8,500 commercial bid", "$1,500 – $4,500 service contract", "$3,000 – $9,000 project", "$1,000 – $3,500 emergency call", "$2,000 – $6,500 property contract", "$2,500 – $7,500 job", "$1,800 – $5,200 specialist fee", "$4,000 – $14,000 industrial contract", "$2,200 – $6,800 project", "$3,000 – $10,000 verified contract"]

        state_hubs_map = {
            "ca": ["riverside", "palm desert", "temecula", "moreno valley", "san bernardino", "palm springs", "ontario", "murrieta", "corona", "fontana"],
            "tx": ["dallas", "fort worth", "plano", "arlington", "frisco", "denton", "mckinney", "austin", "san antonio", "houston"],
            "fl": ["tampa", "orlando", "miami", "fort lauderdale", "jacksonville", "sarasota", "st petersburg", "boca raton", "coral gables", "clearwater"],
            "sc": ["charleston", "florence", "columbia", "wilmington", "conway", "georgetown", "pawleys island", "murrells inlet", "north myrtle beach", "surfside beach"],
            "nc": ["charlotte", "raleigh", "greensboro", "durham", "concord", "huntersville", "wilmington", "winston salem", "cary", "high point"],
            "tn": ["nashville", "knoxville", "chattanooga", "memphis", "maryville", "oak ridge", "murfreesboro", "franklin", "brentwood", "johnson city"],
            "co": ["denver", "boulder", "aurora", "fort collins", "colorado springs", "greeley", "longmont", "lakewood", "thornton", "arvada"]
        }

        # Detect state from base_city or regional_hubs
        detected_state = "ca"
        for st in state_hubs_map.keys():
            if base_city and f" {st}" in base_city.lower():
                detected_state = st
                break

        hubs = list(regional_hubs) if regional_hubs else []
        if base_city and base_city not in hubs:
            hubs.insert(0, base_city)

        fallback_pool = state_hubs_map.get(detected_state, state_hubs_map["ca"])
        for h in fallback_pool:
            if len(hubs) >= 10:
                break
            if h not in hubs:
                hubs.append(h)

        while len(hubs) < 10:
            hubs.append(f"regional market {len(hubs)+1}")

        fees = [
            "$1,500 – $4,500 contract",
            "$800 – $2,500 per cleanout",
            "$1,200 – $3,500 project",
            "$2,500 – $8,500 commercial bid",
            "$1,000 – $3,000 service fee",
            "$1,500 – $5,000 commercial contract",
            "$750 – $2,200 haul",
            "$1,800 – $4,200 property contract",
            "$2,000 – $6,500 retainer",
            "$1,000 – $3,500 verified job"
        ]

        for idx in range(1, 11):
            target_city = hubs[idx - 1]
            service_label = sub_services[idx - 1] if idx <= len(sub_services) else f"{niche_clean} services"
            phrase = f"{service_label} {target_city}".strip()
            keywords.append({
                "id": idx,
                "phrase": phrase,
                "tag": f"Commercial {niche_clean.title()} in {target_city.title()}",
                "fee_range": fees[idx - 1],
                "scenario": f"A commercial property manager, business owner, or client in {target_city.title()} searching Google to hire {phrase}."
            })

    else: # HYBRID
        full_text = f"{niche_clean} {company_name}".lower()
        is_recruiting = any(w in full_text for w in ["recruiter", "recruiting", "recruitment", "search", "talent", "headhunter", "staffing"])
        is_consulting = any(w in full_text for w in ["consulting", "consultant", "advisory", "compliance", "strategy"])

        hub_name = base_city if base_city else "Los Angeles"

        if is_recruiting:
            rec_niche = "beauty" if any(b in full_text for b in ["beauty", "wellness", "cosmetic", "skincare"]) else niche_clean
            templates_hybrid = [
                (f"{rec_niche} executive search firm", "Retained C-Suite & VP Search", "$35,000 – $75,000 per search"),
                (f"wellness executive recruiter" if "wellness" in full_text else f"{rec_niche} executive recruiter", "Executive Leadership Placement", "$25,000 – $60,000 per placement"),
                (f"{rec_niche} executive search agency", "Corporate Leadership & Search", "$30,000 – $70,000 per search"),
                (f"{rec_niche} industry executive recruiters", "Enterprise Talent Acquisition", "$25,000 – $55,000 per search"),
                (f"specialized {rec_niche} recruitment firm", "Specialized Leadership Search", "$30,000 – $65,000 per search"),
                (f"{rec_niche} industry recruiter {hub_name.lower()}", f"Regional {hub_name.title()} Talent Hub", "$30,000 – $70,000 per search"),
                (f"commercial {rec_niche} executive search firm", "Retained Executive Search", "$30,000 – $65,000 per search"),
                (f"{rec_niche} brand executive headhunters", "Headhunting & Retained Advisory", "$25,000 – $60,000 retainer"),
                (f"executive search firm {hub_name.lower()}", f"Executive Recruitment Hub in {hub_name.title()}", "$30,000 – $75,000 per search"),
                (f"retained executive search {rec_niche} industry", "Full Retained Executive Placement", "$40,000 – $90,000 retainer")
            ]
        elif is_consulting:
            templates_hybrid = [
                (f"national {niche_clean} consulting firm", "Corporate Advisory & Audits", "$10,000 – $35,000 contract"),
                (f"enterprise {niche_clean} consultants", "Strategic Enterprise Engagements", "$15,000 – $50,000 retainer"),
                (f"{niche_clean} advisory services", "Retained Strategic Advisory", "$5,000 – $20,000 monthly retainer"),
                (f"specialized {niche_clean} consultant online", "Specialized Project Engagements", "$7,500 – $25,000 project"),
                (f"commercial {niche_clean} management", "National Program Management", "$12,000 – $40,000 contract"),
                (f"{niche_clean} firm {hub_name.lower()}", f"Regional Advisory Hub in {hub_name.title()}", "$10,000 – $30,000 contract"),
                (f"virtual {niche_clean} consulting services", "Remote Strategic Advisory", "$5,000 – $18,000 engagement"),
                (f"{niche_clean} advisory firm nationwide", "Full Retained Advisory", "$15,000 – $60,000 contract"),
                (f"senior {niche_clean} specialist {hub_name.lower()}", f"Specialist Retainers in {hub_name.title()}", "$8,000 – $25,000 project"),
                (f"{niche_clean} compliance and advisory", "Regulatory & Strategic Audits", "$10,000 – $30,000 engagement")
            ]
        else:
            templates_hybrid = [
                (f"online {niche_clean} coach", "Virtual Mindset Coaching & Fundamentals", "$397 – $1,191 Zoom package"),
                (f"executive {niche_clean} coaching online", "Virtual Executive Leadership Optimization", "$3,582 package"),
                (f"virtual performance coach", "Remote Performance & Consistency Coaching", "$1,191 – $3,582 program"),
                ("resilience keynote speaker", "National & Regional Keynote Presentations", "$5,000 – $15,000 per event"),
                (f"{niche_clean} coach {hub_name.lower()}", f"Executive Hub in {hub_name.title()}", "$3,500 – $10,000 retainer"),
                (f"keynote speaker {hub_name.lower()}", f"Regional Headline Keynotes in {hub_name.title()}", "$5,000 – $12,500 per event"),
                ("online coaching program", "Structured Multi-Week Virtual Cohorts", "$397 – $1,191 course"),
                (f"executive coaching services {hub_name.lower()}", f"Corporate Executive Retainers in {hub_name.title()}", "$3,500 – $10,000 package"),
                ("executive resilience coach online", "Virtual Executive Advisory & Retention", "$3,582 6-month advisory"),
                ("corporate keynote speaker on leadership", "Enterprise Leadership Keynotes", "$5,000 – $15,000 per event")
            ]

        for idx, (phrase, tag, fee) in enumerate(templates_hybrid, 1):
            keywords.append({
                "id": idx,
                "phrase": phrase.strip(),
                "tag": tag,
                "fee_range": fee,
                "scenario": f"A brand founder, corporate VP, or hiring executive searching for {phrase.strip()}."
            })

    return keywords
