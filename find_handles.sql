-- Find all handles (contacts)
SELECT ROWID, id, service FROM handle;

-- Search for specific person
SELECT ROWID, id, service
FROM handle
WHERE id LIKE '%[PHONE_NUMBER]%';