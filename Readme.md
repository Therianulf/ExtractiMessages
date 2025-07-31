# iMessage Conversation Export Process

## Overview
This process extracts iMessage conversations from macOS's chat.db, handling the complexities of iCloud-synced messages where text is stored in attributedBody BLOBs rather than plain text fields.

## Prerequisites
- macOS with Messages app
- Python 3
- SQLite3
- Access to ~/Library/Messages/chat.db (or a copy of it)

## Process Steps

### 1. Initial Database Exploration
```sql
-- Check database structure
.tables

-- Examine message table schema
PRAGMA table_info(message);

-- Check for messages and discover empty text fields
SELECT COUNT(*) FROM message WHERE text IS NULL;
SELECT COUNT(*) FROM message WHERE attributedBody IS NOT NULL;
```

### 2. Handle Discovery (`find_handles.sql`)
```sql
-- Find all handles (contacts)
SELECT ROWID, id, service FROM handle;

-- Search for specific person
SELECT ROWID, id, service 
FROM handle 
WHERE id LIKE '%[PHONE_NUMBER]%';
```

### 3. Message Extraction (`extract_messages.py`)
This Python script:
- Finds all handles for a person (handling multiple SMS/iMessage accounts)
- Extracts messages from both `text` and `attributedBody` fields
- Decodes the NSAttributedString format used by iCloud Messages
- Creates a clean `conversation_clean` table with parsed messages

**Key features:**
- Automatically prefers iMessage handles over SMS
- Handles the complex attributedBody BLOB format
- Preserves sender information and timestamps
- Includes service type (SMS/iMessage) for each message

### 4. Initial Date Filter - 2024 Only  
```sql
-- First attempt: Create table with only 2024 messages
CREATE TABLE conversation_2024 AS
SELECT * 
FROM conversation_clean
WHERE formatted_date >= '2024-01-01' 
  AND formatted_date < '2025-01-01'
ORDER BY utc_timestamp;
```

### 5. Expanded Date Filter - Include Context (`filter_with_context.sql`)
```sql
-- Revised: Create table with last 6 months of 2023 + all of 2024
CREATE TABLE conversation_recent AS
SELECT * 
FROM conversation_clean
WHERE formatted_date >= '2023-07-01'
ORDER BY utc_timestamp;

-- Verify results
SELECT 
    strftime('%Y-%m', formatted_date) as month,
    COUNT(*) as messages,
    SUM(CASE WHEN is_sent = 1 THEN 1 ELSE 0 END) as sent,
    SUM(CASE WHEN is_sent = 0 THEN 1 ELSE 0 END) as received
FROM conversation_recent
GROUP BY month
ORDER BY month;
```

## Final Output
The `conversation_recent` table contains:
- `is_sent`: Boolean (1 = you sent, 0 = you received)
- `message_text`: Clean extracted message text
- `utc_timestamp`: Original timestamp
- `formatted_date`: Human-readable local time
- `service`: SMS or iMessage

## Usage
1. Copy your chat.db file to a working directory
2. Run the Python script: `python extract_messages.py`
3. Enter the phone number when prompted
4. Run the date filtering SQL to create the final table
5. Export or query `conversation_recent` as needed

## Note
This process was necessary because modern macOS stores iMessage content in attributedBody BLOBs when iCloud Messages is enabled, making simple SQL queries insufficient for text extraction.

# Searching the output

## filter by date range in nano seconds:

```sql
DELETE FROM conversation_recent
WHERE utc_timestamp >= 757382400000000000;  -- January 1, 2025 in Apple nanoseconds

DELETE FROM conversation_recent
WHERE utc_timestamp < 694224000000000000;  -- June 1, 2023 in Apple nanoseconds
```



```sql
WITH scored_messages AS (
  SELECT
    message_text,
    utc_timestamp,
    formatted_date,
    (
      CASE WHEN LOWER(message_text) LIKE '%indiana%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%job%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%pickup%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%pick up%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%dropoff%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%drop off%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%weekend%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%friday%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%saturday%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%i can''t%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%i cant%' THEN 1 ELSE 0 END +
      CASE WHEN LOWER(message_text) LIKE '%help%' THEN 1 ELSE 0 END
    ) AS match_score,
    CASE
      WHEN LOWER(message_text) LIKE '%indiana%' THEN 'indiana,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%job%' THEN 'job,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%pickup%' THEN 'pickup,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%pick up%' THEN 'pick up,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%dropoff%' THEN 'dropoff,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%drop off%' THEN 'drop off,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%weekend%' THEN 'weekend,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%friday%' THEN 'friday,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%saturday%' THEN 'saturday,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%i can''t%' THEN 'i can''t,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%i cant%' THEN 'i cant,' ELSE ''
    END ||
    CASE
      WHEN LOWER(message_text) LIKE '%help%' THEN 'help,' ELSE ''
    END AS matched_words
  FROM conversation_recent
)
SELECT
  message_text,
  utc_timestamp,
  formatted_date,
  match_score,
  RTRIM(matched_words, ',') AS matched_words
FROM scored_messages
WHERE match_score > 0
ORDER BY match_score DESC, utc_timestamp DESC;
```

