from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    request_id: str
    user_id: str
    request: Dict[str, Any]
    profile: Dict[str, Any]
    events: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    payment_options: List[Dict[str, Any]]
    
    # Processed states
    updated_events: List[Dict[str, Any]]
    
    # Simulation Output
    amount_safe_to_pay: float
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    
    # Final Output
    decision_explanation: str
    final_output: Dict[str, Any]
