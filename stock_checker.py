import os
import time
import requests
from bs4 import BeautifulSoup

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
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

def send_discord(message):
    r = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=15
    )
    r.raise_for_status()


def fetch_with_retries(url, retries=6):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            session = requests.Session()

            response = session.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            if response.status_code == 200:
                return response.text

            if response.status_code in {500, 502, 503, 504}:
                print(
                    f"Server error {response.status_code}, "
                    f"attempt {attempt}/{retries}"
                )

                last_error = Exception(
                    f"HTTP {response.status_code}"
                )

                time.sleep(5)
                continue

            response.raise_for_status()

        except requests.RequestException as e:
            last_error = e

            print(
                f"Request failed, attempt {attempt}/{retries}: {e}"
            )

            time.sleep(5)

    raise last_error


def check_stock(url):
    html = fetch_with_retries(url)

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if "out of stock" in text:
        return False

    if "add to cart" in text or "in stock" in text:
        return True

    return None


for name, url in PRODUCTS.items():

    try:
        status = check_stock(url)

        if status is True:
            print(f"IN STOCK: {name}")

            send_discord(
                f"🚨🚨 **PS5 IN STOCK** 🚨🚨\n\n"
                f"**{name}**\n"
                f"{url}\n\n"
                f"BUY NOW"
            )

        elif status is False:
            print(f"Out of stock: {name}")

        else:
            print(f"Unknown stock status: {name}")

            send_discord(
                f"⚠️ **PS5 checker could not determine stock status**\n\n"
                f"{name}\n"
                f"{url}\n\n"
                f"Check the page manually."
            )

    except Exception as e:
        print(f"FAILED: {name}: {e}")

        send_discord(
            f"🔥 **MTC PS5 PAGE IS ERRORING** 🔥\n\n"
            f"{name}\n"
            f"The site returned errors after repeated retries.\n\n"
            f"This can happen during heavy traffic/restocks.\n"
            f"CHECK MANUALLY NOW:\n{url}"
        )
