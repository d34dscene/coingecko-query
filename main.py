from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from pathlib import Path

import requests
import json
from math import log, floor

DATA = Path(__file__).absolute().parent / "data"
ICON = Path(__file__).absolute().parent / "images"


class GeckoExtension(Extension):
    def __init__(self):
        super(GeckoExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        fiat = extension.preferences["conv"].lower()
        symbol = extension.preferences["sym"].lower()
        multiplicator, correct_in = 1, True

        query = event.get_argument() if event.get_argument() else None
        args = [x.lower() for x in query.split()] if query else None
        data = DATA / "coinlist.json"

        # Update command
        if query and args[0] in ["update", "up"]:
            msg = self.download_data(data)
            return msg

        # Check if data exists locally
        if not data.is_file():
            items.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Missing Data",
                    description="Please update via <keyword> up",
                )
            )
            return RenderResultListAction(items)

        with open(data) as a:
            coinlist = json.load(a)

        # Input parser
        if query:
            if len(args) == 1:
                symbol = args[0]
            elif len(args) == 2 and not args[1].isnumeric() and args[1]:
                symbol = args[0]
                fiat = args[1]
            elif len(args) == 2 and args[1].isnumeric():
                symbol = args[0]
                multiplicator = float(args[1])
            elif len(args) == 3 and args[1]:
                symbol = args[0]
                fiat = args[1]
                multiplicator = float(args[2])
            else:
                correct_in = False

        coin_id = [cid for cid in coinlist if cid["symbol"] == symbol][0]["id"]
        correct_in = False if coin_id == None else True

        if correct_in:
            coingecko = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={fiat}&ids={coin_id}"
            info = requests.get(coingecko).json()[0]
            current_price = info["current_price"]
            market_cap = info["market_cap"]
            pcp24 = info["price_change_percentage_24h"]

            # Download missing icons
            icon_pth = ICON / f"{symbol}.png"
            if not icon_pth.exists():
                icon_req = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                icon_url = requests.get(icon_req).json()["image"]["small"]
                r = requests.get(icon_url, stream=True)
                if r.status_code == 200:
                    with open(icon_pth, "wb") as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)

            # Show current crypto price
            price = current_price * multiplicator
            precision = max(floor(log(1/price if price !=0 else 0.01)/log(10))+4, 2)
            items.append(
                ExtensionResultItem(
                    icon=f"images/{symbol}.png",
                    name="{}: {:,.{}f} {}".format(coin_id.capitalize(), price, precision, fiat.upper()),
                    description="Market Cap: {:,.2f} {}\nPrice change 24h: {}%".format(market_cap, fiat.upper(), pcp24),
                    on_enter=CopyToClipboardAction(str(current_price * multiplicator)),
                )
            )
        else:
            # Error message if coin/conversion currency doesn't exist
            items.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Wrong input!",
                    description="Coin doesn't exist or fiat currency isn't supported!",
                )
            )
        return RenderResultListAction(items)

    def download_data(self, data):
        """
        Function to manually update data in case more coins get added to Coingecko
        """
        coinlist = requests.get("https://api.coingecko.com/api/v3/coins/list?include_platform=false").json()
        with open(data, "w") as a:
            json.dump(coinlist, a)

        items = [
            ExtensionResultItem(
                icon="images/icon.png",
                name="Data update complete!",
                description="You can now search your favorite coins!",
            )
        ]

        return RenderResultListAction(items)


if __name__ == "__main__":
    GeckoExtension().run()
