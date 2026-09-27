"""Quick manual test of HarakaPay. No database, no FastAPI needed.

Put this file inside the backend/ folder (next to the app/ folder), then run:
    python test_harakapay.py 0712345678 100

What it does:
  1. Reads HARAKAPAY_API_KEY from your .env file
  2. Checks your HarakaPay balance (proves the API key works)
  3. Sends a USSD push to the phone number you gave
  4. Checks the status every 4 seconds until you approve or cancel on the phone
"""
import os
import sys
import time

try:
    from dotenv import load_dotenv  # pip install python-dotenv

    load_dotenv()
except ImportError:
    pass  # fine if you set the variable in the terminal instead

from app.payments.base import PaymentProviderError, PaymentStatus
from app.payments.harakapay import HarakaPayProvider


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python test_harakapay.py <phone> <amount>   e.g. 0712345678 100")
    phone, amount = sys.argv[1], int(sys.argv[2])

    api_key = os.getenv("HARAKAPAY_API_KEY")
    if not api_key:
        sys.exit("HARAKAPAY_API_KEY is missing. Add it to your .env file first.")

    hp = HarakaPayProvider(api_key)
    try:
        print("Balance:", hp.get_balance())

        result = hp.collect(phone, amount, "Smart Taka test")
        print(f"USSD push sent. order_id={result.order_id} fee={result.fee} net={result.net_amount}")
        print("Angalia simu yako na uweke PIN...")

        for _ in range(30):  # about 2 minutes
            time.sleep(4)
            status = hp.get_status(result.order_id)
            print("status:", status.status.value)
            if status.status != PaymentStatus.PENDING:
                print("Final:", status)
                return
        print("Bado pending baada ya dakika 2. Hii ndiyo hali ambayo reconcile_pending inashughulikia.")
    except PaymentProviderError as exc:
        sys.exit(f"HarakaPay error: {exc}")


if __name__ == "__main__":
    main()
