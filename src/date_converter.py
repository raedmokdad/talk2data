import re
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# German month names mapping
GERMAN_MONTHS = {
    'januar': '01',
    'februar': '02',
    'märz': '03',
    'april': '04',
    'mai': '05',
    'juni': '06',
    'juli': '07',
    'august': '08',
    'september': '09',
    'oktober': '10',
    'november': '11',
    'dezember': '12'
}

# English month names
ENGLISH_MONTHS = {
    'january': '01',
    'february': '02',
    'march': '03',
    'april': '04',
    'may': '05',
    'june': '06',
    'july': '07',
    'august': '08',
    'september': '09',
    'october': '10',
    'november': '11',
    'december': '12'
}

# Combined month mapping
ALL_MONTHS = {**GERMAN_MONTHS, **ENGLISH_MONTHS}


def extract_and_convert_dates(text: str) -> str:
    """
    Extract dates from text and convert them to ISO format (YYYY-MM-DD).
    
    Supports formats:
    - "15. Januar 2023" → "2023-01-15"
    - "15 Januar 2023" → "2023-01-15"
    - "Januar 2023" → "2023-01"
    - "15.01.2023" → "2023-01-15"
    - "2023-01-15" → "2023-01-15" (already ISO)
    
    Args:
        text: Input text potentially containing dates
        
    Returns:
        Text with dates converted to ISO format
    """
    original_text = text
    
    # Pattern 1: "15. Januar 2023" or "15 Januar 2023"
    pattern1 = r'\b(\d{1,2})\.?\s+(' + '|'.join(ALL_MONTHS.keys()) + r')\s+(\d{4})\b'
    
    def replace_full_date(match):
        day = match.group(1).zfill(2)
        month_name = match.group(2).lower()
        year = match.group(3)
        month = ALL_MONTHS.get(month_name)
        if month:
            iso_date = f"{year}-{month}-{day}"
            logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
            return iso_date
        return match.group(0)
    
    text = re.sub(pattern1, replace_full_date, text, flags=re.IGNORECASE)
    
    # Pattern 2: "Januar 2023" (month and year only)
    pattern2 = r'\b(' + '|'.join(ALL_MONTHS.keys()) + r')\s+(\d{4})\b'
    
    def replace_month_year(match):
        month_name = match.group(1).lower()
        year = match.group(2)
        month = ALL_MONTHS.get(month_name)
        if month:
            iso_date = f"{year}-{month}"
            logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
            return iso_date
        return match.group(0)
    
    text = re.sub(pattern2, replace_month_year, text, flags=re.IGNORECASE)
    
    # Pattern 3: "15.01.2023" (DD.MM.YYYY) → "2023-01-15"
    pattern3 = r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b'
    
    def replace_german_format(match):
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        iso_date = f"{year}-{month}-{day}"
        logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
        return iso_date
    
    text = re.sub(pattern3, replace_german_format, text)
    
    if text != original_text:
        logger.info(f"Date conversion applied:\nBefore: {original_text}\nAfter: {text}")
    
    return text


def parse_date_to_iso(date_str: str) -> Optional[str]:
    """
    Parse a single date string to ISO format.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        ISO formatted date string (YYYY-MM-DD) or None if parsing fails
    """
    date_str = date_str.strip()
    
    # Try different patterns
    formats = [
        r'(\d{1,2})\.?\s+(' + '|'.join(ALL_MONTHS.keys()) + r')\s+(\d{4})',  # 15. Januar 2023
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.01.2023
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-01-15 (already ISO)
    ]
    
    for pattern in formats:
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            # Handle different group structures
            if len(groups) == 3:
                if re.match(r'\d{4}', groups[0]):  # ISO format
                    return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                elif groups[1].isalpha():  # Month name format
                    day = groups[0].zfill(2)
                    month = ALL_MONTHS.get(groups[1].lower())
                    year = groups[2]
                    if month:
                        return f"{year}-{month}-{day}"
                else:  # DD.MM.YYYY
                    return f"{groups[2]}-{groups[1].zfill(2)}-{groups[0].zfill(2)}"
    
    logger.warning(f"Could not parse date: {date_str}")
    return None


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "Wie viel Umsatz am 15. Januar 2023?",
        "Verkäufe im Januar 2023",
        "Umsatz am 01.03.2023",
        "Was war der Umsatz am 15 Februar 2023?",
        "Vergleiche Januar 2023 und Februar 2023",
        "Sales on January 15, 2023",  # English not yet supported but won't break
    ]
    
    print("Date Conversion Tests:")
    print("=" * 60)
    for test in test_cases:
        result = extract_and_convert_dates(test)
        print(f"Input:  {test}")
        print(f"Output: {result}")
        print("-" * 60)
