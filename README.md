# Archive 89 Monitor

## Overview
Archive 89 Monitor is a Python script that watches for new products on the Archive 89 website and initially sends every new product to you through Discord notifications.

## Setup
1. Install Python.
2. Install required Python packages using `pip install requests beautifulsoup4`.

## Usage
1. Replace `DISCORD_WEBHOOK_URL` with your Discord webhook URL.
2. Run the script using `python main.py`.

The script checks the website for new products and sends Discord notifications when it finds something new. Initially, every product is sent to you for review.

## Customization
You can adjust the script's behavior by changing variables like `base_url` or the monitoring interval.
