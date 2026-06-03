import requests
from bs4 import BeautifulSoup
import re

def validate_cc_number(cc_number):
    # Basic Luhn algorithm validation
    check_sum = 0
    for i in range(len(cc_number)):
        digit = int(cc_number[i])
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        check_sum += digit
    return (check_sum % 10) == 0

def scrape_cc_checker(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the CC input field
    cc_input = soup.find("input", {"name": "cc"})

    if not cc_input:
        print(f"CC input field not found on {url}")
        return

    cc_field = cc_input["id"]  # e.g., "cc-field"

    # Find the CC validation message
    cc_message = soup.find("p", {"id": "cc-message"})

    if not cc_message:
        print(f"CC validation message not found on {url}")
        return

    message_field = cc_message["id"]  # e.g., "cc-message"

    # List of CC numbers to check
    cc_numbers = ["4111111111111111", "4000056655665566", "6011111111111117"]

    for cc_num in cc_numbers:
        data = {cc_field: cc_num}
        response = requests.post(url, data=data)
        soup = BeautifulSoup(response.text, "html.parser")
        message = soup.find("p", {"id": message_field}).get_text().strip()

        if "valid" in message.lower():
            print(f"{cc_num} is valid.")
        else:
            print(f"{cc_num} is invalid.")

if __name__ == "__main__":
    # The URL of the fictional CC checker website
    cc_checker_url = "https://example.com/cc_checker.html"

    # Scrape the CC checker website and validate a list of CC numbers
    scrape_cc_checker(cc_checker_url)
