import csv
from dotenv import load_dotenv
import json
import os
import pdb
import requests
import datetime
def parse_response(response_text):


    # response_text can be either a raw JSON string or an already-converted dictionary
    if isinstance(response_text, str): # if not yet converted, then:
        response_text = json.loads(response_text) # convert string to dictionary

    results = []
    time_series_daily = response_text["Time Series (Daily)"] #> a nested dictionary
    for trading_date in time_series_daily: # FYI: can loop through a dictionary's top-level keys/attributes
        #pdb.set_trace()

        prices = time_series_daily[trading_date] #> {'1. open': '101.0924', '2. high': '101.9500', '3. low': '100.5400', '4. close': '101.6300', '5. volume': '22165128'}
        result = {
            "date": trading_date,
            "open": prices["1. open"],
            "high": prices["2. high"],
            "low": prices["3. low"],
            "close": prices["4. close"],
            "volume": prices["5. volume"]
        }
        results.append(result)
    return results

def write_prices_to_file(prices=[], filename="db/{AAPL}_prices.csv"):
    csv_filepath = os.path.join(os.path.dirname(__file__), "..", filename)
    with open(csv_filepath, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for d in prices:
            row = {
                "timestamp": d["date"], # change attribute name to match project requirements
                "open": d["open"],
                "high": d["high"],
                "low": d["low"],
                "close": d["close"],
                "volume": d["volume"]
            }
            writer.writerow(row)

if __name__ == '__main__': # only execute if file invoked from the command-line, not when imported into other files, like tests

    load_dotenv() # loads environment variables set in a ".env" file, including the value of the ALPHAVANTAGE_API_KEY variable

    api_key = os.environ.get("ALPHAVANTAGE_API_KEY") or "OOPS. Please set an environment variable named 'ALPHAVANTAGE_API_KEY'."

    # CAPTURE USER INPUTS (SYMBOL)

    symbols = []
    while True:
        symbol = input("Please input a stock symbol  (e.g. 'NFLX'):" )
        if symbol == "DONE":
            break
        elif symbol == "CLEAN": #CLEAN UP THE DB FILE
            csv_filenames = os.listdir("../db")
            print("Here are the list for all past file:",csv_filenames)
            for filename in csv_filenames:
                filepath = os.path.join(os.path.dirname(__file__), "..", "db/"+ symbol +"_prices.csv")
            delete_symbol = input("Please enter the stock symbol to delete from file (e.g. 'NFLX'):")
            os.remove(os.path.join(os.path.dirname(__file__), "..", "db/"+ delete_symbol +"_prices.csv"))
            print(f"The ticker symbol:{delete_symbol} has been deleted from file")
            break
        else:
            symbols.append(symbol)
            # VALIDATE SYMBOL AND PREVENT UNECESSARY REQUESTS
            try:
                float(symbol)
                quit("CHECK YOUR SYMBOL. EXPECTING A NON NUMERIC SYMBOL")
            except ValueError as e:
                pass


        # ASSEMBLE REQUEST URL
        request_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}"
        #request_url_weekly = f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={api_key}&outputsize=full"
        # ISSUE "GET" REQUEST
        print("ISSUING A REQUEST")
        response = requests.get(request_url)
        #response_weekly = requests.get(request_url_weekly)
        # VALIDATE RESPONSE AND HANDLE ERRORS
        if "Error Message" in response.text:
            print("REQUEST ERROR, PLEASE TRY AGAIN. CHECK YOUR STOCK SYMBOL.")
            quit("Stopping the program")

        # PARSE RESPONSE (AS LONG AS THERE ARE NO ERRORS)
        daily_prices = parse_response(response.text)
        #weekly_prices =parse_response(response_weekly.text)

        # WRITE TO CSV
        write_prices_to_file(prices=daily_prices, filename="db/"+ symbol +"_prices.csv")

        # PERFORM CALCULATIONS
        #PRINT selected stock symbol
        print("-------------------------")
        print("TICKER SYMBOL:" + symbol)
        print("-------------------------")
        #PRINT date and time when the program was executed
        print("RUN AT: ", datetime.datetime.now().strftime("%-I:%M%p on %b %dth, %Y"))
        print("----------------------------------")
        #PRINT date when the data was last refreshed
        refreshed_date = parse_response(response.text)
        latest_refeshed_date = refreshed_date[0]["date"]
        print("LATEST DATA REFRESHED ON: " + latest_refeshed_date)
        #PRINT latest closing price,
        latest_closing_price = daily_prices[0]["close"]
        latest_closing_price = float(latest_closing_price)
        latest_closing_price_usd = "${0:,.2f}".format(latest_closing_price)
        print(f"LATEST DAILY CLOSING PRICE FOR {symbol} IS: {latest_closing_price_usd}")

        #print its recent average high price
        daily_high = parse_response(response.text)
        #time_series = parse_response(response.text)
        recent_high_price =[]
        for h in daily_prices:
            high_price = h["high"]
            recent_high_price.append(high_price)
        recent_average_high_price = float(max(recent_high_price))
        recent_average_high_price_usd = "${0:,.2f}".format(recent_average_high_price)
        print(f"RECENT AVERAGE HIGH PRICE FOR {symbol} IS: {recent_average_high_price_usd}")
        #print its recent average low price
        recent_low_price =[]
        for l in daily_prices:
            low_price = l["low"]
            recent_low_price.append(low_price)
        recent_average_low_price = float(min(recent_low_price))
        recent_average_low_price_usd = "${0:,.2f}".format(recent_average_low_price)
        print(f"RECENT AVERAGE LOW PRICE FOR {symbol} IS: {recent_average_low_price_usd}")

        # PRODUCE FINAL RECOMMENDATION

        if latest_closing_price > recent_average_high_price:
            print("RECOMMENDATION: Sell")
            print(f"Reason: {symbol}'s lastest closing price exceed the past 100 days maximum average high price")
            print("Great time to sell")
            print("---------------------------------------")
        elif latest_closing_price < recent_average_low_price:
            print("RECOMMENDATION: Buy")
            print(f"Reason: {symbol}'s lastest closing price is below the past 100 days minimum average low price")
            print("Great time to buy!")
            print("---------------------------------------")
        else:
            print("RECOMMENDATION: CURRENTLY NOT AVALIABLE")
            print("---------------------------------------")
