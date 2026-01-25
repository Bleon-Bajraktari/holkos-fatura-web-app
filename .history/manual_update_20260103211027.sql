-- Skripti përditësimit manual për Holkos Fatura
-- Ekzekutoni këtë në phpMyAdmin ose MySQL Workbench

-- 1. Zgjidh databazën
CREATE DATABASE IF NOT EXISTS holkos_fatura;
USE holkos_fatura;

-- 2. Shto tabelën e cilësimeve
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Shto statusin në fatura (Për pagesat)
-- Nëse kolona ekziston, kjo komandë mund të japë gabim, injorojeni.
SELECT count(*) INTO @exist FROM information_schema.columns 
WHERE table_schema = 'holkos_fatura' AND table_name = 'invoices' AND column_name = 'status';

SET @query = IF(@exist <= 0, 'ALTER TABLE invoices ADD COLUMN status ENUM(\'draft\', \'sent\', \'paid\') DEFAULT \'draft\'', 'SELECT \'Column status already exists\'');
PREPARE stmt FROM @query;
EXECUTE stmt;

-- 4. Hiq 'UNIQUE' nga invoice_number (Për numërim vjetor)
-- Provohet të hiqet indeksi. Nëse nuk ekziston, do të japë gabim, injorojeni.
DROP INDEX invoice_number ON invoices;

-- 5. Shto fushat SMTP te kompania
ALTER TABLE companies ADD COLUMN smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com';
ALTER TABLE companies ADD COLUMN smtp_port INT DEFAULT 587;
ALTER TABLE companies ADD COLUMN smtp_user VARCHAR(255);
ALTER TABLE companies ADD COLUMN smtp_password VARCHAR(255);

-- 6. Shto email te klientët
ALTER TABLE clients ADD COLUMN email VARCHAR(255);

-- 7. Aktivizo feature-in e statusit
INSERT INTO settings (setting_key, setting_value) VALUES ('feature_payment_status', 'true')
ON DUPLICATE KEY UPDATE setting_value = 'true';
