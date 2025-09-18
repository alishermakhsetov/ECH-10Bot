import bcrypt

print(bcrypt.hashpw("admin112233".encode(), bcrypt.gensalt()))
