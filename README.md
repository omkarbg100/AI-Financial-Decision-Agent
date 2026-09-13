# Buy or Wait? — AI Financial Decision Agent

> An AI-powered financial agent that evaluates whether a user can safely afford a requested expense. Built using **LangGraph**, **LangChain**, and the **Gemini API**, it reconstructs the user's 90-day financial forecast from structured data (CSVs), messages, and images to recommend whether to pay in full, partially, via installments, wait, or not proceed.

## Requirements
- Python 3.9+
- A `dataset/` directory in the root of the project containing the required CSV files (`requests.csv`, `financial_profiles.csv`, etc.).
- A `.env` file containing `GEMINI_API_KEY=your_key` or set it in your environment variables.

## Setup
1. Create a `.env` file in the root of `agent_code` directory and add your API key:
   ```text
   GEMINI_API_KEY=your_actual_api_key_here
   ```
2. Create a virtual environment: `python -m venv venv`
3. Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Running
Execute the main script:
```bash
python main.py
```

This will read from `dataset/`, evaluate each request, and produce:
1. `output.csv` - The final recommendations.
2. `evaluation/usage_report.md` - Token usage and estimated cost report.
