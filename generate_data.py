from faker import Faker
import json
from random import randint

fake = Faker()
n1 = 10

# to generate customers
customers = {}

for i in range(n1):
    customers[i] = {
        'name': fake.name(),
        'address': fake.address(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'dob': str(fake.date_of_birth()),
        'custID': i,
    }

with open('mockData/customers.json', 'w') as fp:
    json.dump(customers, fp, indent=4)

# to generate accounts
accounts = {}

n2 = 20
accountTypes = ['Checking', 'Savings']

for i in range(n2):
    accounts[i] = {
        'accountType': fake.random_element(elements=accountTypes),
        'openedDate': str(fake.date()),
        'balance': str(fake.pydecimal(left_digits=5, right_digits=2, positive=True)),
        'custID': randint(0, n1-1)
    }

with open('mockData/accounts.json', 'w') as fp:
    json.dump(accounts, fp, indent=4)

# to generate transactions
transactions = {}

n3 = 100

transactionTypes = ['deposit', 'withdrawal', 'transfer', 'payment', 'refund']

for i in range(n3):
    transactions[i] = {
        'transactionDate': fake.date(),
        'transactionType': fake.random_element(elements=transactionTypes),
        'merchantName': fake.company(),
        'transactionAmount': str(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
        'accountID': randint(0, n2-1)
    }

with open('mockData/transactions.json', 'w') as fp:
    json.dump(transactions, fp, indent=4)