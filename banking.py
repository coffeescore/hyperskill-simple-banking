import random
import sqlite3


class CallBankSql:

    def __init__(self):
        self.connection = sqlite3.connect("card.s3db")
        self.cursor = self.connection.cursor()
        self.create_table()

    # what sql operations do we need to support?
    def create_table(self):
        # 1. need to create a table named card
        table = ("\n"
                 "        CREATE TABLE IF NOT EXISTS card (\n"
                 "        id INTEGER,\n"
                 "        number TEXT,\n"
                 "        pin TEXT,\n"
                 "        balance INTEGER DEFAULT 0\n"
                 "        );\n"
                 "        ")

        self.cursor.execute(table)
        self.connection.commit()

    # 2. need to insert cards into the table
    def insert_records(self, record, card_number, pin, balance=0):
        parameters = (record, card_number, pin, balance)
        query = (
            "INSERT INTO card (id, number, pin, balance) "
            "VALUES (?, ?, ?, ?)"
        )

        self.cursor.execute(query, parameters)
        self.connection.commit()
        return None

    # 3. need to get records back
    def get_balance(self, number, pin):
        records = self.cursor.execute("SELECT balance FROM card WHERE number = ? AND pin = ?", (number, pin))
        count = records.fetchone()

        if count is None:
            return False
        else:
            return count[0]

    # 4. need to know the number of previously created accounts
    def count_accounts(self):
        records = self.cursor.execute("SELECT MAX(id) FROM card")
        count = records.fetchone()

        if count[0] is None:
            return (0,)
        else:
            return count

    # 5. need to delete accounts (in reality it would be better to mark it as historical but for now we will delete)
    def delete_account(self, number, pin):
        self.cursor.execute("DELETE FROM card WHERE number = ? AND pin = ?", (number, pin))
        self.connection.commit()

    # 6. add income, pretty self explanatory
    def add_income(self, number, pin, income):
        self.cursor.execute("UPDATE card SET balance = balance + ? "
                            "WHERE number = ? AND pin = ?", (income, number, pin))
        self.connection.commit()

    # 7. transfer account balances
    def transfer_balances(self, account1, account2, transfer):
        # account1 transfer to account2
        self.cursor.execute("UPDATE card SET balance = balance - ? "
                            "WHERE number = ?", (transfer, account1))
        self.cursor.execute("UPDATE card SET balance = balance + ? "
                            "WHERE number = ?", (transfer, account2))
        self.connection.commit()

    def check_account(self, account):
        self.cursor.execute("SELECT number FROM card WHERE number = ?", (account,))
        return self.cursor.fetchone()


class BankingSystem:

    def __init__(self):
        self.db = CallBankSql()
        self.issuer_id = "400000"
        self._count = self.db.count_accounts()
        self.accounts_created = self._count[0]

    def get_options(self):
        print("1. Create an account")
        print("2. Log into account")
        print("0. Exit")

        try:
            return int(input())
        except ValueError:
            return ''

    def log_in(self):
        user_card = input("Enter your card number: ")
        user_pin = input("Enter your PIN: ")

        balance = self.db.get_balance(user_card, user_pin)

        if balance is False:
            print("Wrong card number or PIN!")
            return True
        else:
            tf = self.log_in_actions(user_card, user_pin)
            return tf

    def log_in_actions(self, user_card, user_pin):

        print("You have successfully logged in!")

        while True:
            print("\n")
            print("1. Balance")
            print("2. Add income")
            print("3. Do transfer")
            print("4. Close account")
            print("5. Log out")
            print("0. Exit")
            print("\n")

            user_input = int(input())
            balance = self.db.get_balance(user_card, user_pin)

            if user_input == 1:
                print(f'Balance: {balance}')

            elif user_input == 2:
                income_input = int(input("How much would you like to deposit? "))
                self.db.add_income(user_card, user_pin, income_input)
                print(f"{income_input} has been deposited")

            elif user_input == 3:
                account2 = input("Input the destination account: ")

                if user_card == account2:
                    print("You can't transfer money to the same account!")
                else:
                    if account2[-1] == self.get_luhn_checksum(account2, check=True):
                        records = self.db.check_account(account2)
                        if records:
                            transfer = int(input("Input the transfer amount: "))
                            if balance < transfer:
                                print("Not enough money!")
                            else:
                                self.db.transfer_balances(user_card, account2, transfer)
                        else:
                            print("Such a card does not exist.")
                    else:
                        print("Probably you made mistake in the card number. Please try again!")

            elif user_input == 4:
                self.db.delete_account(user_card, user_pin)
                return True

            elif user_input == 5:
                print("You have successfully logged out!")
                return True

            elif user_input == 0:
                return False
            else:
                print("Invalid Input")
                return None

    def create_account(self):
        # Creates the account number without a checksum
        account_number_no_check = self.issuer_id + format(self.accounts_created, '09d')

        # Creates the PIN
        pin_number = format(random.randint(0000, 9999), '04d')

        # Generates checksum
        checksum = self.get_luhn_checksum(account_number_no_check, check=False)

        # Assembles the account number
        account_number = account_number_no_check + checksum

        # account numbers are created in order so lets increment the account numbers
        self.accounts_created += 1

        # appends the account number and pin number to the database of accounts
        self.db.insert_records(self.accounts_created, account_number, pin_number)

        # print the account numbers out
        print(f"Your card number:\n{account_number}")
        print(f"Your card PIN:\n{pin_number}")

        return None

    def get_luhn_checksum(self, card_number, check=True):
        """
        Takes the card number and checksum.
        Parameters:
        Checksum=True: Optional parameter. If the checksum is True that means the card number includes a checksum.
        Checksum=False: The checksum is not included
        """

        # 1. take in the original number (since its text, i'm going to cast it to a list of integers)
        luhn_card_number = [int(x) for x in card_number]

        # 2. drop the last digit
        if check:
            del luhn_card_number[-1]

        # multiply odd digits by 2 (note that the algorithm uses base 1 but python lists are base 0)
        for i, num in enumerate(luhn_card_number):
            if i % 2 == 0:
                luhn_card_number[i] = num * 2

        # subtract 9 to all numbers over 9
        for i, num in enumerate(luhn_card_number):
            if num > 9:
                luhn_card_number[i] = num - 9

        # add all numbers together
        card_sum = sum(luhn_card_number)
        checksum = 0

        while not card_sum % 10 == 0:
            card_sum += 1
            checksum += 1

        return str(checksum)


bank = BankingSystem()

while True:
    choice = bank.get_options()

    if choice == 1:
        bank.create_account()
    elif choice == 2:
        account_status = bank.log_in()
        if not account_status:
            break
        else:
            continue
    elif choice == 0:
        break
    else:
        print("Input Error")