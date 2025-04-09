-- Check if the 'notes' column exists in the credit_transactions table
PRAGMA table_info(credit_transactions);

-- Add the 'notes' column if it doesn't exist
ALTER TABLE credit_transactions ADD COLUMN notes VARCHAR; 