import os
import yaml
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import List, Dict
from trello import TrelloClient
from dotenv import load_dotenv

class ForexTrelloIntegration:
    def __init__(self):
        # Load environment variables and config
        load_dotenv()
        self.config = self._load_config()
        
        # Initialize Trello client
        self.trello = TrelloClient(
            api_key=os.getenv('TRELLO_API_KEY'),
            api_secret=os.getenv('TRELLO_API_SECRET'),
            token=os.getenv('TRELLO_TOKEN')
        )
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        with open('config.yml', 'r') as file:
            config = yaml.safe_load(file)
        return config

    def get_high_impact_news(self) -> List[Dict]:
        """Fetch high-impact news from Forex Factory"""
        headers = {
            "User-Agent": self.config['forex_factory']['user_agent']
        }
        
        try:
            response = requests.get(
                self.config['forex_factory']['base_url'], 
                headers=headers
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []
            calendar_rows = soup.find_all('tr', class_='calendar_row')
            current_date = None
            
            for row in calendar_rows:
                impact = row.find('td', class_='impact')
                if impact and 'high' in str(impact).lower():
                    date_cell = row.find('td', class_='calendar__date')
                    if date_cell and date_cell.text.strip():
                        current_date = date_cell.text.strip()
                    
                    time = row.find('td', class_='calendar__time')
                    currency = row.find('td', class_='calendar__currency')
                    event = row.find('td', class_='calendar__event')
                    forecast = row.find('td', class_='calendar__forecast')
                    previous = row.find('td', class_='calendar__previous')
                    
                    news_items.append({
                        'date': current_date,
                        'time': time.text.strip() if time else 'N/A',
                        'currency': currency.text.strip() if currency else 'N/A',
                        'event': event.text.strip() if event else 'N/A',
                        'forecast': forecast.text.strip() if forecast else 'N/A',
                        'previous': previous.text.strip() if previous else 'N/A'
                    })
            
            return news_items
            
        except Exception as e:
            print(f"Error fetching forex data: {e}")
            return []

    def format_news_comment(self, news_items: List[Dict]) -> str:
        """Format news items as a Markdown comment for Trello"""
        if not news_items:
            return "No high-impact news events found."
            
        comment = "# High Impact Forex News Events\n\n"
        comment += "| Date | Time | Currency | Event | Forecast | Previous |\n"
        comment += "|------|------|----------|--------|----------|----------|\n"
        
        for item in news_items:
            comment += f"| {item['date']} | {item['time']} | {item['currency']} | "
            comment += f"{item['event']} | {item['forecast']} | {item['previous']} |\n"
            
        comment += f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return comment

    def update_trello_card(self, comment_text: str) -> None:
        """Post the forex news as a comment on the specified Trello card"""
        try:
            # Get the board
            board = self.trello.get_board(self.config['trello']['board_id'])
            
            # Find the list
            trello_list = None
            for lst in board.list_lists():
                if lst.name == self.config['trello']['list_name']:
                    trello_list = lst
                    break
            
            if not trello_list:
                raise Exception(f"List '{self.config['trello']['list_name']}' not found")
            
            # Find the card
            card = None
            for c in trello_list.list_cards():
                if c.name == self.config['trello']['card_name']:
                    card = c
                    break
            
            if not card:
                raise Exception(f"Card '{self.config['trello']['card_name']}' not found")
            
            # Add comment
            card.comment(comment_text)
            print("Successfully updated Trello card with forex news")
            
        except Exception as e:
            print(f"Error updating Trello card: {e}")

def main():
    integration = ForexTrelloIntegration()
    news_items = integration.get_high_impact_news()
    comment_text = integration.format_news_comment(news_items)
    integration.update_trello_card(comment_text)

if __name__ == "__main__":
    main()
