import bcrypt

print(bcrypt.hashpw("1234".encode(), bcrypt.gensalt()))