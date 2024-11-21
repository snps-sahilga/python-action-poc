import os
import logging

def main():
    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()