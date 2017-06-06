#!/usr/bin python

import os
from donaldbot import DonaldBot

theDonald = DonaldBot()

# Get the current directory's path
dirname = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the book
book = os.path.join(dirname, 'trumpData.txt')
# Have the bot read the book
theDonald.read(book)

response = raw_input("Ask Trump: ")

if "you" in response:
	response == "I"

response = theDonald.generate_text(16, response)
print(" ")
print(response)
