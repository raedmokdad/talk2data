"""
Test: Talk2Data Agent mit Multi-Table Support
Simuliert interaktiven Test
"""

from src.talk2data_agent import main
import sys
from io import StringIO

# Frage die getestet werden soll
test_question = "Wie viel Umsatz hatte Store Hamburg im Januar 2023?"

print(f"Simuliere Agent-Aufruf mit Frage: {test_question}\n")
print("=" * 60)

# Simuliere user input
old_stdin = sys.stdin
sys.stdin = StringIO(test_question)

try:
    result = main()
    print(f"\n✓ Agent hat Exit Code {result} zurückgegeben")
finally:
    sys.stdin = old_stdin
