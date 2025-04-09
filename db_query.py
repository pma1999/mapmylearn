import sqlite3

# Connect to the database
conn = sqlite3.connect('learni.db')
cursor = conn.cursor()

# Count users
cursor.execute('SELECT COUNT(*) FROM users')
user_count = cursor.fetchone()[0]
print(f"Number of users in the database: {user_count}")

# Get user details
cursor.execute('SELECT id, email, full_name, is_admin FROM users')
users = cursor.fetchall()
print("\nUser details:")
for user in users:
    user_id, email, full_name, is_admin = user
    print(f"ID: {user_id}, Email: {email}, Name: {full_name}, Admin: {is_admin}")

# Close the connection
conn.close() 