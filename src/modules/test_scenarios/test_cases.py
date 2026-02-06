TEST_SCENARIOS = {
    """
    Test Scenarios for Commercial Personas (Thursday Task)
    5 distinctive test cases for each business persona
    """
    "🛡️ Insurance Risk Assessor": [
        {
            "id": "INS_01",
            "question": "I have a portfolio of 50 commercial properties in Northern California. What's my maximum probable loss for a Category 3 wildfire event, and what premium increase should I expect?",
            "expected_aspects": ["financial estimates", "policy analysis", "risk mitigation"]
        },
        {
            "id": "INS_02",
            "question": "A client's warehouse burned down. They have business interruption coverage with a 72-hour waiting period. The fire lasted 5 days. What percentage of their lost revenue is covered?",
            "expected_aspects": ["claims process", "coverage details", "financial calculation"]
        }
    ],
    
    "⚡ Power Grid Operator": [
        {
            "id": "PWR_01",
            "question": "We're planning PSPS (Public Safety Power Shutoff) for next week with 40mph winds forecasted. What's the minimum vegetation clearance needed for our 69kV lines, and how many customers will be affected?",
            "expected_aspects": ["technical specifications", "customer impact", "safety protocols"]
        },
        {
            "id": "PWR_02",
            "question": "A substation is in Red Flag warning area. Should we de-energize proactively? What's the cost-benefit of 24-hour outage vs. wildfire liability?",
            "expected_aspects": ["risk assessment", "cost analysis", "operational decision"]
        }
    ],
    
    "🚚 Logistics Manager": [
        {
            "id": "LOG_01",
            "question": "Highway 101 is closed due to wildfires. I have 20 refrigerated trucks with perishables. What's the best alternate route from San Francisco to Portland, and what's the cost impact?",
            "expected_aspects": ["route planning", "cost analysis", "timeline impact"]
        },
        {
            "id": "LOG_02",
            "question": "Our distribution center is in evacuation zone. We have 48 hours to relocate $2M inventory. What's the optimal relocation strategy and insurance implications?",
            "expected_aspects": ["inventory management", "insurance", "logistical planning"]
        }
    ],
    
    "🏗️ Real Estate Developer": [
        {
            "id": "RE_01",
            "question": "We're developing a 200-home subdivision in a high-fire-risk zone. What fire-resistant building materials should we use to meet California's Chapter 7A requirements, and what's the cost premium?",
            "expected_aspects": ["building codes", "material costs", "compliance"]
        },
        {
            "id": "RE_02",
            "question": "Our construction timeline is delayed 60 days due to fire season. What are the financial penalties from buyers, and can we claim force majeure?",
            "expected_aspects": ["financial impact", "contract law", "risk management"]
        }
    ],
    
    "🏞️ Park Ranger / Tourism": [
        {
            "id": "PARK_01",
            "question": "We have 500 campers in a national park with approaching wildfire. What's the evacuation protocol, and how do we communicate with visitors who don't speak English?",
            "expected_aspects": ["safety protocols", "communication", "visitor management"]
        },
        {
            "id": "PARK_02",
            "question": "A 2-week park closure during peak season costs us $250,000 in lost revenue. What insurance covers this, and what's our deductible?",
            "expected_aspects": ["financial impact", "insurance", "revenue protection"]
        }
    ]
}

def get_test_scenario(persona, scenario_id=None):
    """
    Retrieve test scenarios for a specific persona
    """
    if persona not in TEST_SCENARIOS:
        return []
    
    if scenario_id:
        return [scenario for scenario in TEST_SCENARIOS[persona] if scenario["id"] == scenario_id]
    
    return TEST_SCENARIOS[persona]

def get_all_scenarios():
    """
    Get all test scenarios for reporting
    """
    all_scenarios = []
    for persona, scenarios in TEST_SCENARIOS.items():
        for scenario in scenarios:
            all_scenarios.append({
                "persona": persona,
                **scenario
            })
    return all_scenarios