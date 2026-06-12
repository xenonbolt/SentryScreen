"""
generate_dataset.py — Synthetic Adverse Media Dataset Generator
================================================================
Generates 200 realistic adverse media records across 20 entities,
9 risk categories, and multiple severity levels. Run once to create
the dataset file used by the retrieval agent.

Usage:
    python -m app.data.generate_dataset
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ── Seed for reproducibility ──────────────────────────────────────────────────
random.seed(42)

OUTPUT_FILE = Path(__file__).parent / "synthetic_dataset.json"

# ── Entity definitions ────────────────────────────────────────────────────────
ENTITIES: list[dict] = [
    # High-risk companies
    {"name": "Nexum Capital Partners",    "type": "company", "country": "Cayman Islands",
     "categories": ["money_laundering", "fraud", "sanctions"],       "severity_bias": "high"},
    {"name": "Viktor Dragan",             "type": "person",  "country": "Serbia",
     "categories": ["bribery", "money_laundering", "fraud"],         "severity_bias": "critical"},
    {"name": "Meridian Resources Ltd",    "type": "company", "country": "Nigeria",
     "categories": ["environmental", "bribery", "human_rights"],     "severity_bias": "high"},
    {"name": "GlobalTrust Banking Group", "type": "company", "country": "Switzerland",
     "categories": ["money_laundering", "tax_evasion", "sanctions"], "severity_bias": "critical"},
    {"name": "Dmitri Volkov",             "type": "person",  "country": "Russia",
     "categories": ["sanctions", "fraud", "money_laundering"],       "severity_bias": "critical"},
    # Medium-risk entities
    {"name": "Pacific Rim Ventures",      "type": "company", "country": "Singapore",
     "categories": ["insider_trading", "regulatory", "fraud"],       "severity_bias": "medium"},
    {"name": "Chen Wei Technologies",     "type": "company", "country": "China",
     "categories": ["cybercrime", "regulatory", "sanctions"],        "severity_bias": "high"},
    {"name": "Silvano Carbone",           "type": "person",  "country": "Italy",
     "categories": ["tax_evasion", "bribery", "fraud"],              "severity_bias": "high"},
    {"name": "Atlas Mining Corporation",  "type": "company", "country": "DRC",
     "categories": ["human_rights", "environmental", "bribery"],     "severity_bias": "high"},
    {"name": "Ibrahim Al-Rashidi",        "type": "person",  "country": "UAE",
     "categories": ["terrorism_financing", "money_laundering"],      "severity_bias": "critical"},
    # Lower-risk entities
    {"name": "Quantum Financial Services","type": "company", "country": "Luxembourg",
     "categories": ["regulatory", "tax_evasion"],                    "severity_bias": "medium"},
    {"name": "Elena Marchetti",           "type": "person",  "country": "Italy",
     "categories": ["insider_trading", "fraud"],                     "severity_bias": "medium"},
    {"name": "Redstone Energy Group",     "type": "company", "country": "USA",
     "categories": ["environmental", "regulatory"],                  "severity_bias": "medium"},
    {"name": "Tariq Hassan",              "type": "person",  "country": "Pakistan",
     "categories": ["fraud", "money_laundering"],                    "severity_bias": "high"},
    {"name": "Oceanic Shipping International","type":"company","country": "Panama",
     "categories": ["sanctions", "money_laundering"],                "severity_bias": "high"},
    {"name": "Marcus Petrov",             "type": "person",  "country": "Bulgaria",
     "categories": ["cybercrime", "fraud"],                          "severity_bias": "medium"},
    {"name": "Continental Pharma Ltd",    "type": "company", "country": "India",
     "categories": ["regulatory", "fraud", "bribery"],               "severity_bias": "medium"},
    {"name": "Fatima Al-Zahra",           "type": "person",  "country": "Morocco",
     "categories": ["terrorism_financing", "fraud"],                 "severity_bias": "high"},
    {"name": "Pinnacle Investment Holdings","type":"company", "country": "Bahamas",
     "categories": ["money_laundering", "tax_evasion", "fraud"],     "severity_bias": "high"},
    {"name": "Amara Okonkwo",             "type": "person",  "country": "Ghana",
     "categories": ["bribery", "fraud"],                             "severity_bias": "medium"},
]

# ── Sources ───────────────────────────────────────────────────────────────────
SOURCES = [
    "Reuters",  "Bloomberg",  "Financial Times",  "The Guardian",
    "OCCRP",    "Le Monde",   "Süddeutsche Zeitung", "The Economist",
    "South China Morning Post", "Wall Street Journal",
    "BBC News", "Associated Press", "Al Jazeera",
    "Transparency International Reports", "FATF Bulletin",
    "Europol Press Release", "US DoJ Press Release",
    "UK Serious Fraud Office", "Swiss FINMA Disclosure",
]

# ── Category-specific article templates ──────────────────────────────────────
TEMPLATES: dict[str, list[dict]] = {
    "fraud": [
        {
            "title": "{entity} Faces SEC Probe Over Alleged Securities Fraud Scheme",
            "text": (
                "{entity} is under investigation by securities regulators following allegations "
                "of systematic misrepresentation of financial statements to investors. "
                "Prosecutors allege that senior executives at {entity} deliberately inflated "
                "revenue figures by approximately ${amount}M over a three-year period, "
                "misleading pension funds and retail investors. Whistleblower testimony has "
                "implicated the CFO and two board members. Regulators have frozen assets pending "
                "a full forensic audit. Former employees describe a 'culture of deception' where "
                "accurate reporting was actively discouraged. The company denies wrongdoing and "
                "has retained criminal defense counsel. Class-action lawsuits have been filed "
                "by shareholder groups in multiple jurisdictions."
            ),
        },
        {
            "title": "Victims Accuse {entity} of Running Elaborate Ponzi Scheme",
            "text": (
                "Hundreds of investors claim they were defrauded by {entity} in what prosecutors "
                "describe as a sophisticated Ponzi scheme that operated for over five years. "
                "Alleged losses exceed ${amount}M. Court documents reveal that {entity} used "
                "funds from new investors to pay fictitious 'returns' to earlier participants, "
                "while siphoning tens of millions into offshore accounts in the Cayman Islands "
                "and Liechtenstein. Victims include retirees, charities, and municipal pension "
                "funds. Arrest warrants have been issued. The scheme reportedly collapsed when "
                "redemption requests outpaced incoming capital during a market downturn."
            ),
        },
        {
            "title": "{entity} Director Convicted of Wire Fraud and Bank Fraud",
            "text": (
                "A federal jury returned guilty verdicts on 14 counts of wire fraud and bank "
                "fraud against a senior director at {entity}. The conviction follows a two-year "
                "investigation that uncovered a scheme to defraud banks through falsified loan "
                "applications and fabricated collateral documentation. The defendant faces a "
                "maximum sentence of 20 years. Prosecutors presented evidence of over "
                "${amount}M in fraudulent proceeds channelled through shell companies. "
                "{entity} has stated it is cooperating with authorities and has terminated "
                "the convicted individual's employment pending appeal."
            ),
        },
    ],
    "money_laundering": [
        {
            "title": "{entity} Implicated in Major Money Laundering Operation, Assets Seized",
            "text": (
                "Law enforcement authorities across three jurisdictions have seized assets "
                "linked to {entity} following evidence of extensive money laundering activity. "
                "Investigators allege that {entity} processed over ${amount}M in criminal "
                "proceeds through a complex web of shell companies, cryptocurrency exchanges, "
                "and correspondent banking relationships. The operation, codenamed 'Clean Sweep', "
                "involved coordination between Europol, FinCEN, and national financial "
                "intelligence units. Internal compliance staff reportedly raised concerns "
                "that were ignored by management. Several executives have been placed under "
                "travel bans and their personal accounts frozen. The entity faces potential "
                "deregistration by its primary regulator."
            ),
        },
        {
            "title": "FATF Flags {entity} in Annual High-Risk Entities Report",
            "text": (
                "The Financial Action Task Force has included {entity} in its latest report "
                "on entities demonstrating significant money laundering red flags. The report "
                "cites unusual transaction patterns, including high-velocity cash movements, "
                "unexplained wealth accumulation, and extensive use of nominee structures. "
                "{entity} reportedly conducted transactions worth ${amount}M with jurisdictions "
                "on the FATF grey list without adequate due diligence. AML compliance failures "
                "date back at least four years. Banks are advised to apply enhanced due "
                "diligence measures for any transactions involving {entity}. "
                "Corresponding financial institutions face their own regulatory scrutiny."
            ),
        },
    ],
    "sanctions": [
        {
            "title": "{entity} Added to OFAC Specially Designated Nationals List",
            "text": (
                "The U.S. Treasury Department's Office of Foreign Assets Control (OFAC) has "
                "designated {entity} on the Specially Designated Nationals and Blocked Persons "
                "List. The designation cites {entity}'s alleged role in facilitating financial "
                "transactions on behalf of sanctioned governments and entities. U.S. persons "
                "are now prohibited from engaging in any transactions with {entity}, and all "
                "assets subject to U.S. jurisdiction are to be blocked. The action was "
                "coordinated with the EU Council, which imposed parallel asset freezes. "
                "{entity} has 60 days to seek reconsideration but has not publicly responded "
                "to the designation. Several correspondent banks have already terminated "
                "their relationships effective immediately."
            ),
        },
        {
            "title": "EU Sanctions {entity} for Circumventing Russia Export Controls",
            "text": (
                "The European Union has imposed targeted sanctions on {entity} for its role in "
                "helping circumvent export controls introduced following the 2022 Russia "
                "sanctions regime. Intelligence reports indicate {entity} acted as a "
                "transhipment hub, re-exporting dual-use goods and military-grade electronics "
                "to Russian state entities via third-country intermediaries. The sanctions "
                "include asset freezes, travel bans on key executives, and prohibitions on "
                "EU entities providing financial, technical, or advisory services to {entity}. "
                "The UK and Canada have issued parallel designations. {entity} processed an "
                "estimated ${amount}M in sanctioned goods over 18 months."
            ),
        },
    ],
    "bribery": [
        {
            "title": "Anti-Corruption Probe Implicates {entity} in $${amount}M Bribery Scheme",
            "text": (
                "A multi-year anti-corruption investigation has uncovered evidence that "
                "{entity} paid systematic bribes totalling ${amount}M to government officials "
                "across multiple countries to secure lucrative public contracts. The payments "
                "were concealed through a network of consultancy agreements and offshore "
                "intermediaries, a technique described by prosecutors as 'corruption-as-a-service'. "
                "Internal communications obtained by investigators contain explicit references "
                "to corrupt payments described using code words. The FCPA violations alone "
                "carry penalties in the hundreds of millions. {entity} has entered into "
                "deferred prosecution agreement negotiations with the Department of Justice."
            ),
        },
        {
            "title": "{entity} Official Arrested for Bribing Customs and Regulatory Officers",
            "text": (
                "A senior procurement official at {entity} has been arrested following a "
                "sting operation that captured on camera the transfer of cash bribes to "
                "customs and regulatory enforcement officers. The official allegedly operated "
                "a systematic scheme to circumvent import restrictions and safety inspections, "
                "costing the state an estimated ${amount}M in lost revenue. The arrest is "
                "part of a wider investigation that has already implicated three government "
                "ministers. {entity} shares dropped 18% on the news. Regulators have "
                "launched a fitness and propriety review of the entire senior leadership team."
            ),
        },
    ],
    "tax_evasion": [
        {
            "title": "Pandora Papers Reveal {entity}'s Offshore Tax Evasion Network",
            "text": (
                "Documents obtained by the International Consortium of Investigative "
                "Journalists (ICIJ) as part of the Pandora Papers leak reveal that {entity} "
                "maintained a sophisticated network of offshore shell companies in the British "
                "Virgin Islands, Panama, and Seychelles to conceal taxable income. The leaked "
                "files indicate that approximately ${amount}M in profits were shifted offshore "
                "through transfer pricing manipulation and intra-group royalty payments. "
                "Tax authorities in four countries have launched investigations. {entity}'s "
                "domestic tax payments are alleged to represent a fraction of its true "
                "liability. Several executives are named as beneficial owners of the "
                "offshore structures."
            ),
        },
        {
            "title": "{entity} Ordered to Pay ${amount}M in Back Taxes After Hidden Account Exposed",
            "text": (
                "A tax tribunal has ordered {entity} to pay ${amount}M in back taxes, "
                "interest, and penalties following the discovery of undisclosed foreign "
                "bank accounts and off-balance-sheet income streams. The concealment was "
                "uncovered through international information exchange under the Common "
                "Reporting Standard. {entity} had failed to declare income from overseas "
                "operations for seven consecutive years, a pattern investigators describe "
                "as intentional rather than accidental. Criminal charges for tax fraud "
                "are being considered. The case is expected to set a precedent for similar "
                "enforcement actions across the sector."
            ),
        },
    ],
    "cybercrime": [
        {
            "title": "{entity} Accused of State-Sponsored Cyber Espionage Campaign",
            "text": (
                "Cybersecurity researchers and government intelligence agencies have attributed "
                "a sophisticated cyber espionage campaign to actors linked to {entity}. "
                "The campaign, active for at least two years, targeted critical infrastructure, "
                "defence contractors, and financial institutions across NATO member states. "
                "Techniques included spear-phishing, zero-day exploitation, and supply chain "
                "attacks. Data exfiltration is estimated to have compromised ${amount}M worth "
                "of intellectual property. {entity} has been placed on a restricted entities "
                "list prohibiting government contractors from using its software or services. "
                "Technical indicators of compromise have been shared with national CERTs."
            ),
        },
        {
            "title": "Data Breach at {entity} Exposes Millions of Customer Records",
            "text": (
                "A massive data breach at {entity} has exposed personally identifiable "
                "information of over {amount} million customers, including financial data, "
                "identity documents, and health records. Security researchers allege that "
                "the breach resulted from wilful neglect of basic cybersecurity controls "
                "over an extended period. Regulators have opened investigations under GDPR "
                "and domestic data protection laws. Maximum fines could reach €{amount}M. "
                "Class-action lawsuits have been filed in multiple jurisdictions. "
                "{entity} delayed breach notification by several months, potentially "
                "compounding regulatory penalties. The CEO has resigned amid the fallout."
            ),
        },
    ],
    "environmental": [
        {
            "title": "{entity} Faces Criminal Charges Over Illegal Dumping of Toxic Waste",
            "text": (
                "Environmental prosecutors have filed criminal charges against {entity} "
                "after evidence emerged of systematic illegal dumping of hazardous waste "
                "in protected waterways and wildlife reserves. Contamination has rendered "
                "the water supply unsafe for communities covering an estimated population "
                "of {amount}0,000 people. Environmental testing reveals heavy metal "
                "concentrations at {amount}00 times the legal limit. The cleanup bill is "
                "estimated at ${amount}M with full remediation expected to take a decade. "
                "{entity} continued dumping activities despite receiving regulatory warnings. "
                "Whistleblowers allege that senior management was fully aware of the practice."
            ),
        },
        {
            "title": "Regulator Fines {entity} ${amount}M for Repeated Environmental Violations",
            "text": (
                "The environmental regulator has imposed a record fine of ${amount}M on "
                "{entity} for a pattern of environmental violations spanning five years. "
                "The violations include illegal emissions exceeding permitted levels by "
                "factors of up to 200%, unlicensed waste disposal, and failure to implement "
                "court-mandated remediation measures. {entity} had previously received "
                "14 warning notices and two smaller fines, all of which were contested. "
                "The regulator described the violations as 'wilful and systematic'. "
                "A corporate suspension order has been issued. NGOs are pursuing separate "
                "civil litigation on behalf of affected communities."
            ),
        },
    ],
    "human_rights": [
        {
            "title": "UN Report Links {entity} to Forced Labour in Supply Chain",
            "text": (
                "A United Nations Special Rapporteur report has documented credible evidence "
                "linking {entity}'s supply chain to forced labour practices in at least three "
                "countries. The report describes conditions including wage theft, passport "
                "confiscation, physical coercion, and denial of freedom of movement. "
                "{entity} sourced materials worth an estimated ${amount}M annually from "
                "facilities where these conditions were documented. Despite having a "
                "'zero-tolerance' forced labour policy, audits appear to have been "
                "superficial or falsified. Institutional investors have called for "
                "an emergency board review. Import authorities in the US and UK are "
                "considering bans on {entity}'s products."
            ),
        },
        {
            "title": "{entity} Executives Sued for Complicity in Human Rights Abuses",
            "text": (
                "A class action lawsuit has been filed against senior executives of {entity} "
                "for alleged complicity in human rights abuses committed against indigenous "
                "communities affected by the company's operations. Plaintiffs allege that "
                "{entity} funded and directed security forces that committed violent acts "
                "against peaceful protesters, resulting in deaths and serious injuries. "
                "Internal documents reportedly show executive-level awareness of the "
                "security operations. {entity} operations have been suspended by the "
                "host government pending investigation. Asset freezes have been sought "
                "against named executives in multiple jurisdictions."
            ),
        },
    ],
    "terrorism_financing": [
        {
            "title": "INTERPOL Links {entity} to Terrorism Financing Network",
            "text": (
                "INTERPOL and national counter-terrorism units have identified {entity} as "
                "a key node in an international terrorism financing network. Intelligence "
                "assessments indicate that {entity} facilitated the transfer of approximately "
                "${amount}M to proscribed terrorist organisations through hawala networks "
                "and cryptocurrency transactions. The entity is alleged to have knowingly "
                "provided financial services to individuals on multiple terrorism watch lists. "
                "An emergency designation under counter-terrorism financing laws has been "
                "issued, with immediate asset freezes and travel bans for associated "
                "individuals. Law enforcement agencies in 12 countries are coordinating "
                "the investigation."
            ),
        },
        {
            "title": "{entity} Accounts Frozen in Counter-Terror Financing Operation",
            "text": (
                "Authorities have frozen all accounts and assets associated with {entity} "
                "following evidence of transactions linked to terrorist financing. Court "
                "documents filed by prosecutors describe a pattern of structured cash "
                "deposits, cryptocurrency mixing, and cross-border wire transfers designed "
                "to conceal the ultimate beneficiaries — individuals and organisations "
                "designated as terrorist entities under UN Security Council Resolution 1267. "
                "The principal of {entity} is alleged to have personally directed transfers "
                "worth ${amount}M. International arrest warrants have been issued. "
                "Financial institutions are required to report any transactions with the entity."
            ),
        },
    ],
    "regulatory": [
        {
            "title": "Regulator Revokes {entity}'s Operating Licence Following Compliance Failures",
            "text": (
                "The financial services regulator has revoked the operating licence of "
                "{entity} following a comprehensive compliance review that uncovered systemic "
                "failures in AML controls, customer due diligence, and transaction monitoring. "
                "Examiners found that {entity} had processed transactions totalling "
                "${amount}M without adequate KYC documentation, failed to file required "
                "suspicious activity reports, and maintained inaccurate beneficial ownership "
                "records. The regulator described the compliance function as 'wholly inadequate'. "
                "{entity} has 30 days to appeal. Customers are advised to transfer funds "
                "immediately, as operations must wind down within 90 days."
            ),
        },
        {
            "title": "{entity} Under Investigation for Market Manipulation by Securities Regulator",
            "text": (
                "The securities regulator has launched a formal investigation into {entity} "
                "following allegations of coordinated market manipulation across multiple "
                "securities. The investigation was triggered by unusual trading patterns "
                "preceding several significant corporate announcements. Investigators are "
                "examining whether {entity} exploited material non-public information and "
                "used wash trades and spoofing to artificially influence prices. Preliminary "
                "analysis suggests profits of up to ${amount}M from the alleged manipulations. "
                "{entity}'s trading privileges have been suspended pending the outcome. "
                "Multiple individuals have been questioned under caution."
            ),
        },
    ],
    "insider_trading": [
        {
            "title": "{entity} Director Arrested for Insider Trading Ahead of Major Acquisition",
            "text": (
                "Securities enforcement officers have arrested a senior director of {entity} "
                "on charges of insider trading following their purchase of ${amount}M in "
                "call options two weeks before the announcement of a major acquisition. "
                "The trades generated alleged profits of over ${amount}M and were made using "
                "accounts belonging to family members and close associates to evade detection. "
                "Digital forensics recovered communications showing the director shared "
                "material non-public information with at least four other individuals. "
                "Charges have been filed against all involved parties. The case has prompted "
                "a full review of {entity}'s information security and trading policies."
            ),
        },
        {
            "title": "SEC Charges {entity} Employees With Insider Trading Ring",
            "text": (
                "The Securities and Exchange Commission has charged seven employees of "
                "{entity} with participating in an insider trading ring that exploited "
                "confidential mergers and acquisitions intelligence over three years. "
                "The employees allegedly shared advance information on upcoming deals "
                "through encrypted messaging apps, with trades generating combined profits "
                "of approximately ${amount}M. The SEC's market analysis tools detected "
                "systematic unusual options activity preceding announcements. {entity} "
                "faces reputational damage and potential regulatory sanctions for failing "
                "to maintain adequate information barriers. Civil penalty proceedings "
                "are also underway."
            ),
        },
    ],
}

SEVERITY_OPTIONS: dict[str, list[str]] = {
    "critical": ["critical"],
    "high":     ["high", "critical"],
    "medium":   ["medium", "high"],
    "low":      ["low", "medium"],
}


def _random_date(start_year: int = 2019, end_year: int = 2025) -> str:
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    random_day = start + timedelta(days=random.randint(0, delta.days))
    return random_day.strftime("%Y-%m-%d")


def _pick_severity(bias: str) -> str:
    opts = SEVERITY_OPTIONS.get(bias, ["medium"])
    return random.choice(opts)


def generate_records() -> list[dict]:
    records: list[dict] = []
    amounts = [5, 12, 25, 50, 75, 100, 150, 200, 350, 500, 780]

    for entity in ENTITIES:
        # How many articles per entity (aim for 200 total across 20 entities ≈ 10 each)
        n_articles = random.randint(8, 12)
        # Pool of categories available for this entity
        cat_pool = entity["categories"] * 3  # repeat to allow multiple articles per cat

        for i in range(n_articles):
            category = random.choice(cat_pool)
            templates_for_cat = TEMPLATES.get(category, TEMPLATES["fraud"])
            template = random.choice(templates_for_cat)
            amount = random.choice(amounts)

            title = template["title"].format(entity=entity["name"], amount=amount)
            text  = template["text"].format(entity=entity["name"], amount=amount)

            severity = _pick_severity(entity["severity_bias"])

            records.append({
                "id":             str(uuid.uuid4()),
                "entity_name":    entity["name"],
                "entity_type":    entity["type"],
                "article_title":  title,
                "article_text":   text,
                "source":         random.choice(SOURCES),
                "published_date": _random_date(),
                "category":       category,
                "severity_label": severity,
                "country":        entity["country"],
            })

    # Shuffle to avoid entity clustering
    random.shuffle(records)

    # Trim / pad to exactly 200
    if len(records) > 200:
        records = records[:200]

    return records


def main() -> None:
    print("Generating synthetic adverse media dataset...")
    records = generate_records()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"✓  Generated {len(records)} records → {OUTPUT_FILE}")

    # Quick stats
    from collections import Counter
    cats = Counter(r["category"] for r in records)
    sevs = Counter(r["severity_label"] for r in records)
    ents = len(set(r["entity_name"] for r in records))
    print(f"   Entities: {ents} | Categories: {dict(cats)} | Severities: {dict(sevs)}")


if __name__ == "__main__":
    main()
