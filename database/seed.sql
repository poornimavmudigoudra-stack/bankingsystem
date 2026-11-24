-- Apex National Bank Seed Data
-- Default Admin Account: username=admin, password=Admin@123
-- Default Customer Account: username=poorvi, password=poorvi@123
-- Additional Customer: username=alex_turner, password=Alex@123

INSERT INTO users (id, full_name, email, username, password_hash, account_number, balance, role, is_active, phone_number, created_at)
VALUES 
(1, 'System Administrator', 'admin@apexbank.com', 'admin', 'scrypt:32768:8:1$YVqSggFC81g9mJrx$f9ee88087cd7a9a9fce19fa8856cee4b1edb5c892e4d007a7e5b5cda1cef0bb975273ec49e45ee03d752b0e7d4261c44e1032e547e7d7f9b309eba3d4a362ecc', '100000000001', 0.0, 'admin', 1, '+1-800-555-0199', datetime('now', '-30 days')),
(2, 'Poornima Veeranagouda', 'poorvi@example.com', 'poorvi', 'scrypt:32768:8:1$XO0WTiS1N3ISjShg$4afccc378dea5e80e9c4936d3f6cd1f90cfea750dbb6c4db7e24e5debac72840d0d05abecee71942d44ab818f526718eb6c5d779920867ff867b52998e04a9ed', '984729104823', 5420.50, 'customer', 1, '+1-555-0142', datetime('now', '-15 days')),
(3, 'Alex Turner', 'alex.turner@example.com', 'alex_turner', 'scrypt:32768:8:1$b5d4HDhoUh4OluMf$c80e6798e10142ec01bb4de4a8bec83490a79a0ad3e31edd096b33f69e6a75718011245714c0b1b1e8c6d89dae1b92f7cba281b7b63bcbf50345f60131416ef9', '847291038291', 12500.00, 'customer', 1, '+1-555-0188', datetime('now', '-10 days'));

INSERT INTO transactions (id, user_id, transaction_type, amount, balance_after, description, recipient_name, recipient_account, reference_id, timestamp)
VALUES
(1, 2, 'deposit', 5000.00, 5000.00, 'Initial Account Opening Deposit', NULL, NULL, 'TXN-INIT001', datetime('now', '-14 days')),
(2, 2, 'deposit', 1000.00, 6000.00, 'Salary Direct Deposit - ACME Corp', NULL, NULL, 'TXN-DEP002', datetime('now', '-7 days')),
(3, 2, 'withdrawal', 300.00, 5700.00, 'ATM Cash Withdrawal - Downtown Branch', 'ATM Branch #102', 'ATM-102', 'TXN-WTH003', datetime('now', '-5 days')),
(4, 2, 'transfer_debit', 279.50, 5420.50, 'Monthly High-Speed Fiber Internet Bill', 'Utility Pay Corp', '847291038291', 'TXN-TRF004', datetime('now', '-2 days')),
(5, 3, 'deposit', 15000.00, 15000.00, 'Wire Transfer Deposit', NULL, NULL, 'TXN-DEP005', datetime('now', '-9 days')),
(6, 3, 'withdrawal', 2500.00, 12500.00, 'Business Equipment Purchase', 'Tech Supplier LLC', 'TECH-889', 'TXN-WTH006', datetime('now', '-4 days'));
