import os
import re
import glob
import json
from datetime import datetime, timezone, timedelta

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS_DIR = os.path.join(WORKSPACE_DIR, 'knowledge_base', 'leads')
SCREENSHOTS_DIR = os.path.join(WORKSPACE_DIR, 'screenshots')
MASTER_PATH = os.path.join(WORKSPACE_DIR, 'scratch', 'master_client_directory_enriched.json')
PMS_CACHE_PATH = os.path.join(WORKSPACE_DIR, 'data', 'pms_cache.json')
VERIFIED_OUTREACH_PATH = os.path.join(WORKSPACE_DIR, 'scratch', 'verified_outreach_personas.json')

OUTREACH_REGISTRY = {}
if os.path.exists(VERIFIED_OUTREACH_PATH):
    try:
        with open(VERIFIED_OUTREACH_PATH, 'r', encoding='utf-8') as f:
            OUTREACH_REGISTRY = json.load(f)
    except Exception as e:
        print(f"Error loading verified outreach registry: {e}")

COORDINATOR_BANLIST = [
    'arvind', 'yatendra', 'geeta', 'sachin', 'pawan', 'ankit',
    'deepak', 'prem', 'abhishek', 'amit', 'rohit', 'yogesh'
]

AREA_CODE_TIMEZONES = {
    # PST (California, Washington, Oregon, Nevada)
    '206': 'PST', '253': 'PST', '360': 'PST', '425': 'PST', '509': 'PST',
    '503': 'PST', '541': 'PST', '971': 'PST',
    '209': 'PST', '213': 'PST', '310': 'PST', '323': 'PST', '408': 'PST',
    '415': 'PST', '510': 'PST', '530': 'PST', '559': 'PST', '562': 'PST',
    '619': 'PST', '626': 'PST', '650': 'PST', '661': 'PST', '707': 'PST',
    '714': 'PST', '760': 'PST', '805': 'PST', '818': 'PST', '831': 'PST',
    '858': 'PST', '909': 'PST', '916': 'PST', '925': 'PST', '949': 'PST', '951': 'PST',
    '702': 'PST', '775': 'PST',
    # MST (Arizona, Colorado, Utah, New Mexico, Montana, Idaho, Wyoming)
    '480': 'MST', '520': 'MST', '602': 'MST', '623': 'MST', '928': 'MST',
    '303': 'MST', '719': 'MST', '720': 'MST', '970': 'MST',
    '385': 'MST', '435': 'MST', '801': 'MST',
    '505': 'MST', '575': 'MST',
    '208': 'MST', '406': 'MST', '307': 'MST',
    # CST (Texas, Illinois, Minnesota, Missouri, Wisconsin, Tennessee, etc.)
    '210': 'CST', '214': 'CST', '254': 'CST', '281': 'CST', '325': 'CST',
    '361': 'CST', '409': 'CST', '432': 'CST', '469': 'CST', '512': 'CST',
    '713': 'CST', '737': 'CST', '806': 'CST', '817': 'CST', '830': 'CST',
    '832': 'CST', '903': 'CST', '915': 'CST', '936': 'CST', '940': 'CST', '956': 'CST', '972': 'CST', '979': 'CST',
    '217': 'CST', '309': 'CST', '312': 'CST', '618': 'CST', '630': 'CST', '708': 'CST', '773': 'CST', '815': 'CST', '847': 'CST',
    '218': 'CST', '320': 'CST', '507': 'CST', '612': 'CST', '651': 'CST', '763': 'CST', '952': 'CST',
    '314': 'CST', '417': 'CST', '573': 'CST', '636': 'CST', '816': 'CST',
    '262': 'CST', '414': 'CST', '608': 'CST', '715': 'CST', '920': 'CST',
    '423': 'CST', '615': 'CST', '731': 'CST', '865': 'CST', '901': 'CST', '931': 'CST',
    '405': 'CST', '580': 'CST', '918': 'CST',
    '316': 'CST', '620': 'CST', '785': 'CST', '913': 'CST',
    '308': 'CST', '402': 'CST', '531': 'CST',
    '319': 'CST', '515': 'CST', '563': 'CST', '641': 'CST', '712': 'CST',
    '225': 'CST', '318': 'CST', '337': 'CST', '504': 'CST', '985': 'CST',
    '205': 'CST', '251': 'CST', '256': 'CST', '334': 'CST',
    '228': 'CST', '601': 'CST', '662': 'CST',
    '479': 'CST', '501': 'CST', '870': 'CST',
    # EST (New York, Florida, Pennsylvania, Georgia, North Carolina, Ohio, etc.)
    '212': 'EST', '315': 'EST', '347': 'EST', '516': 'EST', '518': 'EST', '585': 'EST', '607': 'EST', '631': 'EST',
    '646': 'EST', '716': 'EST', '718': 'EST', '845': 'EST', '914': 'EST', '917': 'EST', '929': 'EST',
    '239': 'EST', '305': 'EST', '321': 'EST', '352': 'EST', '386': 'EST', '407': 'EST', '561': 'EST', '727': 'EST',
    '772': 'EST', '786': 'EST', '813': 'EST', '850': 'EST', '863': 'EST', '904': 'EST', '941': 'EST', '954': 'EST',
    '215': 'EST', '267': 'EST', '272': 'EST', '412': 'EST', '484': 'EST', '570': 'EST', '610': 'EST', '717': 'EST',
    '724': 'EST', '814': 'EST', '878': 'EST',
    '229': 'EST', '404': 'EST', '470': 'EST', '478': 'EST', '678': 'EST', '706': 'EST', '762': 'EST', '770': 'EST', '912': 'EST',
    '252': 'EST', '336': 'EST', '704': 'EST', '828': 'EST', '910': 'EST', '919': 'EST', '980': 'EST', '984': 'EST',
    '803': 'EST', '843': 'EST', '854': 'EST', '864': 'EST',
    '276': 'EST', '434': 'EST', '540': 'EST', '703': 'EST', '757': 'EST', '804': 'EST',
    '216': 'EST', '330': 'EST', '419': 'EST', '440': 'EST', '513': 'EST', '567': 'EST', '614': 'EST', '740': 'EST', '937': 'EST',
    '201': 'EST', '551': 'EST', '609': 'EST', '732': 'EST', '848': 'EST', '856': 'EST', '862': 'EST', '908': 'EST', '973': 'EST',
    '301': 'EST', '410': 'EST', '443': 'EST', '667': 'EST',
    '339': 'EST', '351': 'EST', '413': 'EST', '508': 'EST', '617': 'EST', '774': 'EST', '781': 'EST', '857': 'EST', '978': 'EST',
    '203': 'EST', '475': 'EST', '860': 'EST', '959': 'EST',
    '248': 'EST', '269': 'EST', '313': 'EST', '517': 'EST', '586': 'EST', '616': 'EST', '734': 'EST', '810': 'EST', '906': 'EST', '989': 'EST',
    # Canada / Special
    '514': 'EST', '438': 'EST', '450': 'EST', # Montreal
    '778': 'PST', '250': 'PST', '604': 'PST', # BC
    '249': 'EST', '705': 'EST', # Ontario
    '236': 'PST' # BC
}

STATE_TIMEZONES = {
    'CA': 'PST', 'CALIFORNIA': 'PST',
    'WA': 'PST', 'WASHINGTON': 'PST',
    'OR': 'PST', 'OREGON': 'PST',
    'NV': 'PST', 'NEVADA': 'PST',
    'BC': 'PST', 'BRITISH COLUMBIA': 'PST',
    'AZ': 'MST', 'ARIZONA': 'MST',
    'CO': 'MST', 'COLORADO': 'MST',
    'UT': 'MST', 'UTAH': 'MST',
    'NM': 'MST', 'NEW MEXICO': 'MST',
    'MT': 'MST', 'MONTANA': 'MST',
    'ID': 'MST', 'IDAHO': 'MST',
    'WY': 'MST', 'WYOMING': 'MST',
    'TX': 'CST', 'TEXAS': 'CST',
    'IL': 'CST', 'ILLINOIS': 'CST',
    'MN': 'CST', 'MINNESOTA': 'CST',
    'MO': 'CST', 'MISSOURI': 'CST',
    'WI': 'CST', 'WISCONSIN': 'CST',
    'TN': 'CST', 'TENNESSEE': 'CST',
    'OK': 'CST', 'OKLAHOMA': 'CST',
    'KS': 'CST', 'KANSAS': 'CST',
    'NE': 'CST', 'NEBRASKA': 'CST',
    'IA': 'CST', 'IOWA': 'CST',
    'LA': 'CST', 'LOUISIANA': 'CST',
    'AL': 'CST', 'ALABAMA': 'CST',
    'MS': 'CST', 'MISSISSIPPI': 'CST',
    'AR': 'CST', 'ARKANSAS': 'CST',
    'NY': 'EST', 'NEW YORK': 'EST',
    'FL': 'EST', 'FLORIDA': 'EST',
    'PA': 'EST', 'PENNSYLVANIA': 'EST',
    'GA': 'EST', 'GEORGIA': 'EST',
    'NC': 'EST', 'NORTH CAROLINA': 'EST',
    'SC': 'EST', 'SOUTH CAROLINA': 'EST',
    'VA': 'EST', 'VIRGINIA': 'EST',
    'OH': 'EST', 'OHIO': 'EST',
    'NJ': 'EST', 'NEW JERSEY': 'EST',
    'MD': 'EST', 'MARYLAND': 'EST',
    'MA': 'EST', 'MASSACHUSETTS': 'EST',
    'CT': 'EST', 'CONNECTICUT': 'EST',
    'MI': 'EST', 'MICHIGAN': 'EST',
    'IN': 'EST', 'INDIANA': 'EST',
    'QC': 'EST', 'QUEBEC': 'EST', 'MONTREAL': 'EST',
    'ON': 'EST', 'ONTARIO': 'EST',
    'DC': 'EST'
}

# Verified PMS and user-supplied data overrides
PMS_OVERRIDES = {
    'centredental': {
        'name': 'Dr. John Shi, DDS',
        'business': 'Centre Dental NYC',
        'email': 'centredentalnyc@gmail.com',
        'phone': '212-925-7066',
        'website': 'https://centredentalnyc.com/',
        'timezone': 'EST',
        'colleague': 'Patrick',
        'location': 'Lower Manhattan, New York, NY'
    },
    'centredentalnyc': {
        'name': 'Dr. John Shi, DDS',
        'business': 'Centre Dental NYC',
        'email': 'centredentalnyc@gmail.com',
        'phone': '212-925-7066',
        'website': 'https://centredentalnyc.com/',
        'timezone': 'EST',
        'colleague': 'Patrick',
        'location': 'Lower Manhattan, New York, NY'
    },
    'alaskahighwaynews': {
        'name': 'Todd Buck',
        'business': 'Alaska Highway News',
        'email': 'alaskahighwaynews@outlook.com',
        'phone': '778-890-2077',
        'website': 'https://www.thealaskahighwaynews.com/contact-3',
        'timezone': 'EST',
        'colleague': 'Catalina',
        'location': 'Fort St. John, BC, Canada'
    },
    'innatlongwood': {
        'name': 'Reservations Team',
        'business': 'The Inn at Longwood Medical',
        'email': 'reservations@innatlongwood.com',
        'phone': '(617) 731-4700',
        'website': 'https://www.innatlongwood.com/',
        'timezone': 'EST',
        'colleague': 'Abigail',
        'location': '342 Longwood Ave, Boston, MA 02115'
    },
    'carolinadrivingschool': {
        'name': 'Carolina Driving School Team',
        'business': 'Carolina Driving School',
        'email': 'drive123@usa.com',
        'phone': '(336) 515-0584',
        'website': 'https://www.carolinadrivingschool.com/',
        'timezone': 'EST',
        'colleague': 'Abigail',
        'location': '534 Walkertown Guthrie Rd, Winston-Salem, NC 27101'
    },
    'crystalcarecleaning': {
        'name': 'Jane Ottero',
        'business': 'CrystalCare Commercial Cleaning',
        'email': 'info@crystalcarecleaning.com',
        'phone': '(732) 510-0258',
        'website': 'https://crystalcarecleaning.com/',
        'timezone': 'EST',
        'colleague': 'Jone',
        'location': 'Central & Northern New Jersey'
    },
    'goldfieldscanada': {
        'name': 'Dayna Hale',
        'business': 'GoldFields Global Canada',
        'email': 'dayna@goldfieldscanada.com',
        'phone': '+1 (905) 806-6114',
        'website': 'https://www.goldfieldscanada.com/',
        'timezone': 'EST',
        'colleague': 'Manoj',
        'location': 'Ontario, Canada'
    },
    'gothamfragrances': {
        'name': 'Aaron Robinson',
        'business': 'Gotham Fragrances',
        'email': 'sales@gothamfragrances.com',
        'phone': '(301) 691-3159',
        'website': 'https://gothamfragrances.com/',
        'timezone': 'EST',
        'colleague': 'Shalandaserita',
        'location': 'Maryland / DC Metro'
    },
    'melrosenl': {
        'name': 'Kathy Brenner',
        'business': 'Melrose Nameplate & Label Co.',
        'email': 'kbrenner@melrose-nl.com',
        'phone': '(800) 826-7741',
        'website': 'https://melrose-nl.com/',
        'timezone': 'PST',
        'colleague': 'Tom',
        'location': 'Hayward, CA'
    },
    'metalbuildmarketing': {
        'name': 'Metal Build Marketing Team',
        'business': 'Metal Build Marketing',
        'email': 'metalbuildmarketing@gmail.com',
        'phone': '(213) 754-8506',
        'website': 'https://metalbuildmarketing.com/',
        'timezone': 'PST',
        'colleague': 'Carol',
        'location': 'Los Angeles, CA'
    },
    'occusafeserv': {
        'name': 'Natalia Timacheva',
        'business': 'OccuSafe Environmental',
        'email': 'natalia@occusafeserv.ca',
        'phone': '(778) 956-9559',
        'website': 'https://www.occusafeserv.com/',
        'timezone': 'PST',
        'colleague': 'Jessica',
        'location': 'Vernon, BC, Canada'
    },
    'justinveterancleaning': {
        'name': 'Justin Fraser',
        'business': 'Justin Veteran Cleaning Co',
        'email': 'justinveterancleaningco@gmail.com',
        'phone': '(813) 669-8301',
        'website': 'https://veterancleaning.com/',
        'timezone': 'EST',
        'colleague': 'Rose',
        'location': 'Tampa, FL'
    },
    'glowtiquecleaning': {
        'name': 'Glowtique Cleaning Team',
        'business': 'Glowtique Cleaning',
        'email': 'glowtiquecleaning18@gmail.com',
        'phone': '(669) 315-3128',
        'website': 'https://www.glowtiquecleaning.com/',
        'timezone': 'PST',
        'colleague': 'Grace',
        'location': 'San Jose, CA'
    },
    'urbancontractorsnyc': {
        'name': 'Urban Contractors NYC Team',
        'business': 'Urban Contractors NYC',
        'email': 'info@urbancontractorsnyc.com',
        'phone': '(646) 922-9144',
        'website': 'https://www.urbancontractorsnyc.com/',
        'timezone': 'EST',
        'colleague': 'Jinni',
        'location': 'New York, NY'
    },
    'trueshinewindows': {
        'name': 'Liam Grawey',
        'business': 'True Shine Windows',
        'email': 'trueshinewindows25@gmail.com',
        'phone': '(309) 501-5358',
        'website': 'https://www.trueshinewindowcleanings.com/',
        'timezone': 'CST',
        'colleague': 'Janet',
        'location': 'Peoria, IL 61602'
    },
    'metrobrokersmadison': {
        'name': 'John Valenza',
        'business': 'Metro Brokers Madison',
        'email': 'metrojvj@gmail.com',
        'phone': '(608) 221-8455',
        'website': 'https://www.metrobrokersmadison.com/',
        'timezone': 'CST',
        'colleague': 'Curtis',
        'location': 'Madison, WI 53716'
    },
    'asphaltexps': {
        'name': 'Tony Pesce',
        'business': "Réparation d'Asphalte XPS Inc.",
        'email': 'reparationdasphaltexps@gmail.com',
        'phone': '514-972-1137',
        'website': 'https://www.asphaltexps.ca/',
        'timezone': 'EST',
        'colleague': 'Ajmal',
        'location': 'Montreal, QC, Canada'
    },
    'supermariodetailingllc': {
        'name': 'Mario Fonseca',
        'business': 'Super Mario Detailing LLC',
        'email': 'supermarioautodetail@icloud.com',
        'phone': '(626) 221-0524',
        'website': 'https://supermariodetailingllc.com/',
        'colleague': 'Jess'
    },
    'willowcreekminihighlands': {
        'name': 'Willow Smith',
        'business': 'Willow Creek Mini Highlands',
        'email': 'contact@willowcreekminihighlands.com',
        'phone': '+1 214-716-0788',
        'website': 'https://willowcreekminihighlands.com/',
        'colleague': 'Willie'
    },
    'kikisparkleshine': {
        'name': 'Kiki',
        'business': "KiKi's Sparkle & Shine Solutions LLC",
        'phone': '(515) 217-2646',
        'colleague': 'Janice'
    },
    'nicotinefreecigarettes': {
        'name': 'James',
        'business': 'Nicotine Free Cigarettes',
        'phone': '+1 888-817-6653',
        'colleague': 'James'
    },
    'studiorue': {
        'name': 'Studio Rue',
        'business': 'Studio Rue',
        'phone': '210.273.0201',
        'colleague': 'Melissa'
    },
    'summitmotors': {
        'name': 'Summit Motors',
        'business': 'Summit Motors NJ',
        'phone': '(551) 999-5208',
        'website': 'https://www.summitmotorsnj.com/contact-us',
        'colleague': 'Gabrielle'
    },
    'rcmacapital': {
        'name': 'RCMA Capital',
        'business': 'Red Metal Resources / RCMA Capital',
        'phone': '236.513.4776',
        'colleague': 'Vipin'
    },
    'happy_bobas': {
        'name': 'Happy Bobas Team',
        'business': 'Happy Bobas',
        'phone': '+1 773-887-5651',
        'email': 'happybobastea@gmail.com',
        'website': 'https://happybobas.com/',
        'colleague': 'Anna'
    },
    'linda_mowat': {
        'name': 'Linda Mowat',
        'business': "Mowat's Art",
        'phone': '250-545-5627',
        'website': 'https://mowatsart.ca/',
        'colleague': 'Lucy'
    },
    'chakraflowuniversity': {
        'name': 'Victoria Martinez',
        'business': 'Chakra Flow University',
        'email': 'hello@chakraflowuniversity.com',
        'phone': '704-578-0006',
        'website': 'https://www.chakraflowuniversity.com/',
        'colleague': 'Rain'
    },
    'cabrerafamilyconstruction': {
        'name': 'Yosimar Cabrera',
        'business': 'Cabrera Family Construction',
        'email': 'cabreraconstruction100@gmail.com',
        'phone': '(209) 637-1514',
        'website': 'https://cabrerafamilyconstruction.com/'
    },
    'headintheclouds': {
        'name': 'Gabriela',
        'business': 'Head In the Clouds Head Spa',
        'email': 'headintheclouds.headspa@gmail.com',
        'phone': '(775) 771-3725',
        'website': 'https://headinthecloudsheadspa.com/'
    },
    'smrrental': {
        'name': 'Sarah Darling',
        'business': 'SMR Rental',
        'email': 'smr@smrrental.com',
        'phone': '(507) 345-1290',
        'website': 'https://smrrental.com/'
    },
    'trashhounds': {
        'name': 'Lamar Terrell',
        'business': 'Trash Hounds',
        'email': 'lamarterrell87@gmail.com',
        'phone': '(860) 497-9321',
        'website': 'https://trashhoundsct.com/'
    },
    'testequipmentusa': {
        'name': 'Test Equipment USA Team',
        'business': 'Test Equipment USA',
        'email': 'sales@testequipmentusa.com',
        'phone': '(713) 904-4604',
        'website': 'https://testequipmentusa.com/',
        'status': 'lost',
        'do_not_contact': True
    },
    'vehicleinspectors': {
        'name': 'Marc Henderson',
        'business': 'Vehicle Inspectors',
        'email': 'marc@vehicleinspectors.com',
        'phone': '(888) 923-5890',
        'website': 'https://vehicleinspectors.com/',
        'status': 'lost',
        'do_not_contact': True
    },
    'rgelectricsolutionsllc': {
        'name': 'Robertho Leon',
        'business': 'RG Electric Solutions LLC',
        'email': 'rgelectricontractor@gmail.com',
        'phone': '862-334-0210',
        'website': 'https://www.rgelectricsolutionsllc.com/',
        'timezone': 'EST',
        'colleague': 'Mega',
        'location': 'Paterson, NJ'
    },
    'cratingexpress': {
        'name': 'Lea',
        'business': 'Crating Express',
        'email': 'cratingexpress02@gmail.com',
        'phone': '786 558 6007',
        'website': 'https://cratingexpress.com/',
        'timezone': 'EST',
        'colleague': 'Ramu Ver',
        'location': 'Doral, FL'
    },
    'ragstorinses': {
        'name': 'Ellen',
        'business': 'Rags to Rinses Detailing',
        'email': 'rags2rinses419@gmail.com',
        'phone': '(810) 642-4979',
        'website': 'https://ragstorinsespremiumdetailing.com/'
    },
    'humboldtmobilefootcare': {
        'name': 'Eva Pedro',
        'business': 'Humboldt Mobile Foot Care',
        'email': 'myrtletownnails@icloud.com',
        'phone': '(707) 502-2611',
        'website': 'https://humboldtmobilefootcare.com/'
    },
    'mksdevelopment': {
        'name': 'KC',
        'business': 'MKS Development',
        'email': 'kc@mksdevelopment.com',
        'phone': '(212) 925-4500',
        'website': 'https://mksdevelopment.com/',
        'colleague': 'Rada',
        'location': 'Columbus, OH',
        'timezone': 'EST'
    },
    'kcbstitches': {
        'name': 'Rebecca Vause',
        'business': 'KCB Stitches',
        'email': 'kcbpillowsandstuff@gmail.com',
        'phone': '(480) 550-0673',
        'website': 'https://kcbstitches.com/'
    },
    'fixknix': {
        'name': 'AJ Housholder',
        'business': 'QC City Auto (FixKnix)',
        'email': 'aj@intuicodigital.com',
        'phone': 'No Direct #',
        'website': 'https://fixknix.com/'
    },
    'sassybee': {
        'name': 'Kimberly Baker',
        'business': 'Sassy Bee',
        'email': 'kay@shopsassybee.com',
        'phone': '(804) 794-6363',
        'website': 'https://shopsassybee.com/'
    },
    'thebeautyandboudoirstudio': {
        'name': 'Lanett Franko',
        'business': 'The Beauty & Boudoir Studio',
        'email': 'thebeautyandboudoirstudio@gmail.com',
        'phone': '(303) 395-0213',
        'website': 'https://thebeautyandboudoirstudio.com/'
    },
    'checkmatknoxville': {
        'name': 'Kevin-James Gonzalez',
        'business': 'Checkmat Knoxville',
        'email': 'kevinjamesgonzalez@gmail.com',
        'phone': '(855) 765-5255'
    },
    'ronsterbikes': {
        'name': 'Ronster Bikes Team',
        'business': 'Ronster Bikes',
        'email': 'sales@ronsterbikes.com',
        'phone': '+1 (249) 617-8244',
        'website': 'https://ronsterbikes.com/'
    },
    'riverwalksalem': {
        'name': 'Marc Tranos',
        'business': 'Riverwalk Kitchen and Bath',
        'email': 'marc@riverwalksalem.com',
        'phone': '(978) 722-4105',
        'website': 'https://riverwalksalem.com/'
    },
    'dantaraspa': {
        'name': 'Dantara Spa',
        'business': 'Dantara Spa NYC',
        'email': 'info@dantaraspa.com',
        'phone': '(212) 355-6677',
        'website': 'https://www.dantaraspa.com/'
    },
    'raspberryhills': {
        'name': 'Raspberry Hills Team',
        'business': 'Raspberry Hills Farm',
        'website': 'https://raspberryhillsfarm.com/'
    },
    'relincgroup': {
        'name': 'Eclesiaste Chana',
        'business': 'Relinc Group',
        'email': 'info@relincgroup.com',
        'phone': '(405) 465-6840',
        'website': 'https://www.relincgroup.com/',
        'location': 'Oklahoma City, OK',
        'timezone': 'CST'
    },
    'theheatpumpsource': {
        'name': 'Steve Wolff',
        'business': 'The Heat Pump Source',
        'email': 'sales@theheatpumpsource.com',
        'phone': '(928) 457-7167',
        'website': 'https://www.theheatpumpsource.com/',
        'location': 'Show Low, AZ',
        'timezone': 'MST'
    }
}

# Master directory indexing
MASTER_BY_EMAIL = {}
MASTER_BY_DOMAIN = {}
MASTER_BY_SLUG = {}

def norm_email(e: str) -> str:
    if not e: return ''
    e = e.lower().strip()
    e = re.sub(r'\s*@\s*', '@', e)
    e = re.sub(r'\s*\.\s*', '.', e)
    return e

def norm_domain(d: str) -> str:
    if not d: return ''
    d = d.lower().replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
    d = re.sub(r'\s*\.\s*', '.', d)
    return d.split('/')[0].strip()

def load_master_directory():
    if os.path.exists(MASTER_PATH):
        try:
            with open(MASTER_PATH, 'r', encoding='utf-8') as f:
                m_list = json.load(f)
                for m in m_list:
                    em = norm_email(m.get('email'))
                    if em: MASTER_BY_EMAIL[em] = m
                    dom = norm_domain(m.get('website'))
                    if dom: MASTER_BY_DOMAIN[dom] = m
                    c_slug = re.sub(r'[^a-z0-9]', '', (m.get('company') or '').lower())
                    if c_slug: MASTER_BY_SLUG[c_slug] = m
                    n_slug = re.sub(r'[^a-z0-9]', '', (m.get('name') or '').lower())
                    if n_slug: MASTER_BY_SLUG[n_slug] = m
        except Exception as e:
            print(f"Error loading master directory: {e}")

load_master_directory()

def clean_text(s: str) -> str:
    if not s:
        return ''
    s = re.sub(r'[*_`]', '', s)
    s = re.sub(r'\\([^\\])', r'\1', s)
    # Strip emojis without deleting accented non-ASCII letters (e.g. é in Réparation)
    s = re.sub(r'[\U00010000-\U0010ffff]', '', s)
    return ' '.join(s.split()).strip()

def clean_contact_name(raw_name: str) -> str:
    if not raw_name: return ''
    n = clean_text(raw_name)
    # Remove parenthetical notes/titles like (Owner / Maker), (17+ years experience...)
    n = re.sub(r'\s*\([^)]*\)', '', n).strip()
    # Remove professional post-nominals / trailing credentials
    n = re.sub(r',\s*(?:DDS|DVM|ESQ|Esquire|APRN|LLC|Inc\.|JD|MD|PhD).*', '', n, flags=re.I).strip()
    # If separated by slash (e.g. ark dome / Owner), take the name part
    if ' / ' in n:
        parts = n.split(' / ')
        if parts[1].strip().lower() in ['owner', 'maker', 'founder', 'director', 'principal', 'manager']:
            n = parts[0].strip()
        elif parts[0].strip().lower() in ['owner', 'maker', 'founder', 'director', 'principal', 'manager']:
            n = parts[1].strip()
    # Strip & Team suffix if a specific name precedes it (e.g. Ashley & Dream Earth Bowls Team -> Ashley)
    n = re.sub(r'\s*&\s*.*(?:Team|Staff).*', '', n, flags=re.I).strip()
    if n.islower():
        n = n.title()
    return n.strip()

def clean_phone(phone_str: str) -> str:
    if not phone_str:
        return ''
    digits = re.sub(r'[^\d]', '', str(phone_str))
    if digits in ['6452201660', '1234567890']:
        return ''
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    return digits

def format_phone_display(digits: str) -> str:
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) > 10:
        if digits[0] in '23456789' and len(digits) >= 10:
            d = digits[:10]
            return f"({d[:3]}) {d[3:6]}-{d[6:]}"
    return digits

def infer_timezone(location_str: str, phone_str: str, raw_tz: str = None) -> str:
    if raw_tz:
        for tz in ['PST', 'PDT', 'EST', 'EDT', 'CST', 'CDT', 'MST', 'MDT']:
            if tz in raw_tz.upper():
                return tz[:3]
                
    loc_upper = (location_str or '').upper()
    for state, tz in STATE_TIMEZONES.items():
        if re.search(r'\b' + re.escape(state) + r'\b', loc_upper):
            return tz
            
    digits = clean_phone(phone_str)
    if len(digits) >= 10:
        area_code = digits[:3]
        if area_code in AREA_CODE_TIMEZONES:
            return AREA_CODE_TIMEZONES[area_code]
            
    return 'EST'

def get_current_local_time(tz_code: str) -> dict:
    now_utc = datetime.now(timezone.utc)
    tz_offsets = {
        'EST': -4, 'EDT': -4,
        'CST': -5, 'CDT': -5,
        'MST': -6, 'MDT': -6,
        'PST': -7, 'PDT': -7
    }
    offset = tz_offsets.get(tz_code[:3].upper(), -4)
    local_dt = now_utc + timedelta(hours=offset)
    
    hour = local_dt.hour
    is_safe = (9 <= hour < 17) and (local_dt.weekday() < 5)
    
    time_str = local_dt.strftime('%I:%M %p')
    return {
        'time_str': time_str,
        'hour': hour,
        'is_safe': is_safe,
        'day_str': local_dt.strftime('%a'),
        'timezone': tz_code[:3].upper()
    }

def parse_lead_file(filepath: str) -> dict:
    slug = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. Contact / Decision Maker
    name = ''
    name_patterns = [
        r'\*\*(?:Client Contact Name|Contact / Decision Maker|Owner/Contact|Decision Maker|Decision Makers|Contact Name|Contact|Owner|Lead Contact|Name)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Client Contact Name|Contact / Decision Maker|Owner/Contact|Decision Maker|Decision Makers|Contact Name|Contact|Owner|Lead Contact|Name)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
        r'\|\s*Name\s*\|\s*([^\|\n\r]+)',
        r'##\s+[^\|#\n\r]+\|\s*([A-Za-z0-9\.\,\'\& ]+)',
        r'#\s+CALL BRIEFING:\s*[^•\n\r]+[•\-]\s*([A-Za-z0-9\.\,\'\& ]+)',
        r'>\s*\*\*Client\*\*:\s*([^\n\r]+)'
    ]
    for p in name_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_contact_name(m.group(1))
            if val and val.lower() not in ['n/a', 'none', 'unknown', 'field', 'details']:
                name = val
                break

    # 2. Business Name
    biz = ''
    biz_patterns = [
        r'\*\*(?:Business Name|Company Name|Company|Business)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Business Name|Company Name|Company|Business)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
        r'#+\s*(?:Client Dossier:|CALL COPILOT SALES DOSSIER:?|CALL BRIEFING:?|Client Briefing:?)\s*([^\|\n\r•\(\)\-\:\#]+)',
        r'##\s*([^\|\n\r]+)\s*\|',
        r'>\s*\*\*Business\*\*:\s*([^\n\r]+)'
    ]
    for p in biz_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none', 'unknown', 'field', 'details']:
                biz = val
                break

    # 3. Phone
    phone = ''
    phone_patterns = [
        r'\*\*(?:Phone|Primary Phone|Contact Number|Direct Phone|Direct Phones|Store Phone|Studio Phone|Academy Phone|Mobile|Tel|Cell)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Phone|Primary Phone|Contact Number|Direct Phone|Direct Phones|Store Phone|Studio Phone|Academy Phone|Mobile|Tel|Cell)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
    ]
    raw_phone_cell = ''
    for p in phone_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none', 'unknown']:
                raw_phone_cell = val
                break

    if raw_phone_cell:
        # Match standard 10-digit North American phone number first
        m_us = re.search(r'(?:\+?1[\s.-]?)?\(?([2-9][0-9]{2})\)?[\s.-]?([0-9]{3})[\s.-]?([0-9]{4})\b', raw_phone_cell)
        if m_us:
            digits = f"{m_us.group(1)}{m_us.group(2)}{m_us.group(3)}"
            if digits != '1234567890' and digits != '6452201660':
                phone = f"({m_us.group(1)}) {m_us.group(2)}-{m_us.group(3)}"
        else:
            m_intl = re.search(r'(\+?[0-9\-\(\)\. ]{10,20})', raw_phone_cell)
            if m_intl:
                c_d = clean_phone(m_intl.group(1))
                if c_d and c_d not in ['1234567890', '6452201660']:
                    phone = m_intl.group(1).strip()

    if not phone:
        for line in content.splitlines():
            if any(bad in line.lower() for bad in ['assigned rep', 'consultant', 'innovate marketers', 'call me back at', 'direct: +1(645)', 'direct: (645)', 'rep: shiv']):
                continue
            m_line = re.search(r'(?:Phone|Direct|Cell|Tel|Call)[:\s]+(?:\+?1[\s.-]?)?\(?([2-9][0-9]{2})\)?[\s.-]?([0-9]{3})[\s.-]?([0-9]{4})\b', line, re.IGNORECASE)
            if m_line:
                digits = f"{m_line.group(1)}{m_line.group(2)}{m_line.group(3)}"
                if digits not in ['6452201660', '1234567890']:
                    phone = f"({m_line.group(1)}) {m_line.group(2)}-{m_line.group(3)}"
                    break

    # 4. Email
    email = ''
    email_patterns = [
        r'\*\*(?:Primary Email|Contact Email|Email Address|Email)[^:]*?\:?\*\*\s*[:\|]?\s*`?([^\n\r\|`]+)`?',
        r'\|\s*\*\*(?:Primary Email|Contact Email|Email Address|Email)[^:]*?\:?\*\*\s*\|\s*`?([^\n\r\|`]+)`?',
        r'([a-zA-Z0-9_.+-]+\s*@\s*[a-zA-Z0-9-.]+\s*\.\s*[a-zA-Z]{2,})'
    ]
    for p in email_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none']:
                email = norm_email(val)
                break

    # 5. Website
    website = ''
    web_patterns = [
        r'\*\*(?:Website|Domain|Site)[^:]*?\:?\*\*\s*[:\|]?\s*`?([^\n\r\|`]+)`?',
        r'\|\s*\*\*(?:Website|Domain|Site)[^:]*?\:?\*\*\s*\|\s*`?([^\n\r\|`]+)`?',
        r'(https?://[^\s\)\>\|]+)'
    ]
    for p in web_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none']:
                website = re.sub(r'\s*\.\s*', '.', val).strip('/')
                break

    # 6. Location & Timezone
    location = ''
    loc_patterns = [
        r'\*\*(?:Location & Timezone|Location / Timezone|Location|Clinic Address|Shop Address|Office Address|Address|City/State)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Location & Timezone|Location / Timezone|Location|Clinic Address|Shop Address|Office Address|Address|City/State)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
        r'Location[:\s]+([^\n\r\|]+)'
    ]
    for p in loc_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none']:
                location = val
                break

    # 7. Outreach Colleague & Reply
    colleague = ''
    colleague_patterns = [
        r'\*\*(?:Warm Introduction|Outreach Colleague|Colleague Connection|Colleague|Source|Lead Source|Known Relationship|Referrer)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Warm Introduction|Outreach Colleague|Colleague Connection|Colleague|Source|Lead Source|Known Relationship|Referrer)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
        r'colleague\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    ]
    for p in colleague_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val and val.lower() not in ['n/a', 'none']:
                colleague = val
                break

    lead_reply = ''
    reply_patterns = [
        r'\*\*(?:Lead Origin|Reply|Client Reply|Warmth Level|Initial Response)[^:]*?\:?\*\*\s*[:\|]?\s*([^\n\r\|]+)',
        r'\|\s*\*\*(?:Lead Origin|Reply|Client Reply|Warmth Level|Initial Response)[^:]*?\:?\*\*\s*\|\s*([^\n\r\|]+)',
        r'Replied\s*["\']([^"\']+)["\']'
    ]
    for p in reply_patterns:
        m = re.search(p, content, re.IGNORECASE)
        if m:
            val = clean_text(m.group(1))
            if val:
                lead_reply = val
                break

    # Cross-reference with Master Directory and Verified Overrides
    clean_slug = re.sub(r'[^a-z0-9]', '', slug.lower())
    match = MASTER_BY_EMAIL.get(email) or MASTER_BY_DOMAIN.get(norm_domain(website)) or MASTER_BY_SLUG.get(clean_slug)

    if (not phone or not clean_phone(phone)) and match and match.get('phone'):
        phone = match.get('phone')
    if not email and match and match.get('email'):
        email = match.get('email')
    if not website and match and match.get('website'):
        website = match.get('website')
    if (not name or name.lower() in ['n/a', 'unknown', 'none', 'details', 'field']) and match and match.get('name'):
        name = match.get('name')
    if (not biz or biz.lower() in ['n/a', 'unknown', 'none', 'details', 'field']) and match and match.get('company'):
        biz = match.get('company')
    if not location and match and match.get('location'):
        location = match.get('location')

    # Apply Verified Overrides
    if slug in PMS_OVERRIDES:
        ov = PMS_OVERRIDES[slug]
        if ov.get('name'): name = ov['name']
        if ov.get('business'): biz = ov['business']
        if ov.get('phone'): phone = ov['phone']
        if ov.get('email'): email = ov['email']
        if ov.get('website'): website = ov['website']
        if ov.get('colleague'): colleague = ov['colleague']
        if ov.get('location'): location = ov['location']
        if ov.get('timezone'): raw_tz = ov['timezone']

    # Normalize Website URL
    if website:
        if not website.startswith('http://') and not website.startswith('https://'):
            website = 'https://' + website

    # Infer timezone
    raw_tz = ''
    tz_match = re.search(r'\b(PST|PDT|EST|EDT|CST|CDT|MST|MDT)\b', content)
    if tz_match:
        raw_tz = tz_match.group(1)
    if slug in PMS_OVERRIDES and PMS_OVERRIDES[slug].get('timezone'):
        raw_tz = PMS_OVERRIDES[slug]['timezone']
    tz_code = infer_timezone(location, phone, raw_tz)

    # 8. Semrush Metrics
    as_score = ''
    as_m = re.search(r'\*\*Authority Score:?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'Authority Score\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
    if as_m:
        raw_as = clean_text(as_m.group(1))
        m_num = re.search(r'(\d+)\s*(?:/\s*100)?', raw_as)
        as_score = f"{m_num.group(1)} / 100" if m_num else raw_as

    traffic = ''
    tr_m = re.search(r'\*\*(?:Total Organic Traffic|Monthly Organic Traffic|Organic Search Traffic|Organic Traffic):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'Organic (?:Search )?Traffic\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
    if tr_m:
        traffic = clean_text(tr_m.group(1))
        m_tr = re.search(r'([0-9\.,]+(?:\s*[KkMmBb])?)\s*(?:visits?|monthly visits|visits/mo)', traffic, re.I)
        if m_tr:
            traffic = f"{m_tr.group(1)} visits/mo"

    us_share = ''
    us_m = re.search(r'\*\*(?:US Traffic Share|Traffic Share \(US\)|Traffic Share US):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'Traffic Share.*?([0-9]{1,3}\%)', content, re.I)
    if us_m:
        us_share = clean_text(us_m.group(1))

    keywords = ''
    kw_m = re.search(r'\*\*(?:Organic Keywords|Organic Keywords Indexed|Keywords Indexed):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'Organic Keywords\s*[:\|]\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'Keywords Indexed\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
    if kw_m:
        keywords = clean_text(kw_m.group(1))
        m_kw = re.search(r'([0-9\.,]+)\s*(?:keywords?|terms?)', keywords, re.I)
        if m_kw:
            keywords = f"{m_kw.group(1)} keywords"

    ref_domains = ''
    backlinks = ''
    # Support combined backlink/referring domains bullet lines
    comb_m = re.search(r'\*\*(?:Backlink Profile|Backlinks):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I)
    if comb_m:
        comb_val = clean_text(comb_m.group(1))
        bl_match = re.search(r'([0-9\.,]+(?:\s*[KkMmBb])?)\s*(?:backlinks?|links?)', comb_val, re.I)
        rd_match = re.search(r'([0-9\.,]+(?:\s*[KkMmBb])?)\s*referring domains', comb_val, re.I)
        if bl_match:
            backlinks = f"{bl_match.group(1)} links"
        if rd_match:
            ref_domains = f"{rd_match.group(1)} domains"

    if not backlinks:
        bl_m = re.search(r'\*\*(?:Backlinks|Total Backlinks):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
               re.search(r'Backlinks\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
        if bl_m:
            backlinks = clean_text(bl_m.group(1))

    if not ref_domains:
        rd_m = re.search(r'\*\*(?:Referring Domains|Ref\. Domains):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
               re.search(r'Referring Domains\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
        if rd_m:
            ref_domains = clean_text(rd_m.group(1))

    ai_score = ''
    ai_m = re.search(r'\*\*(?:AI Search Visibility|AI Visibility|AI Search Visibility \(AEO\)):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
           re.search(r'AI Search Visibility\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
    if ai_m:
        ai_score = clean_text(ai_m.group(1))

    competitors = ''
    comp_m = re.search(r'\*\*(?:Key Local Competitors|Local Competitors|Competitors):?\*\*\s*[:\|]?\s*([^\|\n\r]+)', content, re.I) or \
             re.search(r'Competitors\s*[:\|]\s*([^\|\n\r]+)', content, re.I)
    if comp_m:
        competitors = clean_text(comp_m.group(1))

    # Core Trap / Bottleneck
    core_trap = ''
    trap_m = re.search(r'Core Trap:\s*([^\n\r]+)', content, re.IGNORECASE) or \
             re.search(r'The Fatal Flaw:\s*([^\n\r]+)', content, re.IGNORECASE) or \
             re.search(r'THE DOMINANT BOTTLENECK:[^\n\r]*\n\n([^\n\r]+)', content, re.IGNORECASE) or \
             re.search(r'Critical Diagnosis & Bottleneck\s*\|\s*\n[^\n]+\|\s*([^\|\n\r]+)', content, re.IGNORECASE)
    if trap_m:
        core_trap = clean_text(trap_m.group(1))
    if not core_trap:
        if us_share and int(re.sub(r'[^\d]', '', us_share) or '100') < 20:
            core_trap = f"Domain has authority ({ref_domains or 'hundreds of'} ref domains), but {us_share} US traffic leak; missing local revenue to competitors."
        elif ref_domains and (keywords and int(re.sub(r'[^\d]', '', keywords) or '0') < 20):
            core_trap = f"{ref_domains} passing authority, but only {keywords} keywords indexed; authority wasted on non-commercial pages."
        else:
            core_trap = f"Authority disconnected from high-intent commercial buyer searches; competitors capturing market share."

    # Multi-pattern screenshot checking
    screenshot_file = ''
    for pattern in [f"{slug}_seo.png", f"{slug}_semrush.png", f"{slug}_clean_crop.png", f"{slug}.png"]:
        if os.path.exists(os.path.join(SCREENSHOTS_DIR, pattern)):
            screenshot_file = pattern
            break
    has_screenshot = bool(screenshot_file)

    # Clean display names
    clean_slug_title = slug.replace('_', ' ').replace('-', ' ').title()
    if not name or name.lower() in ['n/a', 'unknown', 'none', 'field', 'details']:
        name = clean_slug_title
    if not biz or biz.lower() in ['n/a', 'unknown', 'none', 'field', 'details']:
        biz = clean_slug_title

    verified_info = OUTREACH_REGISTRY.get(slug, {})
    verified_colleague = verified_info.get('colleague', '')
    verified_email = verified_info.get('colleague_email', '')
    verified_reply = verified_info.get('lead_reply', '')

    c_raw = colleague.split('(')[0].split('/')[0].strip() if colleague else ''
    if any(b in c_raw.lower() for b in COORDINATOR_BANLIST) or not c_raw:
        colleague_clean = verified_colleague or 'my colleague'
    else:
        colleague_clean = c_raw

    colleague_email = verified_email
    if not colleague_email:
        em_paren = re.search(r'\(([\w\.-]+@[\w\.-]+\.\w+)\)', colleague or '')
        if em_paren:
            colleague_email = em_paren.group(1).strip()
        else:
            em_m = re.search(r'(?:Outreach Email|Outreach|Colleague Email|Sent From)[^:\n]*:\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', content, re.I)
            if em_m:
                colleague_email = em_m.group(1).strip()

    if not lead_reply or lead_reply.lower() in ['replied to outreach', 'warm reply', 'warm lead', 'initial response']:
        if verified_reply:
            lead_reply = verified_reply

    # 9. Scripts with 100% SOP Fallbacks
    live_opener = ''
    opener_m = re.search(r'###\s*Live Call Opener[^\n\r]*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content) or \
               re.search(r'Live Call \(When [^\)]+\):\s*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content)
    if opener_m:
        live_opener = clean_text(opener_m.group(1))
    if not live_opener:
        live_opener = f"Hi {name}, this is Shiv. This is a follow-up call regarding your email reply to {colleague_clean} about your website and SEO problem. I just sent you the diagnostic details to your email. Can we do a quick 5-minute call tomorrow to look at it together?"

    what_is_it_about = ''
    about_m = re.search(r'###\s*If [^\n\r]*asks:?\s*[\*"]*What is it about\?[\*"]*\s*[:\n\r]+>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content, re.IGNORECASE) or \
              re.search(r'If they ask "What is it about\?":\s*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content, re.IGNORECASE) or \
              re.search(r'If he asks "What is this about\?":\s*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content, re.IGNORECASE)
    if about_m:
        what_is_it_about = clean_text(about_m.group(1))
    if not what_is_it_about:
        comp_phrase = f"competitors like {competitors}" if competitors else "local competitors"
        what_is_it_about = f"Your website is not ranking on Google for key buyer searches, and {comp_phrase} are taking all the customers. I can show you what to fix in 5 minutes."

    voicemail = ''
    vm_m = re.search(r'###\s*Voicemail Script[^\n\r]*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content) or \
           re.search(r'Voicemail \(Under 15 seconds\):\s*\n>\s*([^\n\r]+(?:\n>[^\n\r]+)*)', content)
    if vm_m:
        voicemail = clean_text(vm_m.group(1))
    if not voicemail:
        voicemail = f"Hi {name}, this is Shiv. This is a follow-up call regarding your email reply to {colleague_clean} about your website and SEO problem. I just sent the details to your email. Please check your inbox, or call me back at (645) 220-1660. Thank you!"

    # Purge coordinator names from scripts and clean quote markers
    for bad in COORDINATOR_BANLIST:
        pat = re.compile(rf'\b{bad}(?:\s+[a-z]+)?\b', re.IGNORECASE)
        live_opener = pat.sub(colleague_clean, live_opener)
        voicemail = pat.sub(colleague_clean, voicemail)
        what_is_it_about = pat.sub(colleague_clean, what_is_it_about)

    live_opener = re.sub(r'^\s*>\s*', '', live_opener).replace(' > ', ' ').strip()
    voicemail = re.sub(r'^\s*>\s*', '', voicemail).replace(' > ', ' ').strip()

    # 10. Standard Objection Handlers
    objections = [
        {
            "objection": "We already get enough word-of-mouth / referrals.",
            "reframe": f"Referrals are great, but high-intent customers who don't know you yet search Google; competitors are capturing those high-dollar orders right now."
        },
        {
            "objection": "How much does your service cost?",
            "reframe": "Our packages start from $300/mo month-to-month with no long-term contracts. But this 10-minute screen share is 100% free with zero obligation."
        },
        {
            "objection": "Send me an email first.",
            "reframe": f"I already sent the report with your scorecard. Can you check your inbox right now so we can look at it together for 2 minutes?"
        },
        {
            "objection": "We already have an SEO person / agency.",
            "reframe": f"That's great! You can share our diagnostic report directly with your SEO person so they can fix these exact indexation and crawl errors for you."
        }
    ]

    c_digits = clean_phone(phone)
    disp_phone = format_phone_display(c_digits) if c_digits else (phone or 'No Direct #')

    # 11. On Hold / Pause Status
    on_hold = False
    snooze_until = ''
    if re.search(r'(?:ON HOLD|SNOOZED|DO NOT CALL OR EMAIL)', content, re.IGNORECASE):
        on_hold = True
        date_m = re.search(r'(?:until|date:?)\s*([A-Za-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})', content, re.IGNORECASE)
        if date_m:
            snooze_until = date_m.group(1).strip()

    return {
        'slug': slug,
        'name': name,
        'business': biz,
        'phone': disp_phone,
        'clean_phone': c_digits,
        'email': email,
        'website': website,
        'location': location,
        'timezone': tz_code,
        'colleague': colleague_clean,
        'colleague_email': colleague_email,
        'lead_reply': lead_reply,
        'authority_score': as_score,
        'organic_traffic': traffic,
        'us_traffic_share': us_share,
        'organic_keywords': keywords,
        'referring_domains': ref_domains,
        'backlinks': backlinks,
        'ai_score': ai_score,
        'competitors': competitors,
        'core_trap': core_trap,
        'has_screenshot': has_screenshot,
        'screenshot_file': screenshot_file,
        'live_opener': live_opener,
        'what_is_it_about': what_is_it_about,
        'voicemail': voicemail,
        'objections': objections,
        'on_hold': on_hold,
        'snooze_until': snooze_until
    }

def get_all_leads() -> list:
    global OUTREACH_REGISTRY
    if os.path.exists(VERIFIED_OUTREACH_PATH):
        try:
            with open(VERIFIED_OUTREACH_PATH, 'r', encoding='utf-8') as f:
                OUTREACH_REGISTRY = json.load(f)
        except Exception:
            pass

    files = glob.glob(os.path.join(LEADS_DIR, '*.md'))
    leads = []
    seen_emails = set()
    seen_websites = set()

    for f in sorted(files):
        try:
            lead = parse_lead_file(f)
            # Avoid redundant duplicate dossier between centredental and centredentalnyc
            if lead['slug'] == 'centredental' and os.path.exists(os.path.join(LEADS_DIR, 'centredentalnyc.md')):
                continue
            leads.append(lead)
        except Exception as e:
            print(f"Error parsing {f}: {e}")
    return leads
