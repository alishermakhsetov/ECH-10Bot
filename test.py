import bcrypt

print(bcrypt.hashpw("admin1234".encode(), bcrypt.gensalt()))
