import sys
import random
import string

print(
    ''.join(
        random.SystemRandom().choice(
            string.ascii_letters + string.digits
            ) for _ in range(
            30
            )
        )
    )
