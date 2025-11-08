import bcrypt

def hash_password(password):
    """Hashes the password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_hash, provided_password):
    """Verifies a password against a stored hash."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash)