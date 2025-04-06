import requests
import json
import re
from typing import Dict, Optional

def extract_investor_info(text: str) -> Dict[str, Optional[float]]:
    required_fields = ["age", "budget", "start_date", "end_date", "avoid", "salary"]
    default_values = {
        "age": 30,
        "budget": 100000.00,
        "start_date": "2024-01-01",
        "end_date": "2025-01-01",
        "avoid": "",
        "salary": 50000.00
    }

    prompt = f"""Analyze this text and extract the following details as a valid JSON object:
{{
    "age": <integer>,
    "budget": <decimal number with optional cents>,
    "start_date": <YYYY-MM-DD>,
    "end_date": <YYYY-MM-DD>,
    "avoid": <text description>,
    "salary": <decimal number if present>
}}

Text to analyze: "{text}"

Return ONLY the JSON object with double quotes, nothing else."""

    try:
        # Verify Ollama is running
        requests.get("http://localhost:11434/api/tags", timeout=5).raise_for_status()

        # Get LLM response
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3}
            },
            timeout=30
        ).json()

        # Improved JSON extraction using regex
        raw_response = response["response"].strip()
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            return default_values
            
        data = json.loads(json_match.group())

        # Safely convert numeric fields with fallbacks
        conversions = {
            'age': lambda x: int(x) if x else default_values['age'],
            'budget': lambda x: round(float(str(x).replace(',', '')), 2) if x else default_values['budget'],
            'salary': lambda x: round(float(str(x).replace(',', '')), 2) if x else default_values['salary']
        }

        return {
            field: conversions[field](data.get(field, default_values[field])) 
            if field in conversions 
            else data.get(field, default_values[field])
            for field in required_fields
        }

    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return default_values