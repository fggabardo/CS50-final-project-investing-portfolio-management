from functools import wraps
from flask import session, request, redirect
import sqlite3
import requests
from dotenv import load_dotenv
import os

load_dotenv()

FMP_key = os.getenv("FMP_key")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_db_connection():
    conn = sqlite3.connect('site.db', check_same_thread=False)
    return conn


def read_sql(query, parameters=[]):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if len(parameters) > 0:
        query_result =  cur.execute(query, parameters).fetchall()

    else:
        query_result =  cur.execute(query).fetchall()

    conn.close()

    i = 0
    for result in query_result:
        query_result[i] = dict(result)
        i += 1

    return query_result


def to_sql(query, parameters=[]):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if len(parameters) > 0:
        cur.execute(query, parameters)

    else:
        cur.execute(query)

    conn.commit()
    conn.close()


def search_investments(exchangeShortName=None, type=None):
    list = []
    url=f'https://financialmodelingprep.com/api/v3/stock/list?apikey={FMP_key}'
    
    try:
        r = requests.get(url)
        r = r.json()
    except:
        return None

    if not exchangeShortName and not type:
        list = r
    
    elif not exchangeShortName and type:
        for stock in r:
            if stock['type'] == type:
                list.append(stock)

    elif exchangeShortName and not type:
        for stock in r:
            if stock['exchangeShortName'] == exchangeShortName:
                list.append(stock)

    else:
        for stock in r:
            if stock['exchangeShortName'] == exchangeShortName and stock['type'] == type:
                list.append(stock)

    return list


def get_current_price(symbol, type='stock'):

    if (type == 'stock') or (type == 'etf'):
        url=f'https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_key}'
        r = requests.get(url)
        try:
            return r.json()[0]['price']
        except:
            return 0
    
    elif type == 'crypto':
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
        r = requests.get(url)
        try:
            return r.json()['market_data']['current_price']['usd']
        except:
            return 0


def search_cryptos():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin"

    try:
        response = requests.get(url)
        coins = response.json()
        coins_return = {
            'id': coins['id'],
            'symbol': coins['symbol'],
            'name': coins['name']
        }
        return [coins_return]
    
    except:
        return None

    
    

# conn = get_db_connection()
# cur = conn.cursor()
# rows = cur.execute("SELECT * FROM users WHERE username = ?", ("1"))
# tables = cur.fetchall()
# conn.close()