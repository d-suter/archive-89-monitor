import json
import requests
from bs4 import BeautifulSoup
import time

DISCORD_WEBHOOK_URL = ''

def load_exchange_rates(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data['rates']

def convert_price(price_gbp, rate_gbp, rate_target):
    return price_gbp * rate_target / rate_gbp

def load_existing_products(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def extract_products(soup, rates):
    products = []
    rate_gbp = float(rates['GBP'])
    rate_eur = float(rates['EUR'])
    rate_chf = float(rates['CHF'])

    for product_block in soup.find_all(class_='card-wrapper'):
        product_info = product_block.find(class_='card-information__wrapper')
        
        name_tag = product_info.find('h3', class_='card-information__text')
        name = name_tag.get_text(strip=True) if name_tag else 'No Name'

        link_tag = name_tag.find('a', href=True) if name_tag else None
        link = link_tag['href'] if link_tag else 'No Link'
        full_link = 'https://archive89.com' + link

        price_tag = product_info.find('span', class_='money')
        price_text = price_tag.get_text(strip=True) if price_tag else 'No Price'
        price_gbp = float(price_text.replace('£', '').replace(' GBP', ''))

        price_eur = convert_price(price_gbp, rate_gbp, rate_eur)
        price_chf = convert_price(price_gbp, rate_gbp, rate_chf)

        image_tag = product_block.find('img', src=True)
        image_url = 'https:' + image_tag['src'].split("?")[0] if image_tag else 'No Image'

        sold_out_tag = product_block.find('div', class_='card__badge')
        sold_out = 'Sold out' in sold_out_tag.get_text() if sold_out_tag else False

        products.append({
            'name': name,
            'detail_link': full_link,
            'price_gbp': f"£{price_gbp:.2f}",
            'price_eur': f"€{price_eur:.2f}",
            'price_chf': f"CHF {price_chf:.2f}",
            'image_url': image_url,
            'sold_out': sold_out
        })

    return products

def check_page(url, rates):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        if "No products found" in soup.text:
            return False, [] 
        else:
            return True, extract_products(soup, rates)
    except requests.RequestException as e:
        print(f"Error while checking the page: {e}")
        return None, []

def send_discord_webhook(product):
    color = 0x91f795 if not product['sold_out'] else 0xff5151
    webhook_payload = {
        "content": None,
        "embeds": [
            {
                "title": product['name'],
                "description": f"[**Buy now!**]({product['detail_link']})\nMessage sent at <t:{int(time.time())}:F>",
                "color": color,
                "fields": [
                    {"name": "Price in GBP", "value": f"```{product['price_gbp']}```", "inline": True},
                    {"name": "Price in EUR", "value": f"```{product['price_eur']}```", "inline": True},
                    {"name": "Price in CHF", "value": f"```{product['price_chf']}```", "inline": True}
                ],
                "author": {
                    "name": "Archive 89 Monitor",
                    "url": "https://github.com/d-suter/archive-89-monitor"
                },
                "footer": {"text": "Archive 89 Monitor"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "thumbnail": {"url": product['image_url']}
            }
        ],
        "attachments": []
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=webhook_payload)
        if response.status_code in [401, 403, 429]:
            return False
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Webhook send failed: {e}")
        return False

def save_products(products, file_path):
    with open(file_path, 'w') as file:
        json.dump(products, file, indent=4)

def monitor_website(base_url, rates, existing_products, file_path):
    new_products = False

    for current_page in range(1, 100):
        url = f"{base_url}?page={current_page}"
        print(f"Checking {url}")
        exists, products = check_page(url, rates)

        if exists is None:
            print("Error occurred. Stopping the monitoring.")
            break
        elif not exists:
            print(f"No products found on page {current_page}. Moving to next cycle.")
            break
        else:
            for product in products:
                product_id = product['detail_link']
                if product_id not in existing_products:
                    print(f"New product found: {product['name']}")
                    success = send_discord_webhook(product)
                    if not success:
                        print("Webhook failed, waiting for 1 minute before retrying...")
                        time.sleep(60)
                        send_discord_webhook(product)
                    existing_products[product_id] = product
                    new_products = True

        if new_products:
            save_products(existing_products, file_path)

    time.sleep(1200)

# Main execution
exchange_rates = load_exchange_rates("exchange-rate.json")
existing_products = load_existing_products("products.json")
base_url = "https://archive89.com/collections/all"
monitor_website(base_url, exchange_rates, existing_products, "products.json")
