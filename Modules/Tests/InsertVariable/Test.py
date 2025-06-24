import math
import random
import matplotlib.pyplot as plt


def expand_bit_groups(number, bit_group_size):
    group_size = 1 << bit_group_size
    group_mask  = (1 << group_size) - 1
    expanded_value = 0
    bit_shift = 0
    # Get the total number of bits in n
    number_of_bits = number.bit_length()
    # Iterate over the number of groups in representation
    for i in range(0, number_of_bits, group_size):
        group = number & group_mask
        expanded_value  |= (group << bit_shift) | (group << (bit_shift + group_size))
        bit_shift += 2 * group_size
        number >>= group_size

    return expanded_value

def doTest():
    random_number = 64335 #random.getrandbits(L)
    print(f"Oryginalna liczba:\n{bin(random_number)}\n")
    s=str(bin(random_number))
    s= '0b ' + ' '.join(s[2:])
    print(f"Oryginalna liczba (binarnie):\n{s}\n")

    for n in range(3):
        print(f"n = {n}")
        print(s)
        print(' ' + bin(expand_bit_groups(random_number, n)))
