# stonks-only-go-up
 Tool to check P/L history from TastyWorks portfolio
 
 Currently uses Selenium to log into your TastyWorks account and grab your current balance
 
 Logs current balance to an sqlite3 database with timestamp
 
 Not sure where this is going yet, may end up using this in a flask app to create interactive P/L chart
 
 Might also implement displaying current positions, not sure yet
 
 ## Requirements
 Currently using selenium as the tastyworks api wrapper was out of my wheelhouse
 
 Install requirements with
 `pip install -r requirements.txt`
 
 ## Webdriver
 Download chromedriver from `https://chromedriver.chromium.org/downloads`
 
 Place the executable in a folder called `driver` in the root directory

Make sure to grab the correct driver based on your version of Chrome and your OS

## Credentials
You will need to supply your TastyWorks credentials

Create a file called `creds.py` in the root directory

Inside of `creds.py`, create a dict with your username and password, like so

```python
creds = {
    'tw_user': 'YOUR_USERNAME',
    'tw_pass': 'YOUR_PASSWORD'
}
```

## Notes
I'm sure I'm missng some other shit. Will update later