
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, get_db_connection, read_sql, to_sql, search_investments, search_cryptos, get_current_price
from datetime import datetime

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():

    user_id = session.get("user_id")
    
    query = """
    WITH table_delta AS 
    (
        SELECT
            user_id
            ,strategy_id
            ,type
            ,investment_id
            ,SUM(CASE WHEN add_or_delete="add" THEN quantity ELSE 0 END) AS total_added
            ,SUM(CASE WHEN add_or_delete="delete" THEN quantity ELSE 0 END) AS total_deleted
        FROM investment_hist
        WHERE user_id = ?
        GROUP BY user_id
            ,strategy_id
            ,type
            ,investment_id
    )
    SELECT 
        user_id
        ,strategy_id
        ,strategies.strategy_name
        ,type
        ,investment_id
        ,total_added - total_deleted AS remaining
    FROM table_delta
    ,strategies
    WHERE total_added > total_deleted
        AND strategies.id = table_delta.strategy_id
    """

    investments_list = read_sql(query, [user_id])

    for investment in investments_list:
        investment['current_price'] = get_current_price(investment['investment_id'], investment['type'])
        investment['current_total_value'] =  investment['current_price'] * investment['remaining']

        investment['current_price_str'] = f"$ {investment['current_price']:,.0f}"
        investment['current_total_value_str'] = f"$ {investment['current_total_value']:,.0f}"

    portfolio_balance = read_sql("""
                            SELECT users_strategies.*, strategies.strategy_name
                            FROM users_strategies 
                            ,strategies
                            WHERE user_id = ?
                                AND strategies.id = users_strategies.strategy_id
                            """,[user_id])
    
    for strategy in portfolio_balance:
        strategy['current_total_value'] = 0

    for strategy in portfolio_balance:
        for investment in investments_list:
            if investment['strategy_id'] == strategy['strategy_id']:
                strategy['current_total_value'] = strategy['current_total_value'] + investment['current_total_value']

    gross_amount = 0
    for strategy in portfolio_balance:
        gross_amount = gross_amount + strategy['current_total_value']

    for strategy in portfolio_balance:
        strategy['per_real'] = strategy['current_total_value'] / gross_amount
        strategy['per_delta'] =  strategy['per_real'] - strategy['per_amount']
        strategy['amount_delta'] = strategy['per_delta'] * gross_amount

        strategy['current_total_value_str']  = f"$ {strategy['current_total_value']:,.0f}"
        strategy['per_real_str']  = f"{strategy['per_real'] * 100:.0f} %"
        strategy['per_amount_str']  = f"{strategy['per_amount'] * 100:.0f} %"
        strategy['per_delta_str']  = f"{strategy['per_delta'] * 100:.0f} %"
        strategy['amount_delta_str']  = f"$ {strategy['amount_delta']:,.0f}"

    return render_template("index.html", portfolio_balance=portfolio_balance, gross_amount=f'$ {gross_amount:,.0f}', investments_list=investments_list)


@app.route("/strategy", methods=["GET", "POST"])
@login_required
def strategy():

    user_id = session.get("user_id")

    strategy_list = read_sql("SELECT * FROM strategies")
    user_strategy = read_sql("""
                            SELECT * FROM users_strategies 
                            WHERE user_id = ?
                            """, [user_id])

    strategy_dict = {}

    for strategy in strategy_list:
        strategy_dict[strategy['id']] = strategy['strategy_name'].capitalize()

    total_amount = 0
    for strategy in user_strategy:
        strategy['strat_name'] = strategy_dict[strategy['strategy_id']]
        strategy['per_amount_str'] = f"{str(int(strategy['per_amount'] * 100))}%"
        total_amount = total_amount + float(strategy['per_amount'] * 100)


    if request.method == "POST":
        # Ensure strategy name was submitted
        if not request.form.get("strategyName"):
            return str(403)

        # Ensure amount was submitted
        elif not request.form.get("amount"):
            return str(403)

        dict_convert = {
            '5%' : 0.05,
            '10%' : 0.1,
            '15%' : 0.15,
            '20%' : 0.2,
            '25%' : 0.25,
            '30%' : 0.3,
            '35%' : 0.35,
            '40%' : 0.4,
            '45%' : 0.45,
            '50%' : 0.5,
            '55%' : 0.55,
            '60%' : 0.6,
            '65%' : 0.65,
            '70%' : 0.7,
            '75%' : 0.75,
            '80%' : 0.8,
            '85%' : 0.85,
            '90%' : 0.9,
            '95%' : 0.95
        }

        strat_id = next(k for k, v in strategy_dict.items() if v == request.form.get("strategyName").capitalize())

        to_sql("UPDATE users_strategies SET per_amount = ? WHERE user_id = ? AND strategy_id = ?"
                    , [dict_convert[request.form.get("amount")], user_id, strat_id])
        
        user_strategy = read_sql("""
                                SELECT * FROM users_strategies 
                                WHERE user_id = ?
                                """, [user_id])

        total_amount = 0
        for strategy in user_strategy:
            strategy['strat_name'] = strategy_dict[strategy['strategy_id']]
            strategy['per_amount_str'] = f"{str(int(strategy['per_amount'] * 100))}%"
            total_amount = total_amount + float(strategy['per_amount'] * 100)


        return render_template("strategy.html", strategy_list=strategy_list, user_strategy=user_strategy, total_amount=f'{str(int(total_amount))}%')


    return render_template("strategy.html", strategy_list=strategy_list, user_strategy=user_strategy, total_amount=f'{str(int(total_amount))}%')


@app.route("/add_stocks", methods=["GET", "POST"])
@login_required
def add_stocks():

    strategy_list = read_sql("SELECT * FROM strategies")

    investments_list = search_investments('NASDAQ', 'stock')
    investments_list = sorted(investments_list, key = lambda x: x['symbol'])

    if request.method == "POST":
        # Ensure strategy was submitted
        if not request.form.get("strategy"):
            return f"Missing Strategy"
        
        # Ensure investment was submitted
        elif not request.form.get("investment"):
            return f"Missing Investment"
        
        # Ensure quantity was submitted
        elif not request.form.get("quantity"):
            return f"Missing Quantity"

        # Ensure amount was submitted
        elif not request.form.get("amount"):
            return f"Missing Amount"
        
        
        to_sql("""INSERT INTO investment_hist (datetime, user_id, strategy_id, type, investment_id, symbol, add_or_delete, quantity, amount, investment_dict)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [datetime.now(), 
                 session.get("user_id"),
                 int(request.form.get("strategy")),
                 'stock',
                 request.form.get("investment"),
                 request.form.get("investment"),
                 request.form.get("add_or_delete"),
                 float(request.form.get("quantity")),
                 float(request.form.get("amount")),
                 str(next((item for item in investments_list if item["symbol"] == request.form.get("investment")), None))
                 ])
        
        # Redirect user to home page
        return redirect("/")
        
    return render_template("add_stocks.html", strategy_list=strategy_list, investments_list=investments_list)


@app.route("/add_etfs", methods=["GET", "POST"])
@login_required
def add_etfs():

    strategy_list = read_sql("SELECT * FROM strategies")

    investments_list = search_investments('NASDAQ', 'etf')
    investments_list = sorted(investments_list, key = lambda x: x['symbol'])

    if request.method == "POST":
        # Ensure strategy was submitted
        if not request.form.get("strategy"):
            return f"Missing Strategy"
        
        # Ensure investment was submitted
        elif not request.form.get("investment"):
            return f"Missing Investment"
        
        # Ensure quantity was submitted
        elif not request.form.get("quantity"):
            return f"Missing Quantity"

        # Ensure amount was submitted
        elif not request.form.get("amount"):
            return f"Missing Amount"
        
        to_sql("""INSERT INTO investment_hist (datetime, user_id, strategy_id, type, investment_id, symbol, add_or_delete, quantity, amount, investment_dict)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [datetime.now(), 
                 session.get("user_id"),
                 int(request.form.get("strategy")),
                 'etf',
                 request.form.get("investment"),
                 request.form.get("investment"),
                 request.form.get("add_or_delete"),
                 float(request.form.get("quantity")),
                 float(request.form.get("amount")),
                 str(next((item for item in investments_list if item["symbol"] == request.form.get("investment")), None))
                 ])
        
        # Redirect user to home page
        return redirect("/")
        
    return render_template("add_etfs.html", strategy_list=strategy_list, investments_list=investments_list)


@app.route("/add_cryptos", methods=["GET", "POST"])
@login_required
def add_crypto():

    strategy_list = read_sql("SELECT * FROM strategies")

    investments_list = search_cryptos()
    investments_list = sorted(investments_list, key = lambda x: x['symbol'])

    if request.method == "POST":
        # Ensure strategy was submitted
        if not request.form.get("strategy"):
            return f"Missing Strategy"
        
        # Ensure investment was submitted
        elif not request.form.get("investment"):
            return f"Missing Investment"
        
        # Ensure quantity was submitted
        elif not request.form.get("quantity"):
            return f"Missing Quantity"

        # Ensure amount was submitted
        elif not request.form.get("amount"):
            return f"Missing Amount"
        
        selected_investment_dict = next((item for item in investments_list if item["id"] == request.form.get("investment")), None)
        
        to_sql("""INSERT INTO investment_hist (datetime, user_id, strategy_id, type, investment_id, symbol, add_or_delete, quantity, amount, investment_dict)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [datetime.now(), 
                 session.get("user_id"),
                 int(request.form.get("strategy")),
                 'crypto',
                 request.form.get("investment"),
                 f'{selected_investment_dict["symbol"]} - {selected_investment_dict["name"]}',
                 request.form.get("add_or_delete"),
                 float(request.form.get("quantity")),
                 float(request.form.get("amount")),
                str(selected_investment_dict)
                 ])
        
        # Redirect user to home page
        return redirect("/")
        
    return render_template("add_cryptos.html", strategy_list=strategy_list, investments_list=investments_list)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return str(403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return str(403)

        # Query database for username
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")]).fetchall()
        conn.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            dict(rows[0])["hash"], request.form.get("password")
        ):
            return f'400 - Invadid username and/or password'

        # Remember which user has logged in
        session["user_id"] = dict(rows[0])["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        # Ensure username was submitted
        if not username:
            return f'400 - Must provide username'
        
        password = request.form.get("password")
        # Ensure password was submitted
        if not password:
            return f'400 - Must provide password'

        confirmation = request.form.get("confirmation")
        # Ensure password confirmation was submitted
        if not confirmation:
            return f'400 - Must confirm password' 
        
        # Ensure password and password confirmation matches
        if password != confirmation:
            return f'400 - Passwords must match'
        
        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, hash) VALUES (?, ?)", [request.form.get("username"), password_hash])
            conn.commit()
            conn.close()

        except:
            return f'400 - User already exists' 
        
        # Redirect user to login'
        return redirect("/login")
        
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
        

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

