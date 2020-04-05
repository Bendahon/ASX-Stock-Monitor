# <-------------------------------------------------------------->
# |Stock market monitoring, ideally on an AWS account            |
# |ASX only rn. modify yourself for your own country             |
# |Before the sun dries up and turns us to sand                  |
# |Do you remember when the ocean went mad                       |
# |Bendahon 2020                                                 |
# <-------------------------------------------------------------->

# Limit of 5 API calls a minute so need to slow it down
from time import time, sleep
from alpha_vantage.timeseries import TimeSeries
import json
# Checking if markets open
import pytz
from datetime import datetime, date
# Live data from Yahoo Finance
from bs4 import BeautifulSoup
import urllib.error
import urllib.parse
import urllib.request
# Directory making, file checking and such
import os
# For creating HighLow
from lxml import etree as ET
# Converting historical to XML
from json2xml import json2xml
from json2xml.utils import readfromurl, readfromstring, readfromjson


# We need to module this shit
# Bendahon globals
ProgramName = "stocky"
# Lets keep logs local
# BendahonBaseDir = f"{os.getenv('HOME')}/.bendahon/"
BendahonBaseDir = f"./logs/"
ProgramFolderName = BendahonBaseDir + f"{ProgramName}/"
LocalCurrentStocks = "./ASX_stocks/"
InvalidStockFolder = "./ASX_invalid/"
StockFolder = "./ASX_company/"
StockFile = f"{StockFolder}codes.txt"
KeyFile = f"./key.txt"

StatusFileName = f"{ProgramFolderName}ASX_Log"

# Some global vars
ASX_Codes = []
KEY = ""
market_open = False
per_minute_count = 1


def load_key_file():
    global KEY
    if os.path.isfile(KeyFile):
        file = open(KeyFile)
        KEY = file.read()
        file.close()
        write_to_log_file(f"Key loaded: {KEY}")
    else:
        write_to_log_file(f"You need to add a key in the file: {KeyFile}")
        exit(1)


def check_if_market_open():
    global market_open
    days_open = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    aedt = pytz.timezone("Australia/Sydney")
    time_now = datetime.now(aedt)
    current_hour = time_now.strftime("%H")
    if int(current_hour) <= 10 or int(current_hour) >= 16:
        write_to_log_file("Market is closed!")
        market_open = False
    else:
        if time_now.strftime("%a") in days_open:
            write_to_log_file("Market is open!")
            market_open = True
    market_open = True


def check_if_stock_file_exits():
    if not os.path.isfile(StockFile):
        write_to_log_file(f"Stock file not found, creating at: {StockFile}")
        write_to_log_file(f"Add each 3 letter code seperated by a newline")
        file = open(StockFile, "w")
        file.write("CBA")
        file.close()


def get_asx_codes():
    global ASX_Codes
    check_if_stock_file_exits()
    file = open(StockFile)
    opls = file.read().split('\n')
    file.close()
    # randomly adds a null at the end of opls, lets fix that
    for i in opls:
        if len(i) == 3:
            ASX_Codes.append(i.upper())


def get_historical_data(current_asx):
    try:
        write_to_log_file(f"Trying {current_asx} for historical")
        ts = TimeSeries(key=KEY)
        # data, meta_data = ts.get_daily(f'ASX:{Current_ASX}')
        data, meta_data = ts.get_daily_adjusted(f'ASX:{current_asx}')
        convert_to_xml = json2xml.Json2xml(data).to_xml()
        # If you want as a json file with pretty formatting
        # json_dump = json.dumps(data, indent=4)
        return convert_to_xml
    except ValueError as err:
        # print("Error {0}".format(str(err.args[0])).encode("utf-8"))
        byte_error = err.args[0].encode("utf-8")
        str_decode = byte_error.decode()
        # print(str_decode)
        if "Invalid API call" in str_decode:
            write_to_log_file("Invalid API Call bro")
            return "None"
        else:
            print("Failed due to making too many calls")
            print("Waiting 60 seconds to try again")
            sleep(60)
            get_historical_data(current_asx)


def get_live_price(current_asx):
    # Test url = https://au.finance.yahoo.com/quote/CBA.AX
    write_to_log_file(f"Trying {current_asx} for live price")
    stock_url = f"https://au.finance.yahoo.com/quote/{current_asx}.AX"
    response = urllib.request.urlopen(stock_url)
    getmystrings = response.read()
    soup = BeautifulSoup(getmystrings, "html.parser")
    opls = []

    live_price = ""
    for tag in soup.find_all('span'):
        # print(tag)
        opls.append(tag)
    for string in opls:
        if str(string).startswith(
                '<span class="Trsdu(0.3s) Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(b)" data-reactid="14">'):
            live_price = str(string)

    live_price = live_price.replace(
        '<span class="Trsdu(0.3s) Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(b)" data-reactid="14">', "")
    live_price = live_price.replace('</span>', "")
    # write_to_log_file(live_price)
    return live_price


def check_folders_exits():
    # write_to_log_file("Checking folder integrity")
    if not os.path.exists(BendahonBaseDir):
        print("Default folder doesnt exit, creating")
        os.mkdir(BendahonBaseDir)
    if not os.path.exists(ProgramFolderName):
        print(f"{ProgramName} folder doesn't exist, creating")
        os.mkdir(ProgramFolderName)
    if not os.path.exists(LocalCurrentStocks):
        print("stocks folder doesn't exist, creating")
        os.mkdir(LocalCurrentStocks)
    if not os.path.exists(InvalidStockFolder):
        print("Invalid folder doesn't exist, creating")
        os.mkdir(InvalidStockFolder)
    if not os.path.exists(StockFolder):
        print("Stocks folder does'nt exist, creating")
        os.mkdir(StockFolder)


def write_to_log_file(writeme):
    print(writeme)
    # This might be stupidly inefficient
    my_time_zone = pytz.timezone("Australia/Brisbane")
    time_now = datetime.now(my_time_zone)
    clock_info = time_now.strftime("%d-%m-%Y %H:%M:%S")
    statfile.write(f"{clock_info} {writeme}\n")


def check_if_new_stock(current_asx):
    global per_minute_count
    if os.path.exists(f"{InvalidStockFolder}{current_asx}"):
        write_to_log_file(f"Found invalid stock file: {current_asx}.")
        write_to_log_file(f"To fix you need to delete from ./invalid/")
        write_to_log_file(f"or delete from the monitored stock list")
        write_to_log_file(f"located: {StockFolder}")
        return
    if not os.path.exists(f"{LocalCurrentStocks}/{current_asx}"):
        write_to_log_file(f"Found new stock {current_asx}, checking if alpha and yahoo have it")
        yahoo_price = get_live_price(current_asx)
        daily_price = get_historical_data(current_asx)
        if yahoo_price != "" and daily_price != "None":
            os.mkdir(f"{LocalCurrentStocks}{current_asx}")
            file = open(f"{LocalCurrentStocks}{current_asx}/live_price", "w")
            file.write(yahoo_price + "\n")
            file.close()
            file = open(f"{LocalCurrentStocks}{current_asx}/history.xml", "w")
            file.write(str(daily_price))
            file.close()
            highlow_filename = f"{LocalCurrentStocks}{current_asx}/highlow.xml"
            make_new_high_low(highlow_filename, yahoo_price)
            write_to_log_file(f"Added stock: {current_asx}")
        else:
            write_to_log_file("Invalid stock name. See below")
            write_to_log_file(f"Yahoo - {yahoo_price}")
            write_to_log_file(f"alpha - {daily_price}")
            write_to_log_file("Adding to invalid list, manually delete under ./invalid/ to retry")
            if os.path.exists(f"{InvalidStockFolder}{current_asx}"):
                return
            os.mkdir(f"{InvalidStockFolder}{current_asx}")
            per_minute_count += 1
    else:
        return 0


def make_new_high_low(filename, current_price):
    current_price = float(current_price)
    high_price = str(current_price + 10)
    if current_price <= 11:
        low_price = str(3)
    else:
        low_price = str(current_price - 10)
    root = ET.Element('root')
    level1 = ET.SubElement(root, 'pricing')
    main_text = ET.SubElement(level1, 'Text')
    main_text.text = 'Use this to modify a high/low price monitor'
    second1 = ET.SubElement(level1, 'High_Price')
    second1.text = high_price
    second1 = ET.SubElement(level1, 'Low_Price')
    second1.text = low_price
    tree = ET.ElementTree(root)
    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")


def append_live_price(current_asx, price):
    filename = f"{LocalCurrentStocks}{current_asx}/live_price"
    if os.path.isfile(filename):
        # If it exists, lets flush over a certain amount
        check_if_file_needs_flush(filename)
        file = open(filename, "a+")
        file.write(price + "\n")
        file.close()


def check_if_file_needs_flush(file_name):
    # THIS SUCKS
    # Open the file as a readonly
    file = open(file_name, "r")
    readme = file.read().split("\n")
    file.close()
    # If its got more than 100 lines
    if len(readme) > 100:
        write_to_log_file("Flushing 5 items from the list")
        # Delete 5 from the beginning (i hope)
        opls = readme[5:]
        # Rewrite that file.....
        file = open(file_name, "w")
        for i in opls:
            if i != "":
                file.write(i + "\n")
        file.close()


def rewrite_history_file(current_asx, information):
    file = open(f"{LocalCurrentStocks}{current_asx}/history.xml", "w")
    file.write(information)
    file.close()


def main():
    global per_minute_count
    for asx in ASX_Codes:
        # If its a new stock it automatically pulls the info
        # so no need to do it twice
        check_if_new_stock(asx)
        # at this point we should have a folder
        # so we could write live price or historical data here
        if per_minute_count <= 5:
            if market_open:
                live_price = get_live_price(asx)
                append_live_price(asx, live_price)
                per_minute_count += 1
            else:
                historical_data = get_historical_data(asx)
                rewrite_history_file(asx, historical_data)
                # If the markets closed, no need to keep pulling information. Waste of compute
                write_to_log_file("Markets are closed, gonna wait 10 minutes before updating history")
                sleep(600)
                per_minute_count = 1
                # this should just carry on with new stocks if the market opens
                # so you arent stuck waiting to poll all the history if you have a huge list
                check_if_market_open()
        else:
            write_to_log_file("Sleeping for 60 seconds")
            sleep(60)
            per_minute_count = 1


if __name__ == "__main__":
    check_folders_exits()
    # Start a logfile
    current_date = date.fromtimestamp(time())
    get_date_and_time = current_date.strftime('%Y-%m-%d')
    stat_write_file_name = f"{StatusFileName} {get_date_and_time}"
    statfile = open(stat_write_file_name, "w", encoding="utf-8")
    write_to_log_file(f"Generated: {get_date_and_time}")
    write_to_log_file(f"Version 1.1")
    load_key_file()
    while True:
        check_folders_exits()
        check_if_market_open()
        get_asx_codes()
        main()
