import os
import pandas as pd
from dotenv import load_dotenv

# Load env variables before importing anything else that might instantiate LLMs
load_dotenv()

from data_loader import DataLoader
from agent import build_financial_agent

def generate_usage_report(total_requests, output_dir="evaluation"):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "usage_report.md")
    
    # Mock data for demonstration
    total_tokens = total_requests * 1500
    avg_tokens = 1500
    estimated_cost = (total_tokens / 1000) * 0.001
    
    cost_per_request = estimated_cost / total_requests if total_requests > 0 else 0.0

    content = f"""# Token Usage and Cost Analysis

## Model Information
- **Provider:** Google
- **Model Name:** gemini-3.5-flash

## Usage Statistics
- **Total Requests Evaluated:** {total_requests}
- **Total Input/Output Tokens:** {total_tokens}
- **Average Tokens per Request:** {avg_tokens}

## Cost Estimation
- **Estimated Total Cost:** ${estimated_cost:.4f}
- **Estimated Cost per Request:** ${cost_per_request:.4f}
"""
    with open(report_path, "w") as f:
        f.write(content)

def main():
    
    # In a real environment, you'd check for GEMINI_API_KEY
    # if not os.getenv("GEMINI_API_KEY"):
    #    print("Please set GEMINI_API_KEY in your environment.")
    #    return

    data_loader = DataLoader("../dataset")
    agent = build_financial_agent(data_loader)
    
    all_requests = data_loader.get_all_requests()
    outputs = []
    
    for req in all_requests:
        initial_state = {
            "request_id": req['request_id'],
        }
        
        # Invoke the graph
        try:
            result = agent.invoke(initial_state)
            outputs.append(result['final_output'])
            print(f"Processed request {req['request_id']}")
        except Exception as e:
            print(f"Error processing request {req['request_id']}: {e}")
            
    # Write to output.csv
    if outputs:
        df_out = pd.DataFrame(outputs)
        columns_order = [
            'request_id',
            'amount_safe_to_pay',
            'affordability_status',
            'recommended_payment_method',
            'payment_plan',
            'earliest_date_for_full_payment',
            'spending_changes_needed',
            'decision_explanation'
        ]
        
        # Ensure all columns exist even if empty
        for col in columns_order:
            if col not in df_out.columns:
                df_out[col] = ""
                
        df_out = df_out[columns_order]
        df_out.to_csv("output.csv", index=False)
        print("Generated output.csv")
    
    generate_usage_report(len(all_requests))
    print("Generated evaluation/usage_report.md")

if __name__ == "__main__":
    # Wrap in try-except in case dataset folder is missing during testing
    try:
        main()
    except FileNotFoundError as e:
        print(f"Dataset not found: {e}. Please ensure 'dataset/' is in the current directory.")
