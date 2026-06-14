import ssl
import sys

# Windows SSL cert store bug patch
# Python's ssl module fails on Windows if there is a corrupted certificate in the Windows Certificate Store.
# We patch _load_windows_store_certs to catch and ignore parsing exceptions.
orig_load = ssl.SSLContext._load_windows_store_certs
def patched_load(self, storename, purpose):
    try:
        orig_load(self, storename, purpose)
    except Exception as e:
        print(f"[Warning] Handled SSL Certificate Store error: {e}", file=sys.stderr)
        pass

ssl.SSLContext._load_windows_store_certs = patched_load

# Run streamlit
from streamlit.web import cli

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", "app.py"]
    cli.main()
