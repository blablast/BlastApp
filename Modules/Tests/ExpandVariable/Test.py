import timeit
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

# Function to test bitwise shift approach
def run_bit_shift(n):
    """
    Perform bitwise shift operations to calculate a value.
    Parameters:
        n (int): The upper limit for the shifting process.
    Returns:
        int: Result of the bitwise shift calculation.
    """
    a = l = 2
    while l < n:
        a = (a << l) | a
        l <<= 1
    return a


# Function to test mathematical approach
def run_math(n):
    """
    Perform mathematical calculation using bitwise operations.
    Parameters:
        n (int): The upper limit for the calculation.
    Returns:
        int: Result of the mathematical calculation.
    """
    a = l = 2
    a = a * (1 << n - 1) // (1 << l - 1)
    return a

# Function to test and time both approaches with specific parameters
def test_expand_variable(i, number):
    """
    Test and time the execution of the bitwise shift and mathematical approaches.
    Parameters:
        i (int): Exponent to determine the size of n (n = 2^i).
        number (int): Number of iterations to repeat each test for timing.
    Returns:
        dict: Results containing parameters and execution times for both methods.
    """

    n = 1 << i  # Calculate n as 2^i

    def bit_shift_test():
        run_bit_shift(n)

    def math_test():
        run_math(n)

    bit_shift_time = timeit.timeit(bit_shift_test, number = number)
    math_time = timeit.timeit(math_test, number = number)

    return {
        'i': i,
        'Runs': number,
        'run_bit_shift_time (s)': bit_shift_time / number,
        'run_math_time (s)': math_time / number,
        'ratio': bit_shift_time / math_time
    }


# Main testing loop
def doTest():
    test_expand_variable(i = 0, number = 10)
    results = []
    number = 1000
    df_results = pd.DataFrame()
    for i in range(40):  # Testing for i = 0 to 31
        result = test_expand_variable(i=i, number=number)
        print(pd.DataFrame([result]))
        results.append(result)
        if results[-1]['run_math_time (s)'] * number > 1:
            number //= 10
            number = max(number, 1)

        df_results = pd.DataFrame(results)
        df_results.to_csv("bit_shift_vs_math_results.csv", index = False)

    # Display the DataFrame in the console
    display(df_results)

    # Plotting the results
    plt.figure(figsize = (12, 6))
    plt.plot(df_results['i'], df_results['ratio'], label = 'Bit Shift Time to Math Time Ratio', marker = 'o')

    plt.xlabel('i (Exponent, N = 2^i)')
    plt.ylabel('Ratio of Bit Shift Time to Math Time')
    plt.title('Performance Comparison: Bit Shift vs Math')
    plt.legend()
    plt.grid(True)
    plt.xticks(range(df_results['i'].min(), df_results['i'].max() + 1))  # Set x-axis ticks at every integer
    plt.grid(axis = 'x', which = 'both', linestyle = '--', linewidth = 0.5)  # Add grid lines for x-axis
    plt.grid(axis = 'y', which = 'both', linestyle = '--', linewidth = 0.5)  # Add grid lines for y-axis
    plt.savefig("bit_shift_vs_math_comparison.png", dpi = 300, bbox_inches = 'tight')
    plt.show()