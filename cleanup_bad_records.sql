-- CLEAN EXISTING BAD RECORDS (RUN ONCE)
-- Remove WhatsApp service IDs (120363xxxxx)
DELETE FROM message_inbox
WHERE phone_number LIKE '120363%';

-- Remove group chats (@g.us suffixes)
DELETE FROM message_inbox
WHERE phone_number LIKE '%@g.us';

-- Verify cleanup results
SELECT COUNT(*) as remaining_individual_chats 
FROM message_inbox 
WHERE phone_number NOT LIKE '120363%' 
AND phone_number NOT LIKE '%@g.us'
AND chat_type = 'individual';
