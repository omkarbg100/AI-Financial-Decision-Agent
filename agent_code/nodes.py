import os
import json
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from schema import ExtractedAmount, EventStatus, OutputRow
from state import GraphState
from simulation import simulate_90_days

# Ensure to load API key
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

def gather_context_node(state: GraphState, data_loader) -> GraphState:
    request_id = state['request_id']
    req = data_loader.get_request(request_id)
    user_id = req['user_id']
    
    return {
        "request": req,
        "user_id": user_id,
        "profile": data_loader.get_profile(user_id) or {},
        "events": data_loader.get_events(user_id) or [],
        "messages": data_loader.get_messages(user_id, request_id=request_id) or [],
        "images": data_loader.get_images(user_id, request_id=request_id) or [],
        "payment_options": data_loader.get_payment_options(request_id) or [],
    }

def process_unstructured_node(state: GraphState, data_loader) -> GraphState:
    # 1. Update events with image amounts if amount is missing/null
    updated_events = []
    
    for event in state['events']:
        event_copy = event.copy()
        if pd.isna(event_copy.get('amount')) or event_copy.get('amount') == '':
            # Look for related image
            related_images = [img for img in state['images'] if str(img.get('related_event_id')) == str(event_copy['event_id'])]
            if related_images:
                # In a real scenario, use Vision LLM to extract amount
                # For this agent template, we mock the vision extraction call
                image_id = related_images[0]['image_id']
                image_path = os.path.join(data_loader.dataset_dir, "media", "images", f"{image_id}.png")
                
                # Mocked extraction (assume 100 for skeleton, in actual we'd pass image_path to LLM)
                event_copy['amount'] = 100.0 
        updated_events.append(event_copy)
        
    # 2. Process messages to cancel/amend events
    # (Mocked message processing for skeleton)
    
    return {"updated_events": updated_events}

def simulation_node(state: GraphState, data_loader) -> GraphState:
    simulation_results = simulate_90_days(state, data_loader)
    return simulation_results

def generate_explanation_node(state: GraphState) -> GraphState:
    prompt = f"""
    You are a financial advisor. Explain this decision briefly.
    Request: {state['request']}
    Status: {state['affordability_status']}
    Recommended Method: {state['recommended_payment_method']}
    Safe to pay: {state['amount_safe_to_pay']}
    """
    
    # Try calling LLM, if it fails due to no key, fallback
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        decision_explanation = response.content
    except Exception as e:
        decision_explanation = f"Based on your current balance and 90-day forecast, this is the recommended action. (LLM error: {e})"
    
    final_output = {
        "request_id": state['request_id'],
        "amount_safe_to_pay": state['amount_safe_to_pay'],
        "affordability_status": state['affordability_status'],
        "recommended_payment_method": state['recommended_payment_method'],
        "payment_plan": state['payment_plan'],
        "earliest_date_for_full_payment": state['earliest_date_for_full_payment'],
        "spending_changes_needed": state['spending_changes_needed'],
        "decision_explanation": decision_explanation
    }
    
    return {"decision_explanation": decision_explanation, "final_output": final_output}
