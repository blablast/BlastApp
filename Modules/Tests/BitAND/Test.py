import timeit
import random
import pandas as pd
import os
import matplotlib.pyplot as plt

# Generate two random integers of length 2**i bits
a: int
b: int

def bit_and():
    return a & b


def generate_large_random_int(bit_length):
    """
    Generate a large random integer using os.urandom.
    Parameters:
        bit_length (int): Number of bits for the integer.
    Returns:
        int: A random integer with the given bit length.
    """
    num_bytes = (bit_length + 7) // 8
    random_bytes = int.from_bytes(os.urandom(num_bytes), 'big')
    return random_bytes & ((1 << bit_length) - 1)


# Main testing loop
def doTest():
    results = []
    number = 100
    df_results = pd.DataFrame()

    for i in range(40):  # Testing for i = 0 to 29
        length = 2 ** i
        a = generate_large_random_int(length)
        b = generate_large_random_int(length)

        time = timeit.timeit(bit_and, number=number)
        print(f"i: {i}, bit_len: {a.bit_length()}, time: {time}")
        results.append({'i': i, 'Time (s)': time})
        df_results = pd.DataFrame(results)
        df_results.to_csv("bitwise_and_performance_log.csv", index = False)


    # Convert results to DataFrame


    # Plot the results with a logarithmic y-axis
    plt.figure(figsize = (10, 6))
    plt.plot(df_results['i'], df_results['Time (s)'], marker = 'o', label = 'AND Operation Time')
    plt.xlabel('i (Exponent, Length = 2^i bits)')
    plt.ylabel('Time (s)')
    plt.title('Bitwise AND Operation Performance (Logarithmic Scale)')
    plt.yscale('log')  # Set the y-axis to a logarithmic scale
    plt.grid(True, which = "both", linestyle = '--', linewidth = 0.5)  # Apply grid to both major and minor ticks
    plt.legend()
    plt.savefig("bitwise_and_performance_log.png", dpi = 300, bbox_inches = 'tight')
    plt.show()