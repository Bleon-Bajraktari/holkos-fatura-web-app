-- Skripti i Përditësimit Manual - Holkos Fatura v1.2.0
-- Udhëzime:
-- Kopjoni dhe ekzekutoni këto komanda në SQL tab të phpMyAdmin ose Workbench.
-- Nëse merrni error "Duplicate column name" ose "Column already exists", INJOROJENI. Do të thotë që databaza është tashmë e përditësuar.

-- 1. Zgjidh databazën (Sigurohuni që emri është i saktë)
CREATE DATABASE IF NOT EXISTS holkos_fatura;
USE holkos_fatura;

-- 2. Krijimi i Tabelës Settings (nëse mungon)
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Ndryshimet në tabelën Invoices (Faturat)
-- Shto statusin për pagesat
-- SHËNIM: Nëse kjo jep error "Duplicate column name 'status'", është OK.
ALTER TABLE invoices ADD COLUMN status ENUM('draft', 'sent', 'paid') DEFAULT 'draft';

-- Hiq indeksin unik nga numri i faturës (që të lejohen numra të njëjtë në vite të ndryshme)
-- SHËNIM: Nëse kjo jep error "Can't DROP 'invoice_number'; check that column/key exists", është OK.
DROP INDEX invoice_number ON invoices;

-- 4. Ndryshimet në tabelën Companies (Kompania)
-- Shto fushat për dërgimin e email-it
ALTER TABLE companies ADD COLUMN smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com';
ALTER TABLE companies ADD COLUMN smtp_port INT DEFAULT 587;
ALTER TABLE companies ADD COLUMN smtp_user VARCHAR(255);
ALTER TABLE companies ADD COLUMN smtp_password VARCHAR(255);

-- 5. Ndryshimet në tabelën Clients (Klientët)
ALTER TABLE clients ADD COLUMN email VARCHAR(255);

-- 6. Konfigurimi i Feature-it të Statusit
-- Aktivizo 'true' si default
INSERT INTO settings (setting_key, setting_value) 
VALUES ('feature_payment_status', 'true')
ON DUPLICATE KEY UPDATE setting_value = setting_value;

SELECT "Përditësimi përfundoi. Injoroni gabimet 'Duplicate column' nëse keni pasur." as Mesazh;
