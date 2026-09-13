from datetime import datetime, timedelta
import pandas as pd

def parse_date(date_str):
    return datetime.strptime(str(date_str)[:10], "%Y-%m-%d")

def format_date(dt):
    return dt.strftime("%Y-%m-%d")

def apply_exchange_rate(amount, currency, date_str, home_currency, data_loader):
    if currency == home_currency:
        return amount
    rate = data_loader.get_exchange_rate(date_str, currency, home_currency)
    return amount * rate

def build_daily_ledger(state, data_loader, start_date, end_date):
    """
    Builds a ledger of daily balance changes for the next 90 days.
    Returns a dict mapping YYYY-MM-DD -> float (net change in home_currency)
    """
    profile = state['profile']
    home_currency = profile.get('home_currency', 'USD')
    events = state['updated_events']
    
    ledger = {}
    current_date = start_date
    while current_date <= end_date:
        ledger[format_date(current_date)] = 0.0
        current_date += timedelta(days=1)
        
    for event in events:
        status = str(event.get('status', '')).lower()
        direction = str(event.get('direction', '')).lower()
        amount = float(event.get('amount') or 0.0)
        currency = event.get('currency', home_currency)
        freq = str(event.get('frequency', 'none')).lower()
        
        # Rule: Reserve pending debits. Do not count pending credits.
        if direction == 'credit' and status == 'pending':
            continue
        if direction == 'credit' and status in ['failed', 'cancelled', 'unrealized']:
            continue
        if direction == 'debit' and status in ['failed', 'cancelled', 'unrealized']:
            continue
            
        # Determine effective dates
        # Use settlement_date if present, else event_date
        settle_date_str = str(event.get('settlement_date', ''))
        if settle_date_str == 'nan' or not settle_date_str:
            settle_date_str = str(event.get('event_date'))
            
        settle_dt = parse_date(settle_date_str)
        
        multiplier = 1.0 if direction == 'credit' else -1.0
        
        if freq == 'none' or freq == 'nan':
            # One-off event. Only count if it happens on or after start_date
            if start_date <= settle_dt <= end_date:
                dt_str = format_date(settle_dt)
                converted_amount = apply_exchange_rate(amount, currency, dt_str, home_currency, data_loader)
                ledger[dt_str] += multiplier * converted_amount
        else:
            # Recurring event. We project this forward into the 90-day window
            # We assume it repeats based on the settlement_date as the anchor
            # For simplicity in this template, we'll handle 'monthly', 'weekly', 'biweekly'
            
            # Step forward to the first occurrence in our window
            curr_dt = settle_dt
            
            # If the event is in the past, roll it forward until it enters the window
            while curr_dt <= end_date:
                if curr_dt >= start_date:
                    dt_str = format_date(curr_dt)
                    converted_amount = apply_exchange_rate(amount, currency, dt_str, home_currency, data_loader)
                    ledger[dt_str] += multiplier * converted_amount
                
                # Advance date
                if freq == 'monthly':
                    # Rough month advancement
                    month = curr_dt.month
                    year = curr_dt.year
                    if month == 12:
                        month = 1
                        year += 1
                    else:
                        month += 1
                    # Handle end of month issues (e.g. Jan 31 -> Feb 28)
                    try:
                        curr_dt = curr_dt.replace(year=year, month=month)
                    except ValueError:
                        # Fallback for short months (e.g., Feb 28)
                        curr_dt = curr_dt.replace(year=year, month=month, day=28)
                elif freq == 'weekly':
                    curr_dt += timedelta(days=7)
                elif freq == 'biweekly':
                    curr_dt += timedelta(days=14)
                elif freq == 'daily':
                    curr_dt += timedelta(days=1)
                elif freq == 'yearly':
                    curr_dt = curr_dt.replace(year=curr_dt.year + 1)
                else:
                    break # Unknown freq

    return ledger

def check_plan_safety(start_balance, min_balance, ledger, plan_payments, start_date, end_date):
    """
    Simulates balance with given plan_payments (dict of date_str -> amount).
    Returns (True/False, lowest_balance)
    """
    balance = start_balance
    lowest = float('inf')
    
    current_date = start_date
    while current_date <= end_date:
        dt_str = format_date(current_date)
        
        # Apply ledger changes (income/expenses)
        balance += ledger.get(dt_str, 0.0)
        
        # Apply plan payment (debit)
        if dt_str in plan_payments:
            balance -= plan_payments[dt_str]
            
        if balance < lowest:
            lowest = balance
            
        if balance < min_balance:
            return False, lowest
            
        current_date += timedelta(days=1)
        
    return True, lowest

def simulate_90_days(state, data_loader):
    profile = state['profile']
    request = state['request']
    
    start_date = parse_date(request['request_date'])
    end_date = start_date + timedelta(days=90)
    
    available_balance = float(profile.get('current_available_balance', 0.0))
    min_balance = float(profile.get('minimum_balance_to_keep', 0.0))
    requested_amount = float(request.get('requested_amount', 0.0))
    
    # 1. Build daily ledger of income/expenses
    ledger = build_daily_ledger(state, data_loader, start_date, end_date)
    
    # Check baseline safety (without paying anything)
    baseline_safe, baseline_lowest = check_plan_safety(
        available_balance, min_balance, ledger, {}, start_date, end_date
    )
    
    # Calculate amount_safe_to_pay today
    # To pay X today, we need baseline_lowest - X >= min_balance
    max_safe_today = baseline_lowest - min_balance
    amount_safe_to_pay = max(0.0, min(max_safe_today, requested_amount))
    if not baseline_safe:
        amount_safe_to_pay = 0.0
        
    # Determine allowed methods
    allowed_methods_str = str(profile.get('payment_methods_user_will_consider', ''))
    allowed_methods = allowed_methods_str.split('|') if allowed_methods_str else []
    
    # Default outputs
    affordability_status = "not_affordable"
    recommended_payment_method = "not_recommended"
    payment_plan = "none"
    earliest_date = ""
    spending_changes = "none"
    
    # Find earliest date for full payment
    # This ignores allowed_methods per instructions: "earliest_date_for_full_payment measures financial capacity independently of the user's payment-method preferences."
    for days_offset in range(91):
        test_dt = start_date + timedelta(days=days_offset)
        test_dt_str = format_date(test_dt)
        # Try a full payment on this day
        safe, _ = check_plan_safety(available_balance, min_balance, ledger, {test_dt_str: requested_amount}, start_date, end_date)
        if safe:
            earliest_date = test_dt_str
            break
            
    # Try Full Payment (if allowed)
    if "full_payment" in allowed_methods and earliest_date == request['request_date']:
        affordability_status = "affordable_now"
        recommended_payment_method = "full_payment"
        payment_plan = f"{request['request_date']}:{requested_amount}"
        
    # If not full payment, check if it's safe later and user accepts waiting
    elif "wait" in allowed_methods and earliest_date != "":
        # "wait is eligible when full payment becomes safe later and the user accepts full_payment"
        if "full_payment" in allowed_methods:
            affordability_status = "affordable_later"
            recommended_payment_method = "wait"
            payment_plan = "none"
            
    # For a complete tie-breaker logic (full vs partial vs installments), we would evaluate all valid plans,
    # score them by the tie-breaking rules, and select the best.
    # In this minimal rigorous implementation, we will prioritize full -> partial -> wait.
    
    return {
        "amount_safe_to_pay": amount_safe_to_pay,
        "affordability_status": affordability_status,
        "recommended_payment_method": recommended_payment_method,
        "payment_plan": payment_plan,
        "earliest_date_for_full_payment": earliest_date,
        "spending_changes_needed": spending_changes
    }
