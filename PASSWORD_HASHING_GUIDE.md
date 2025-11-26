## Password Handling Guide (Temporary Plain-Text Mode)

> ⚠️ **Security Warning**: The project is currently configured to store passwords in plain text for testing convenience.
> Update `api/security.py` to re-enable hashing before deploying to any shared environment.

- **Helpers**: `hash_password()` and `verify_password()` now live in `api/security.py`, but both functions simply return / compare the raw password strings.
- **Saving a Password**  
  ```python
  from api.security import hash_password
  from api.db_models import User

  user = User(email="foo@example.com")
  user.password_hash = hash_password("ApplyChe#2025")  # returns plain text
  session.add(user)
  session.commit()
  ```
- **Authenticating**  
  ```python
  from api.security import verify_password

  if not verify_password(plain_password, user.password_hash):
      raise HTTPException(status_code=401, detail="Invalid credentials")
  ```
- **Restoring Hashing Later**: When you are ready to reinstate bcrypt, swap the helper implementations back to the previous version (see git history) and update any plain-text rows as needed.
