import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

PRODUCTS = {
    "PS5 Disc Edition CFI-1x15A":
        "https://mtcfactoryoutlet.com/product/playstation-5-ps5-disc-edition-console-cfi-1x15a-no-stand-included-2/",

    "PS5 Slim Disc Edition CFI-2x15A":
        "https://mtcfactoryoutlet.com/product/playstation-5-ps5-slim-disc-edition-console-cfi-2x15a/",
}

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131 Safari/537.36"
    )
}


def check_stock(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if "out of stock" in text:
        return False

    if "add to cart" in text or "in stock" in text:
        return True

    return None


def send_alert(name, url):
    message = {
        "content": (
            f"🚨 **PS5 STOCK ALERT** 🚨\n\n"
            f"**{name} appears to be IN STOCK!**\n\n"
            f"{url}"
        )
    }

    response = requests.post(
        DISCORD_WEBHOOK,
        json=message,
        timeout=20
    )

    response.raise_for_status()


def log_restock(name, url):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open("restocks.log", "a", encoding="utf-8") as f:
        f.write(f"{now} - IN STOCK - {name} - {url}\n")


for name, url in PRODUCTS.items():
    try:
        status = check_stock(url)

        if status is True:
            print(f"IN STOCK: {name}")
            log_restock(name, url)
            send_alert(name, url)

        elif status is False:
            print(f"Out of stock: {name}")

        else:
            print(f"Could not determine status: {name}")

    except Exception as e:
        print(f"Error checking {name}: {e}")
