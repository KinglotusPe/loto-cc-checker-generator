import random
import string

def generate_bins(starting_number, ending_number):
    bins = []

    # Generate random BINs for the given range of card numbers
    for number in range(starting_number, ending_number + 1):
        bin_ = "".join(random.choices(string.digits, k=6))
        bin_number = f"{bin_}{number:09d}"
        bins.append(bin_number)

    return bins

if __name__ == "__main__":
    # Define the range of card numbers to generate BINs for
    starting_number = 1234567890
    ending_number = 1234567899

    # Generate random BINs for the given range of card numbers
    bins = generate_bins(starting_number, ending_number)

    # Print the generated BINs
    for bin_number in bins:
        print(bin_number)
