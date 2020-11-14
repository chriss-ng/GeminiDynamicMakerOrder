from decimal import Decimal, ROUND_DOWN
from pprint import *
import requests
import json
import base64
import hmac
import hashlib
import datetime, time, threading
import os


# user input variables
position = 'buy'        # set to 'buy' or 'sell'
cryptoPair = 'btcusd'   # set crypto trading pair
totalUSD = 60.3         # set total USD to be spent
sleepTime = 5           # set repeating ping timer in seconds

# set amountOfDecimals variable based on cryptoPair
if cryptoPair == 'btcusd':
    amountOfDecimals = 8
else:
    amountOfDecimals = 6

# get totalUSD_Spent by dividing totalUSD by totalUSD_fee
exchangePrice = 1
totalUSD_fee = 1 + .0035
totalUSD_Math = totalUSD/totalUSD_fee
totalUSD_Spent = round(totalUSD_Math, 2)
amountToTrade = totalUSD_Spent/exchangePrice

# gemini API Info
gemini_api_key = os.environ.get('Gemini API Key').encode()
gemini_api_secret = os.environ.get('Gemini API Secret Key').encode()



# functions

# decimal truncater
def truncate_decimal(d, places):
    #Truncate Decimal d to the given number of places.
    return d.quantize(Decimal(10) ** -places, rounding=ROUND_DOWN)


# set amountToTrade by dividing totalUSD_Spent by exchangePrice
def update_amountToTrade():
    global amountToTrade
    amountToTrade_Math = totalUSD_Spent/exchangePrice
    amountToTrade_Truncation = truncate_decimal(Decimal(amountToTrade_Math), amountOfDecimals)
    amountToTrade = float(amountToTrade_Truncation)


# get highest bid/ask price currently available, then
# set new Maker-or-Cancel price to exchangePrice variable
def update_exchangePrice():
    url = 'https://api.{}gemini.com/v1/pubticker/{}'.format(sand, cryptoPair)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if position == 'buy':
        positionSide = 'bid'
        receivedData = float(data.get(positionSide))
        dataMath = receivedData - .01
        evaluatedData = round(dataMath, 2)

        print('             Highest current bid price: ' + str(receivedData))
        print('Setting maker-or-cancel order price at: ' + str(evaluatedData))
        print('')

    if position == 'sell':
        positionSide = 'ask'
        receivedData = float(data.get(positionSide))
        dataMath = receivedData + .01
        evaluatedData = round(dataMath, 2)

        print('             Highest current ask price: ' + str(receivedData))
        print('Setting maker-or-cancel order price at: ' + str(evaluatedData))
        print('')


    global exchangePrice
    exchangePrice = float(evaluatedData)


# posts order based on the updated amountToTrade & exchangePrice variable, set orderID variable
def newOrder():
    endpoint = '/v1/order/new'
    url = 'https://api.gemini.com{}'.format(endpoint)
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple())*1000))

    payload =  {
        "request": endpoint,
        "nonce": payload_nonce,
        "client_order_id": '=312c-932i49',
        "symbol": cryptoPair,
        "amount": amountToTrade,
        "price": exchangePrice,
        "side": position,
        "type": 'exchange limit',
        "options": ['maker-or-cancel']
        }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {
        'Content-Type': "text/plain",
        'Content-Length': "0",
        'X-GEMINI-APIKEY': gemini_api_key,
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': "no-cache"
        }

    response = requests.post(url,
                             headers=request_headers)

    results = response.json()

    print('NEW ORDER:'.center(50, '-'))
    pprint(results)
    print('')

    global orderID
    orderID = results.get('order_id')


# get order status, sets multiple variables
def orderStatus():
    endpoint = '/v1/order/status'
    url = 'https://api.gemini.com{}'.format(endpoint)
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple())*1000))

    payload =  {
        "request": endpoint,
        "nonce": payload_nonce,
        "order_id": orderID
        }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {
        'Content-Type': "text/plain",
        'Content-Length': "0",
        'X-GEMINI-APIKEY': gemini_api_key,
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': "no-cache"
        }

    response = requests.post(url,
                             headers=request_headers)

    results = response.json()

    print('ORDER STATUS:'.center(50, '-'))
    pprint(results)
    print('')

    global remainingAmount, originalAmount, postedExchangePrice, orderCancelled, error
    remainingAmount = results.get('remaining_amount')
    originalAmount = results.get('original_amount')
    postedExchangePrice = results.get('price')
    orderCancelled = results.get('is_cancelled')
    error = results.get('result')

    return originalAmount


# cancel placed orders
def cancelSessionOrders():
    endpoint = '/v1/order/cancel/session'
    url = 'https://api.gemini.com{}'.format(endpoint)
    t = datetime.datetime.now()
    payload_nonce = str(int(time.mktime(t.timetuple())*1000))

    payload =  {
        "request": endpoint,
        "nonce": payload_nonce
        }

    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

    request_headers = {
        'Content-Type': "text/plain",
        'Content-Length': "0",
        'X-GEMINI-APIKEY': gemini_api_key,
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': "no-cache"
        }

    response = requests.post(url,
                             headers=request_headers)

    results = response.json()
    details = results.get('details')

    print('CANCELLED ORDERS:'.center(50, '-'))
    print(details)
    print('')


# initial startup, set startingAmount variable
def init():
    global startingAmount
    update_exchangePrice()
    update_amountToTrade()
    newOrder()
    time.sleep(1)
    startingAmount = orderStatus()
    print('Starting Amount: {}'.format(startingAmount))


# ping every "x" seconds
def ping():
    try:
        global amountToTrade
        orderStatus()

        # if order filled, stop
        if remainingAmount == '0':
            print('ORDER FILLED:'.center(50, '-'))
            os._exit(0)

        # else if error arises, stop
        elif error == 'error':
            print('ORDER FILLED:'.center(50, '-'))
            os._exit(0)

        # else if order is partially filled
        elif remainingAmount != startingAmount:
            threading.Timer(sleepTime, ping).start()
            time.sleep(1)
            print('FETCHING:'.center(50, '-'))
            print('UPDATE: Order partially filled.')
            partialFillAmount = float(remainingAmount) * float(postedExchangePrice)
            partialFillAmount = truncate_decimal(Decimal(partialFillAmount), amountOfDecimals)
            amountToTrade = float(partialFillAmount)
            update_exchangePrice()
            cancelSessionOrders()
            time.sleep(1)
            newOrder()

        # else if order was cancelled
        elif orderCancelled is True:
            threading.Timer(sleepTime, ping).start()
            time.sleep(1)
            print('ORDER WAS CANELLED: '.center(50, '-'))
            update_exchangePrice()
            newOrder()

        # else if was untouched
        elif remainingAmount == originalAmount:
            threading.Timer(sleepTime, ping).start()
            time.sleep(1)
            print('FETCHING:'.center(50, '-'))
            update_exchangePrice()
            cancelSessionOrders()
            time.sleep(1)
            newOrder()
    except:
        os._exit(0)

# main commands
init()
time.sleep(sleepTime)
ping()
