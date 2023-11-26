import os
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DB_URL")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_ENDPOINT_SECRET = os.getenv("STRIPE_ENDPOINT_SECRET")
FLASK_APP_SECRET_KEY = os.getenv("FLASK_APP_SECRET_KEY")
# COINBASE_ENDPOINT_SECRET = os.getenv("COINBASE_ENDPOINT_SECRET")


if DB_URL is None:
    raise Exception("DB_URL not set in .env file")
elif STRIPE_API_KEY is None:
    raise Exception("STRIPE_API_KEY not set in .env file")
elif STRIPE_ENDPOINT_SECRET is None:
    raise Exception("STRIPE_ENDPOINT_SECRET not set in .env file")
elif FLASK_APP_SECRET_KEY is None:
    raise Exception("FLASK_APP_SECRET_KEY not set in .env file")
# elif COINBASE_ENDPOINT_SECRET is None:
#     raise Exception("COINBASE_ENDPOINT_SECRET not set in .env file")
else :
    print("All environment variables set")