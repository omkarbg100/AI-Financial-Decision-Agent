import pandas as pd
import os

class DataLoader:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir
        
        self.requests = pd.read_csv(os.path.join(self.dataset_dir, "requests.csv"))
        # Using string types for IDs is safer
        self.requests['request_id'] = self.requests['request_id'].astype(str)
        self.requests['user_id'] = self.requests['user_id'].astype(str)

        self.profiles = pd.read_csv(os.path.join(self.dataset_dir, "financial_profiles.csv"))
        self.profiles['user_id'] = self.profiles['user_id'].astype(str)

        self.events = pd.read_csv(os.path.join(self.dataset_dir, "financial_events.csv"))
        self.events['user_id'] = self.events['user_id'].astype(str)
        self.events['event_id'] = self.events['event_id'].astype(str)
        if 'linked_event_id' in self.events.columns:
            self.events['linked_event_id'] = self.events['linked_event_id'].astype(str)

        self.rates = pd.read_csv(os.path.join(self.dataset_dir, "exchange_rates.csv"))

        self.options = pd.read_csv(os.path.join(self.dataset_dir, "request_payment_options.csv"))
        self.options['request_id'] = self.options['request_id'].astype(str)
        
        self.messages = pd.read_csv(os.path.join(self.dataset_dir, "messages.csv"))
        self.messages['user_id'] = self.messages['user_id'].astype(str)
        if 'request_id' in self.messages.columns:
            self.messages['request_id'] = self.messages['request_id'].astype(str)
        if 'related_event_id' in self.messages.columns:
            self.messages['related_event_id'] = self.messages['related_event_id'].astype(str)

        self.images = pd.read_csv(os.path.join(self.dataset_dir, "images.csv"))
        self.images['user_id'] = self.images['user_id'].astype(str)
        self.images['image_id'] = self.images['image_id'].astype(str)
        if 'request_id' in self.images.columns:
            self.images['request_id'] = self.images['request_id'].astype(str)
        if 'related_event_id' in self.images.columns:
            self.images['related_event_id'] = self.images['related_event_id'].astype(str)

    def get_all_requests(self):
        return self.requests.to_dict('records')

    def get_request(self, request_id: str):
        res = self.requests[self.requests['request_id'] == request_id]
        return res.iloc[0].to_dict() if not res.empty else None

    def get_profile(self, user_id: str):
        res = self.profiles[self.profiles['user_id'] == user_id]
        return res.iloc[0].to_dict() if not res.empty else None

    def get_events(self, user_id: str):
        res = self.events[self.events['user_id'] == user_id]
        return res.to_dict('records')

    def get_messages(self, user_id: str, request_id: str = None, event_id: str = None):
        res = self.messages[self.messages['user_id'] == user_id]
        if request_id:
            res = res[res['request_id'] == request_id]
        if event_id:
            res = res[res['related_event_id'] == event_id]
        return res.to_dict('records')

    def get_images(self, user_id: str, request_id: str = None, event_id: str = None):
        res = self.images[self.images['user_id'] == user_id]
        if request_id:
            res = res[res['request_id'] == request_id]
        if event_id:
            res = res[res['related_event_id'] == event_id]
        return res.to_dict('records')

    def get_payment_options(self, request_id: str):
        res = self.options[self.options['request_id'] == request_id]
        return res.to_dict('records')
        
    def get_exchange_rate(self, date: str, from_currency: str, to_currency: str):
        if from_currency == to_currency:
            return 1.0
        # Look for direct match
        res = self.rates[(self.rates['date'] == date) & (self.rates['base_currency'] == to_currency) & (self.rates['target_currency'] == from_currency)]
        if not res.empty:
            # wait, if base is to_currency and target is from_currency, then 1 to_currency = X from_currency
            # so 1 from_currency = 1/X to_currency
            return 1.0 / res.iloc[0]['rate']
            
        res = self.rates[(self.rates['date'] == date) & (self.rates['base_currency'] == from_currency) & (self.rates['target_currency'] == to_currency)]
        if not res.empty:
            return res.iloc[0]['rate']
            
        # If no rate found on exact date, we might need a fallback or assume it's missing (shouldn't happen per instructions)
        return 1.0
