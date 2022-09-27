import json
from math import floor, log
from pathlib import Path

import requests
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import \
    CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import \
    RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

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
        multiplicator = 1

        data = DATA / "coinlist.json"

        # Update command
        if event.get_argument() in ["update", "up"]:
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
        if event.get_argument():
            args = [x.lower() for x in event.get_argument().split()]
            if len(args) > 0:
                symbol = args[0]
                try:
                    if not args[1].isnumeric():
                        fiat = args[1]
                        multiplicator = float(args[2])
                    else:
                        multiplicator = float(args[1])
                except IndexError:
                    pass

            if len(args) > 3:
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="Too many arguments!",
                        description="Example: c eth eur",
                    )
                )
                return RenderResultListAction(items)

        coin_id = None
        for cid in coinlist:
            if cid["symbol"] == symbol:
                coin_id = cid["id"]

        if coin_id != None:
            coingecko = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={fiat}&ids={coin_id}"
            info = requests.get(coingecko)
            if info.status_code != 200:
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="Rate limit exceeded!",
                        description="Please wait 1 minute!",
                    )
                )
                return RenderResultListAction(items)

            current_price = info.json()[0]["current_price"]
            market_cap = info.json()[0]["market_cap"]
            pcp24 = info.json()[0]["price_change_percentage_24h"]

            # Download missing icons
            self.download_icon(coin_id, symbol)

            # Show current crypto price
            price = current_price * multiplicator
            precision = max(
                floor(log(1 / price if price != 0 else 0.01) / log(10)) + 4, 2
            )

            items.append(
                ExtensionResultItem(
                    icon=f"images/{symbol}.png",
                    name="{}: {:,.{}f} {}".format(
                        coin_id.capitalize(), price, precision, fiat.upper()
                    ),
                    description="Market Cap: {:,.2f} {}\nPrice change 24h: {}%".format(
                        market_cap, fiat.upper(), pcp24
                    ),
                    on_enter=CopyToClipboardAction(str(current_price * multiplicator)),
                )
            )
        else:
            # Error message if coin/conversion currency doesn't exist
            items.append(
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Ticker not found!",
                    description="Coin doesn't exist or fiat currency isn't supported!",
                )
            )
        return RenderResultListAction(items)

    def download_data(self, data):
        """
        Function to manually update data in case more coins get added to Coingecko
        """
        ping = requests.get("https://api.coingecko.com/api/v3/ping")
        if ping.status_code != 200:
            items = [
                ExtensionResultItem(
                    icon="images/icon.png",
                    name="Rate limit exceeded!",
                    description="Please wait 1 minute!",
                )
            ]
            return RenderResultListAction(items)

        coinlist = requests.get(
            "https://api.coingecko.com/api/v3/coins/list?include_platform=false"
        ).json()

        ignorelist = ["-wormhole", "binance-peg", "-peg"]
        for idx, coin in enumerate(coinlist):
            if any(i in coin["id"] for i in ignorelist):
                coinlist.pop(idx)

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

    def download_icon(self, coin_id, symbol):
        icon_pth = ICON / f"{symbol}.png"
        if not icon_pth.exists():
            icon_req = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            icon_url = requests.get(icon_req).json()["image"]["small"]
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
            }
            r = requests.get(icon_url, stream=True, headers=headers)
            if r.status_code == 200:
                with open(icon_pth, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)


if __name__ == "__main__":
    GeckoExtension().run()
