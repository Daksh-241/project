from cryptography.fernet import Fernet
import json

# Generate a test key
key = Fernet.generate_key()
f = Fernet(key)

# Test data
test_data = {
    "name": [{
        "family": "Smith",
        "given": ["John", "Robert"]
    }],
    "address": [{
        "line": ["123 Main St", "Apt 4B"],
        "city": "Boston"
    }]
}

# Encrypt function
def encrypt_string(text: str, fernet: Fernet) -> str:
    if not text:
        return text
    return f.encrypt(text.encode()).decode('utf-8')

# Test encryption
print("=== Encryption Test ===")
print("\nOriginal Data:")
print(json.dumps(test_data, indent=2))

# Encrypt sensitive fields
encrypted_data = dict(test_data)
encrypted_data["name"][0]["family"] = encrypt_string(test_data["name"][0]["family"], f)
encrypted_data["name"][0]["given"] = [encrypt_string(g, f) for g in test_data["name"][0]["given"]]
encrypted_data["address"][0]["line"][0] = encrypt_string(test_data["address"][0]["line"][0], f)

print("\nEncrypted Data:")
print(json.dumps(encrypted_data, indent=2))

# Verify encryption occurred
print("\nVerification:")
print(f"Family name changed: {test_data['name'][0]['family'] != encrypted_data['name'][0]['family']}")
print(f"Given names changed: {test_data['name'][0]['given'] != encrypted_data['name'][0]['given']}")
print(f"Address line changed: {test_data['address'][0]['line'][0] != encrypted_data['address'][0]['line'][0]}")
print(f"City unchanged: {test_data['address'][0]['city'] == encrypted_data['address'][0]['city']}")

# Test decryption
decrypted_family = f.decrypt(encrypted_data["name"][0]["family"].encode()).decode('utf-8')
print(f"\nDecryption test - family name: {decrypted_family == test_data['name'][0]['family']}")