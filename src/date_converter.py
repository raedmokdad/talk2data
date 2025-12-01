import re
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


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


ALL_MONTHS = {**GERMAN_MONTHS, **ENGLISH_MONTHS}


def extract_and_convert_dates(text: str) -> str:
    """
    Extract dates from text and convert them to  (YYYY-MM-DD).

    """
    original_text = text
    
    
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
    
    
    pattern3 = r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b'
    
    def replace_german_format(match):
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        iso_date = f"{year}-{month}-{day}"
        logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
        return iso_date
    
    text = re.sub(pattern3, replace_german_format, text)
    
    pattern4 = r'\b(\d{4})/(\d{1,2})/(\d{1,2})\b'
    def replace_slash_format(match):
        year = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        day = match.group(3)
        iso_date = f"{year}-{month}-{day}"
        logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
        return iso_date
    text = re.sub(pattern4, replace_slash_format, text)
    
    
    pattern5 = r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b'
    def replace_hypen_format(match):
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        iso_date = f"{year}-{month}-{day}"
        logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
        return iso_date
    text = re.sub(pattern5, replace_hypen_format, text)
    
    pattern6 = r'\b(' + '|'.join(ALL_MONTHS.keys()) + r')\s+(\d{1,2}),?\s+(\d{4})\b'
    def replace_usformat_format(match):
        month = match.group(1).lower()
        day = match.group(2).zfill(2)
        year = match.group(3)
        month = ALL_MONTHS.get(month)
        if month:
            iso_date = f"{year}-{month}-{day}"
            logger.info(f"Converted date: '{match.group(0)}' → '{iso_date}'")
            return iso_date
        return match.group(0)
    text = re.sub(pattern6, replace_usformat_format, text, flags=re.IGNORECASE)
    
    
    if text != original_text:
        logger.info(f"Date conversion applied:\nBefore: {original_text}\nAfter: {text}")
    
    return text



if __name__ == "__main__":
    
    
    test_cases = [
        "Wie viel Umsatz am 15. Januar 2023?",
        "Verkäufe im Januar 2023",
        "Umsatz am 01.03.2023",
        "Was war der Umsatz am 15 Februar 2023?",
        "Vergleiche Januar 2023 und Februar 2023",
        "Sales on January 15, 2023", 
        "Sales on 2023/01/15",
        "Sales on 15-01-2023",
        "Sales on January 15, 2023"
    ]
    
    print("Date Conversion Tests:")
    print("=" * 60)
    for test in test_cases:
        result = extract_and_convert_dates(test)
        print(f"Input:  {test}")
        print(f"Output: {result}")
        print("-" * 60)
