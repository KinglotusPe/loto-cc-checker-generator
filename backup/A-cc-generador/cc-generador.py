import random

def generate_cc_number(length=16):
    number = "".join(random.choices("0123456789", k=length - 1))
    check_digit = calculate_luhn_checksum(number)
    return f"{number}{check_digit}"

def calculate_luhn_checksum(card_number):
    check_sum = 0
    for i in range(len(card_number)):
        digit = int(card_number[i])
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        check_sum += digit
    return (10 - (check_sum % 10)) % 10

if __name__ == "__main__":
    # Define the desired length of the credit card number (default is 16)
    cc_length = 16

    # Generate a random credit card number
    cc_number = generate_cc_number(cc_length)

    # Print the generated credit card number
    print(cc_number)
