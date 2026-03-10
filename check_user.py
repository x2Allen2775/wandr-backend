import psycopg2
conn = psycopg2.connect("postgresql://postgres:postgres@db.fqizfuewpkxxasazvzno.supabase.co:5432/postgres")
cur = conn.cursor()
cur.execute("SELECT email, phone_verified, kyc_status, legal_name FROM users;")
rows = cur.fetchall()
print(f"Total users: {len(rows)}")
for r in rows:
    print(f"User: {r[0]} | Phone: {r[1]} | KYC: {r[2]} | Name: {r[3]}")
