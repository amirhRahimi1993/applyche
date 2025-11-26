## Password Hashing Guide

- **Hasher**: `api/security.py` exposes `hash_password()` and `verify_password()` backed by Passlib’s bcrypt implementation.
- **Storage Format**: `hash_password()` returns the full bcrypt string (e.g. `$2b$12$...`). Store it verbatim in the `users.password_hash` column; no extra encoding is needed.
- **Saving a Password**  
  ```python
  from api.security import hash_password
  from api.db_models import User

  user = User(email="foo@example.com")
  user.password_hash = hash_password("ApplyChe#2025")
  session.add(user)
  session.commit()
  ```
- **Authenticating**  
  ```python
  from api.security import verify_password

  if not verify_password(plain_password, user.password_hash):
      raise HTTPException(status_code=401, detail="Invalid credentials")
  ```
- **Length Limit**: Bcrypt accepts at most 72 bytes. `hash_password()` enforces this and raises a `ValueError` if the UTF‑8 encoded password is longer. Trim or reject overly long passwords before hashing.
- **Legacy Plain Text**: `verify_password()` falls back to a direct string comparison if it detects an un-hashed value in the database, easing gradual migrations.
- **Seeding/Test Users**: When creating demo users (see `seed_test_data.py`), always call `hash_password()` before persisting the password so that the login flow and FastAPI authentication remain consistent.



