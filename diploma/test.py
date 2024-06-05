import math


def main(x):
    if x == 0:
        result = 0.99
    elif x == 1:
        result = 0.37
    else:
        result = 49 * (math.cos(main(x - 2)))**3 + math.floor(main(x - 1))
    return result
