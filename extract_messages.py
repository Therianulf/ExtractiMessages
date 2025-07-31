import sqlite3
import os
import re


def extract_text_from_attributed_body(blob):
    """Extract plain text from attributedBody BLOB"""
    try:
        text = blob.decode('utf-8', errors='ignore')
        match = re.search(r'NSString[^\w]*([^__]+?)(?=__kIM|NSDictionary|$)', text)
        if match:
            message = match.group(1)
            message = re.sub(r'[^\w\s\.\!\?\,\:\;\-\(\)\'\"]+$', '', message)
            return message.strip()
    except:
        pass
    return None


# Connect to the database
db_path = os.path.expanduser('~/Library/Messages/chat.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find ALL handles for this person
phone_or_email = input("Enter phone number or email (e.g. +15551234567): ")

print("\nSearching for all handles matching this person...")
cursor.execute("""
    SELECT h.ROWID, h.id, h.service, COUNT(m.ROWID) as message_count
    FROM handle h
    LEFT JOIN message m ON h.ROWID = m.handle_id
    WHERE h.id LIKE ?
    GROUP BY h.ROWID
    ORDER BY h.service DESC, message_count DESC
""", (f'%{phone_or_email}%',))

handles = cursor.fetchall()
if not handles:
    print("No handles found!")
    exit()

print("\nFound handles:")
for handle in handles:
    rowid, handle_id, service, msg_count = handle
    print(f"  ID: {rowid}, Handle: {handle_id}, Service: {service}, Messages: {msg_count}")

# Pick the iMessage handle (service='iMessage') with the most messages
imessage_handles = [h for h in handles if h[2] == 'iMessage']
if imessage_handles:
    # Pick iMessage handle with most messages
    best_handle = max(imessage_handles, key=lambda x: x[3])
else:
    # Fall back to handle with most messages
    print("\nNo iMessage handle found, using handle with most messages")
    best_handle = max(handles, key=lambda x: x[3])

handle_id = best_handle[0]
print(f"\nUsing handle ID {handle_id}: {best_handle[1]} ({best_handle[2]}) with {best_handle[3]} messages")

# Also get all handle IDs for this person (in case they switch between services)
all_handle_ids = [h[0] for h in handles]
print(f"All handle IDs for this person: {all_handle_ids}")

# Create output table
cursor.execute("DROP TABLE IF EXISTS conversation_clean")
cursor.execute("""
    CREATE TABLE conversation_clean (
        is_sent BOOLEAN,
        message_text TEXT,
        utc_timestamp INTEGER,
        formatted_date TEXT,
        service TEXT
    )
""")

# Get all messages in any conversation with ANY of their handles
query = """
    SELECT DISTINCT
        m.ROWID,
        m.text,
        m.attributedBody,
        m.is_from_me,
        m.date,
        datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as formatted_date,
        COALESCE(h.service, c.service_name) as service
    FROM message m
    JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    JOIN chat c ON cmj.chat_id = c.ROWID
    JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    WHERE chj.handle_id IN ({})
      AND (m.text IS NOT NULL OR m.attributedBody IS NOT NULL)
    ORDER BY m.date
""".format(','.join('?' * len(all_handle_ids)))

cursor.execute(query, all_handle_ids)

inserted = 0
skipped = 0

for row in cursor.fetchall():
    rowid, text, attributed_body, is_from_me, date, formatted_date, service = row

    message_text = text
    if not message_text and attributed_body:
        message_text = extract_text_from_attributed_body(attributed_body)

    if message_text:
        cursor.execute("""
            INSERT INTO conversation_clean (is_sent, message_text, utc_timestamp, formatted_date, service)
            VALUES (?, ?, ?, ?, ?)
        """, (bool(is_from_me), message_text, date, formatted_date, service))
        inserted += 1
    else:
        skipped += 1

conn.commit()
print(f"\nInserted {inserted} messages, skipped {skipped}")

# Show statistics
cursor.execute("SELECT COUNT(*), is_sent, service FROM conversation_clean GROUP BY is_sent, service")
print("\nMessage counts:")
for row in cursor.fetchall():
    count, is_sent, service = row
    print(f"  {'Sent' if is_sent else 'Received'} ({service}): {count} messages")

# Show sample
print("\nRecent messages:")
cursor.execute("SELECT * FROM conversation_clean ORDER BY utc_timestamp DESC LIMIT 5")
for row in cursor.fetchall():
    is_sent, text, timestamp, date, service = row
    sender = "You" if is_sent else "Them"
    print(f"\n{date} ({service})")
    print(f"{sender}: {text[:100]}{'...' if len(text) > 100 else ''}")

conn.close()