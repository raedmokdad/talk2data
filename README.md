# Talk2Data - Simple SQL Query Generator

Turn your questions into SQL queries! Just ask in plain English and get SQL back.

> I built this to ask questions about Rossmann store data without writing complex SQL. It uses OpenAI's GPT to understand what you want and creates safe SQL queries.

## What it does

- **Ask in English**: "Show me sales for store 5" 
- **Get SQL back**: The AI writes the SQL for you
- **Stay safe**: Validates queries so nothing breaks
- **Pretty smart**: Uses GPT-4 to understand your question

## Quick example

```bash
$ echo "What are the top selling stores?" | python talk2data_agent.py

Generated SQL:
SELECT store, SUM(sales) as total_sales 
FROM rossmann_data 
GROUP BY store 
ORDER BY total_sales DESC 
LIMIT 10;

Confidence: 0.85
```

## How to get started

### What you need
- Python 3.10+ 
- OpenAI API key (get one at openai.com)

### Installation steps
```bash
# Download the code
git clone https://github.com/yourusername/talk2data_rossmann.git
cd talk2data_rossmann

# Set up Python environment  
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install stuff
pip install -r requirements.txt

# Add your OpenAI key
# Create a .env file and put: OPENAI_API_KEY=your-key-here
```

### Try it out
```bash
cd src
python talk2data_agent.py
# Type your question and see what happens!
```
## What's inside

```
src/
├── talk2data_agent.py       # Main program - start here
├── llm_sql_generator.py     # The AI magic happens here  
├── sql_validator.py         # Keeps queries safe
└── test_sql_validator.py    # Tests to make sure it works

prompts/                     # Templates for the AI
config/                      # Database schema info
data/                        # Some example queries
```

## How it works

It's pretty simple:
1. You ask a question in English
2. AI generates SQL query for you
3. System checks if the SQL is safe
4. If not good enough, AI tries again
5. You get the final SQL

## What questions can you ask?

Try things like:
- "Show me sales for store 5"
- "Which stores had the highest revenue?"  
- "What's the average sales per day?"
- "Find stores with sales above 10000"

## Run some tests

```bash
cd src
python test_sql_validator.py
# Should see: All tests passed!
```

## Using it in your code

```python
from talk2data_agent import main

# Simple way
result = main("Show me top 5 stores by sales")
print(result)
```

## Some examples

Ask: "What stores sold the most last week?"
Get: `SELECT store, SUM(sales) FROM rossmann_data WHERE date >= '2024-11-07' GROUP BY store ORDER BY SUM(sales) DESC LIMIT 10`

Ask: "Average daily sales for store 123" 
Get: `SELECT AVG(sales) FROM rossmann_data WHERE store = 123`

## Tech stuff (if you care)

- Python 3.12
- OpenAI GPT-4o-mini for the AI part
- Validates SQL so nothing dangerous runs
- Has retry logic when AI messes up


Made by Raed Mokdad. Hope you find it useful!
