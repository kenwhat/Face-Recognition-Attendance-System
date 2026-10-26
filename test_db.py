import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="attendance_db"
)
print("Connected:", conn.is_connected())
conn.close()