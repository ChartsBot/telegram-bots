start_message = """Welcome to the chart bot.
This bot is designed to help channels and individuals navigate in the defi world, and to keep an eye on their investments.
<b>Main commands:</b>
<code>/price or /p token</code> -> displays informations about the price of the token passed as an argument
<code>/chart or /c token</code> -> displays the chart of the token. Can only be refreshed every 30 seconds to avoid spam
<code>/convert amount token (optional: token2)</code> -> convert the amount of token to usd (and eventually to token2 if specified). Note that lambo is a valid token ;)
<b>Social media commands:</b>
<code>/twitter token</code> -> display the last tweet containing the keyword $token
<code>/biz token</code> -> checks 4chan /biz where the thread contains the keyword token
<b>Fun commands:</b>
<code>/gas</code> -> shows current gas price
<code>/gas_spent WALLET</code> -> shows how much a wallet has spent in gas
<code>/timeto TIME</code> -> shows how long it takes until TIME is reached (ex: /timeto 7 pm UTC)
<b>Chat admins specific commands:</b>
<code>/set_default_token TOKEN (optional: token address)</code> -> will default /price, /chart, /twitter and /biz to the token given as an argument. If no address is passed, it'll try to find the token address based on the given ticker. Example: /set_default_token BOOB 0xa9C44135B3a87E0688c41CF8C27939A22dD437c9
<code>/set_faq FAQ</code> -> will print FAQ when someones calls /faq (ex: /set_faq LOREM IPSUM ...)
<b>Other</b>
* If you make the bot admin, it'll scan through all the images sent to the chat, detect with OCR when someone is having trouble buying due to slippage issues, and send a message telling them how to solve this. 
<code>/trending</code> -> Show what is trending based on queries made in this bot. There are anti cheat functionnalities in place, so spamming /price token won't help making the token appear here
"""

message_faq_empty = "No faq defined for this channel (yet). Any admin can add one with <code>/set_faq message</code>"

symbol_gecko = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'XRP': 'ripple',
    'BCH': 'bitcoin-cash',
    'LTC': 'litecoin'
}
