# INVESTING PORTFOLIO MANAGEMENT
#### Video Demo:  <https://youtu.be/2Ca6AsJRZ6c>
#### Description:
This project is a web app for investment portfolio management. Whether investing in stocks, real estate, or bitcoin, this app helps users set and control an investment strategy.

The `app.py` file manages all routes and pages generated for the app.

### DB Schema (`site.db`) - SQLite3:
- **users**: Contains all created users, including their usernames and passwords.
- **strategies**: Auxiliary table listing all possible investment strategies.
- **users_strategies**: Stores each user's investment portfolio strategy.
- **investment_hist**: Maintains the history of investments.

### Routes:

#### Route `/` (index):
- The user must be logged in, enforced by the `@login_required` function from `helpers.py`.
- The function used for this route is named `index()`.
- Inside the function, a `user_id` variable is created from `session.get("user_id")`, as it is used multiple times in the function's code. This also facilitates testing the code in different files.
- A query retrieves the user's investment history and calculates their current investment portfolio. The query returns the strategy of each investment, the type (stock, ETF, or crypto), the investment itself, and the remaining quantity of each investment.
- The query results are processed using the `read_sql()` function from `helpers.py`.
- For each investment, its current price is fetched using `get_current_price()` from `helpers.py`.
- The user's current investment strategy is queried using `read_sql()`.
- The system then calculates the current portfolio state and how much it deviates from the strategy.
- Finally, `index.html` is rendered.
- `index.html` uses Jinja to extend the same header (`layout.html`) to every template and generates HTML dynamically by iterating over Python lists.
- The index page displays the current portfolio state versus the strategy and the current status of each investment.

#### Route `/strategy`:
- The user must be logged in, enforced by the `@login_required` function from `helpers.py`.
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `strategy()`.
- First, all existing strategies are queried.
- The user's current strategy is queried and used in `render_template()` for both GET and POST requests.
- The total percentage value of the strategies is calculated to ensure it sums to 100%.
- When the user submits the form to update the strategy, the `to_sql()` function updates the `users_strategies` table.
- Finally, `strategy.html` is rendered.

#### Route `/add_stocks`:
- The user must be logged in, enforced by the `@login_required` function from `helpers.py`.
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `add_stocks()`.
- First, all existing strategies are queried.
- An API request retrieves all stocks listed on NASDAQ using the `search_investments()` function from `helpers.py`. Only NASDAQ-listed investments are included to simplify this version.
- When the user submits the form to add or remove stocks, the `to_sql()` function inserts a new row into the `investment_hist` table.
- If the form is submitted, the user is redirected to the `/` route; otherwise, `add_stocks.html` is rendered.

#### Route `/add_etfs`:
- The user must be logged in, enforced by the `@login_required` function from `helpers.py`.
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `add_etfs()`.
- First, all existing strategies are queried.
- An API request retrieves all ETFs listed on NASDAQ using the `search_investments()` function from `helpers.py`. Only NASDAQ-listed investments are included to simplify this version.
- When the user submits the form to add or remove ETFs, the `to_sql()` function inserts a new row into the `investment_hist` table.
- If the form is submitted, the user is redirected to the `/` route; otherwise, `add_etfs.html` is rendered.

#### Route `/add_cryptos`:
- The user must be logged in, enforced by the `@login_required` function from `helpers.py`.
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `add_crypto()`.
- First, all existing strategies are queried.
- An API request retrieves cryptocurrencies using the `search_cryptos()` function from `helpers.py`. Currently, only Bitcoin is included to simplify this version.
- When the user submits the form to add or remove cryptocurrencies, the `to_sql()` function inserts a new row into the `investment_hist` table.
- If the form is submitted, the user is redirected to the `/` route; otherwise, `add_cryptos.html` is rendered.

#### Route `/login`:
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `login()`.
- Any existing session is cleared to remove any stored `user_id`.
- When the user submits a username and password, the system validates whether the user exists and if the password is correct.
- If the login is successful, the user is redirected to the `/` route.
- If the user accesses the route via a GET request, `login.html` is rendered.

#### Route `/register`:
- This route contains a form, allowing both GET and POST methods.
- The function used for this route is named `register()`.
- When the user submits a username, password, and confirmation, the system checks whether the user already exists and if the password and confirmation match.
- If the registration is successful, the user is redirected to the `/` route.
- If the user accesses the route via a GET request, `register.html` is rendered.

#### Route `/logout`:
- The function used for this route is named `logout()`.
- Any existing session is cleared to remove any stored `user_id`.
- The user is redirected to the `/` route.

### `helpers.py` Functions:
- **`login_required()`**: Ensures that login is required for a route in Flask.
- **`get_db_connection()`**: Connects to the SQLite3 database.
- **`read_sql()`**: Reads an SQL query.
- **`to_sql()`**: Executes an SQL query.
- **`search_investments()`**: Searches for investments using the Financial Modeling Prep API.
- **`get_current_price()`**: Retrieves the current price of an investment using the Financial Modeling Prep API and the CoinGecko API.
- **`search_cryptos()`**: Searches for cryptocurrencies using the CoinGecko API.