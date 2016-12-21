import os
import sys
from canvastools import app

def main():
    if len(sys.argv) > 0:
        instance_path = sys.argv[1]

    app.secret_key = os.urandom(24)
    app.run(
        debug=True,
        # host='192.168.33.10',
        host='0.0.0.0',
        port=5000,
        )

if __name__ == '__main__':
    main()
