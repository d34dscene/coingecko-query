# Coingecko Query
Ulauncher Extension for coingecko

Available commands:
 - keyword cryptocurrency-symbol (e.g. `c eth`) 
   - Shows the current price of the cryptocurrency using the default fiat currency.
 - keyword cryptocurrency-symbol fiat-symbol (e.g. `c eth eur`)
   - Shows the current price of the cryptocurrency using a custom fiat currency.
 - keyword cryptocurrency-symbol multiplier (e.g. `c eth 3`) 
   - Shows the current price of the cryptocurrency multiplied by this number.
 - keyword cryptocurrency-symbol fiat-symbol multiplier (e.g. `c eth eur 3`)
   - Stacking the previous commands.
 - keyword up (e.g. `c up`)
   - Update local database
 
It's possible to set the default keyword, cryptocurrency and fiat currency in the preferences.
The update command can be used to manually update the database of coingecko in case new coins get added. Use it if the extension doesn't find your coin and you're sure it exists on coingecko.
