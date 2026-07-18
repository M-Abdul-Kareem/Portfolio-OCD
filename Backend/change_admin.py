"""
Change the admin account's username, password, and/or notification email.

Usage:
    python change_admin.py

You'll be prompted for each field. Leave a field blank and press Enter
to keep the current value unchanged.

Run this from inside the Backend/ folder (same place as seed.py).

Note: once the 2FA feature is set up, you can also change your username
and password directly from the admin panel's Account page — this script
is mainly useful for the very first setup, or as a recovery tool if you
ever get locked out of the panel itself.
"""
import getpass
from app.database import SessionLocal
from app.models import AdminUser
from app.auth import hash_password

db = SessionLocal()
admin = db.query(AdminUser).first()

if not admin:
    print("❌ No admin account found. Run seed.py first.")
    db.close()
    exit(1)

print(f"Current username: {admin.username}")
print(f"Current email:    {admin.email or '(not set)'}\n")

new_username = input("New username (leave blank to keep current): ").strip()
new_email = input("New notification email (leave blank to keep current): ").strip()
new_password = getpass.getpass("New password (leave blank to keep current, input hidden): ").strip()

if new_username:
    admin.username = new_username

if new_email:
    admin.email = new_email

if new_password:
    admin.password_hash = hash_password(new_password)

# Changing credentials via this recovery script also clears any lockout,
# in case that's why you needed to use it.
admin.failed_attempts = 0
admin.locked_until = None

db.commit()
db.close()

print("\n✅ Admin account updated.")
print(f"   Username: {new_username or admin.username}")
print(f"   Email:    {new_email or admin.email or '(not set)'}")
print("   Password: (changed)" if new_password else "   Password: (unchanged)")
