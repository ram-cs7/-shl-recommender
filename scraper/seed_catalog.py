"""
Seed catalog builder.

If the scraper cannot reach shl.com (firewall, JS rendering, etc.), this
script writes a known-good starter catalog derived from SHL's publicly
documented Individual Test Solutions.

Run AFTER attempting the real scraper:
    python -m scraper.seed_catalog           # writes data/catalog.json only if missing
    python -m scraper.seed_catalog --force   # overwrites existing catalog.json
"""

import argparse
import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "catalog.json"

BASE = "https://www.shl.com/solutions/products"

SEED: list[dict] = [
    # ── Ability / Aptitude ─────────────────────────────────────────────────
    {
        "name": "Verify Numerical Reasoning",
        "url": f"{BASE}/verify-numerical-reasoning/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Measures the ability to understand, interpret and draw logical conclusions "
            "from numerical and statistical data presented in graphs, charts and tables. "
            "Suitable for roles requiring data analysis and financial interpretation."
        ),
        "duration": "17–25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "Yes",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["numerical reasoning", "data interpretation", "analytical thinking"],
        "tags": ["cognitive", "ability", "numerical", "quantitative", "finance", "analyst"],
    },
    {
        "name": "Verify Verbal Reasoning",
        "url": f"{BASE}/verify-verbal-reasoning/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Assesses the ability to understand and evaluate written information and "
            "draw correct conclusions. Critical for roles requiring strong written "
            "communication and comprehension of complex documents."
        ),
        "duration": "17–19 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "Yes",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["verbal reasoning", "communication", "comprehension"],
        "tags": ["cognitive", "ability", "verbal", "reading", "comprehension"],
    },
    {
        "name": "Verify Inductive Reasoning",
        "url": f"{BASE}/verify-inductive-reasoning/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Measures the ability to identify patterns, relationships and trends in "
            "abstract information. Useful for assessing general problem-solving and "
            "learning potential across a wide range of roles."
        ),
        "duration": "24–25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "Yes",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["abstract reasoning", "problem-solving", "pattern recognition"],
        "tags": ["cognitive", "ability", "inductive", "abstract", "logic", "developer", "engineer"],
    },
    {
        "name": "Verify Deductive Reasoning",
        "url": f"{BASE}/verify-deductive-reasoning/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Assesses the ability to draw logical conclusions from sets of rules and "
            "premises. Relevant for roles in law, compliance, engineering, and any "
            "position requiring structured logical thinking."
        ),
        "duration": "20 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["logical reasoning", "rule application", "analytical thinking"],
        "tags": ["cognitive", "ability", "deductive", "logic", "compliance", "legal"],
    },
    {
        "name": "Verify Checking",
        "url": f"{BASE}/verify-checking/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Measures accuracy and speed in checking data across tables, codes and "
            "text. Designed for administrative, data-entry and operations roles where "
            "attention to detail is critical."
        ),
        "duration": "12 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Entry", "Frontline", "Professional"],
        "competencies": ["attention to detail", "accuracy", "data checking"],
        "tags": ["cognitive", "ability", "checking", "accuracy", "admin", "clerical", "operations"],
    },
    {
        "name": "Verify Mechanical Comprehension",
        "url": f"{BASE}/verify-mechanical-comprehension/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Evaluates understanding of mechanical concepts and physical principles. "
            "Suited for engineering, manufacturing, technical and maintenance roles."
        ),
        "duration": "20 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Entry", "Frontline", "Professional"],
        "competencies": ["mechanical reasoning", "technical aptitude", "physics principles"],
        "tags": ["cognitive", "ability", "mechanical", "engineering", "technical", "manufacturing"],
    },
    {
        "name": "Verify Calculation",
        "url": f"{BASE}/verify-calculation/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Assesses the ability to perform arithmetic calculations accurately and "
            "quickly. Suitable for roles in finance, accounting, retail and customer service."
        ),
        "duration": "10 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Entry", "Frontline", "Professional"],
        "competencies": ["numerical calculation", "accuracy", "speed"],
        "tags": ["cognitive", "ability", "calculation", "arithmetic", "finance", "retail"],
    },
    {
        "name": "General Ability Assessment (GAA)",
        "url": f"{BASE}/general-ability-assessment/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "A broad measure of cognitive ability combining numerical, verbal and "
            "inductive reasoning. Provides a single general mental ability score for "
            "high-volume screening across many job families."
        ),
        "duration": "36 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["general intelligence", "learning agility", "problem-solving"],
        "tags": ["cognitive", "ability", "general", "numerical", "verbal", "inductive", "screening"],
    },
    {
        "name": "Verify Spatial Reasoning",
        "url": f"{BASE}/verify-spatial-reasoning/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Measures the ability to visualise and manipulate shapes and objects in "
            "two and three dimensions. Key for engineering, design, architecture and "
            "technical roles."
        ),
        "duration": "25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional"],
        "competencies": ["spatial reasoning", "3D visualisation", "technical aptitude"],
        "tags": ["cognitive", "ability", "spatial", "engineering", "design", "architecture"],
    },
    # ── Personality / Behavioural ──────────────────────────────────────────
    {
        "name": "OPQ32",
        "url": f"{BASE}/opq32/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "The Occupational Personality Questionnaire measures 32 dimensions of "
            "personality relevant to work performance, leadership potential and "
            "interpersonal style. The gold-standard personality tool for selection "
            "and development across all professional levels."
        ),
        "duration": "25–45 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional", "Manager", "Director", "Executive"],
        "competencies": ["leadership", "teamwork", "communication", "resilience",
                         "conscientiousness", "interpersonal skills"],
        "tags": ["personality", "behavioural", "OPQ", "leadership", "development",
                 "sales", "manager", "stakeholder", "culture fit"],
    },
    {
        "name": "OPQ32r",
        "url": f"{BASE}/opq32r/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "A shorter, report-only version of OPQ32 that delivers the same 32-scale "
            "profile with a reduced item set. Balances depth with candidate experience "
            "for high-volume hiring scenarios."
        ),
        "duration": "20–30 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional", "Manager"],
        "competencies": ["leadership", "teamwork", "communication", "resilience"],
        "tags": ["personality", "behavioural", "OPQ", "leadership", "sales", "manager"],
    },
    {
        "name": "Motivation Questionnaire (MQ)",
        "url": f"{BASE}/motivation-questionnaire-mq/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "Explores 18 dimensions of work motivation to understand what energises "
            "and engages an individual. Invaluable for assessing cultural fit, role "
            "alignment and long-term retention risk."
        ),
        "duration": "25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Professional", "Manager", "Director"],
        "competencies": ["motivation", "engagement", "culture fit", "values alignment"],
        "tags": ["personality", "motivation", "engagement", "retention", "culture", "values"],
    },
    {
        "name": "Global Skills Assessment (GSA)",
        "url": f"{BASE}/global-skills-assessment/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "A game-based behavioural assessment that measures cognitive and "
            "personality traits through immersive tasks. Provides an engaging "
            "candidate experience while delivering reliable trait scores."
        ),
        "duration": "20–25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate", "Entry", "Frontline"],
        "competencies": ["problem-solving", "attention to detail", "resilience", "adaptability"],
        "tags": ["personality", "game-based", "cognitive", "engagement", "graduate", "volume hiring"],
    },
    # ── Knowledge / Skills (Technical) ────────────────────────────────────
    {
        "name": "Java 8 (New)",
        "url": f"{BASE}/java-8-new/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Assesses knowledge and practical skills in Java 8 including streams, "
            "lambdas, generics and OOP principles. For mid-to-senior Java developer "
            "hiring."
        ),
        "duration": "40 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["Java programming", "object-oriented design", "software development"],
        "tags": ["technical", "Java", "developer", "programming", "coding", "software engineer"],
    },
    {
        "name": "Python (New)",
        "url": f"{BASE}/python-new/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Tests Python proficiency including data structures, standard libraries, "
            "object-oriented and functional programming patterns. Suitable for data "
            "engineers, backend and ML roles."
        ),
        "duration": "35–40 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["Python programming", "data structures", "software development"],
        "tags": ["technical", "Python", "developer", "programming", "data", "ML", "backend"],
    },
    {
        "name": ".NET Framework 4.5",
        "url": f"{BASE}/net-framework-4-5/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Covers C# and .NET ecosystem knowledge: LINQ, async/await, ASP.NET and "
            "the CLR. For .NET developer and architect roles."
        ),
        "duration": "40 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": [".NET programming", "C#", "software development"],
        "tags": ["technical", ".NET", "C#", "developer", "programming", "Microsoft"],
    },
    {
        "name": "SQL (New)",
        "url": f"{BASE}/sql-new/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Evaluates SQL proficiency including joins, aggregations, subqueries, "
            "indexes and query optimisation. Essential for analyst, DBA and "
            "data-engineering roles."
        ),
        "duration": "30 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["SQL", "database querying", "data analysis"],
        "tags": ["technical", "SQL", "database", "data analyst", "DBA", "data engineer"],
    },
    {
        "name": "JavaScript (New)",
        "url": f"{BASE}/javascript-new/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Tests modern JavaScript including ES6+, async programming, DOM "
            "manipulation and core framework concepts. For frontend and full-stack "
            "developer roles."
        ),
        "duration": "35 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["JavaScript", "frontend development", "software development"],
        "tags": ["technical", "JavaScript", "JS", "developer", "frontend", "full-stack", "web"],
    },
    {
        "name": "Microsoft Excel (Advanced)",
        "url": f"{BASE}/microsoft-excel-advanced/",
        "test_type": "K",
        "test_type_label": "Knowledge / Skills",
        "description": (
            "Assesses advanced Excel skills: complex formulas, pivot tables, VBA "
            "macros and data modelling. Critical for finance, operations and "
            "analyst roles."
        ),
        "duration": "30 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["Excel", "data analysis", "spreadsheet modelling"],
        "tags": ["technical", "Excel", "Microsoft", "finance", "analyst", "operations"],
    },
    {
        "name": "Automata — Fix the Code",
        "url": f"{BASE}/automata-fix-the-code/",
        "test_type": "S",
        "test_type_label": "Simulation",
        "description": (
            "A hands-on coding simulation where candidates debug and fix real code "
            "in a browser IDE. Language-agnostic; measures practical programming "
            "ability beyond theoretical knowledge."
        ),
        "duration": "60 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager"],
        "competencies": ["debugging", "code quality", "software development"],
        "tags": ["simulation", "coding", "developer", "software engineer", "debugging", "hands-on"],
    },
    # ── Situational Judgment / Simulation ─────────────────────────────────
    {
        "name": "Customer Service Simulation",
        "url": f"{BASE}/customer-service-simulation/",
        "test_type": "S",
        "test_type_label": "Simulation",
        "description": (
            "An interactive simulation presenting realistic customer service scenarios. "
            "Measures empathy, problem-solving, communication and complaint-handling "
            "ability for frontline and contact-centre roles."
        ),
        "duration": "20 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Entry", "Frontline"],
        "competencies": ["customer service", "communication", "empathy", "problem-solving"],
        "tags": ["simulation", "SJT", "customer service", "contact centre", "frontline",
                 "communication", "representative"],
    },
    {
        "name": "Sales Representative Solution",
        "url": f"{BASE}/sales-representative-solution/",
        "test_type": "S",
        "test_type_label": "Simulation",
        "description": (
            "Simulates real sales scenarios to measure persuasion, resilience, "
            "customer focus and achievement orientation. Designed for B2B and B2C "
            "sales roles at entry to mid level."
        ),
        "duration": "30 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Entry", "Frontline", "Professional"],
        "competencies": ["sales", "persuasion", "resilience", "customer focus"],
        "tags": ["simulation", "sales", "persuasion", "customer focus", "B2B", "B2C"],
    },
    {
        "name": "Managerial Styles Questionnaire (MSQ)",
        "url": f"{BASE}/managerial-styles-questionnaire/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "Measures six managerial styles based on the Hay/McBer model: directive, "
            "visionary, affiliative, participative, pacesetting and coaching. Used for "
            "leadership development and selection of people-managers."
        ),
        "duration": "20 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Manager", "Director", "Executive"],
        "competencies": ["leadership", "people management", "coaching", "team development"],
        "tags": ["personality", "leadership", "manager", "people management", "coaching"],
    },
    {
        "name": "Numerical Reasoning — Graduate",
        "url": f"{BASE}/numerical-reasoning-graduate/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Tailored for graduate-level numerical reasoning, this test presents "
            "business-relevant data interpretation tasks calibrated to graduate "
            "norms. Popular for graduate schemes and early-career hiring."
        ),
        "duration": "25 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate"],
        "competencies": ["numerical reasoning", "data interpretation"],
        "tags": ["cognitive", "ability", "numerical", "graduate", "early career", "scheme"],
    },
    {
        "name": "Verbal Reasoning — Graduate",
        "url": f"{BASE}/verbal-reasoning-graduate/",
        "test_type": "A",
        "test_type_label": "Ability / Aptitude",
        "description": (
            "Measures verbal comprehension and reasoning calibrated to graduate "
            "norms. Widely used in graduate schemes across consulting, finance "
            "and the public sector."
        ),
        "duration": "19 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Graduate"],
        "competencies": ["verbal reasoning", "comprehension"],
        "tags": ["cognitive", "ability", "verbal", "graduate", "early career", "consulting"],
    },
    {
        "name": "Occupational Personality Questionnaire — Development (OPQ Development Report)",
        "url": f"{BASE}/opq-development-report/",
        "test_type": "P",
        "test_type_label": "Personality / Behavioural",
        "description": (
            "Provides a coaching-oriented narrative report from the OPQ32 profile, "
            "highlighting development priorities and strengths. Used for individual "
            "development planning and executive coaching."
        ),
        "duration": "25–45 minutes",
        "remote_testing": "Yes",
        "adaptive_irt": "No",
        "job_levels": ["Professional", "Manager", "Director", "Executive"],
        "competencies": ["self-awareness", "leadership development", "coaching"],
        "tags": ["personality", "development", "coaching", "leadership", "OPQ"],
    },
]


def main(force: bool = False) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists() and not force:
        print(f"catalog.json already exists at {OUTPUT_PATH}. Use --force to overwrite.")
        return

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(SEED, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(SEED)} seed assessments → {OUTPUT_PATH}")
    print("Re-run the real scraper to enrich this catalog:")
    print("  python -m scraper.scrape_catalog")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing catalog.json")
    args = parser.parse_args()
    main(force=args.force)
