import sqlite3
conn = sqlite3.connect("db/nifty100.db")

conn.execute("""
    UPDATE companies
    SET company_name = 'ABB India Ltd',
        about_company = 'ABB India Ltd is a subsidiary of the Swiss-Swedish multinational ABB Ltd, and is a leader in electrification and automation. It operates through four business segments: Electrification, Motion, Robotics and Discrete Automation, and Process Automation, serving utilities, industries, and OEMs across India and internationally.'
    WHERE company_id = 'ABB'
""")
conn.commit()

row = conn.execute("SELECT company_id, company_name, about_company FROM companies WHERE company_id = 'ABB'").fetchall()
print(row)
conn.close()