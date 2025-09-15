import bcrypt

# Parollar
passwords = {
    "Admin@2024!": "admin uchun",
    "Equip@2024!": "equipment uchun",
    "Safety@2024!": "safety uchun"
}

print("🔐 PAROLLAR HASH QILINMOQDA...")
print("=" * 60)

for password, description in passwords.items():
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print(f"📝 {description}")
    print(f"🔑 Parol: {password}")
    print(f"🔒 Hash: {hashed}")
    print("-" * 60)

print("\n✅ Bu hash'larni .env faylga joylashtiring!")