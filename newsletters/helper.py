
import random


def random_string(size, chars='abcdefghjkmnopqrstuvwxyz0123456789'):
    return ''.join(random.choice(chars) for _ in range(size))

def random_token(size):
    fnp = random.randint(1,size)
    return '%s%d%s' % (random_string(fnp-1), random.randint(0, 9), random_string(size-fnp))
