-- Holkos Fatura LOKAL Backup
-- Data: 2026-02-01 20:37:59
CREATE DATABASE IF NOT EXISTS `holkos_fatura1` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `holkos_fatura1`;

DROP TABLE IF EXISTS `clients`;
CREATE TABLE `clients` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` text DEFAULT NULL,
  `unique_number` varchar(50) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `clients` (`id`, `name`, `address`, `unique_number`, `phone`, `email`, `created_at`, `updated_at`) VALUES
(3, 'Fahrije M.Gashi B.I', 'Istog', '811319731', '', '', '2025-12-30 23:40:52', '2025-12-30 23:45:11'),
(4, 'Mercom Company sh.p.k', 'Fazli Grajqevci', '810298548', '', '', '2025-12-30 23:42:12', '2025-12-30 23:42:12'),
(5, 'Mercom L L C sh.p.k', 'Prishtinë', '812101418', '', '', '2025-12-30 23:42:54', '2025-12-30 23:42:54'),
(6, 'N.T.P Driloni Com', 'Prishtinë', '810707383', '', '', '2025-12-30 23:43:55', '2025-12-30 23:43:55'),
(7, 'Gëzim Kastrati', 'Vërmicë Malishevë', '2013381847', '', '', '2025-12-30 23:44:33', '2025-12-30 23:44:33'),
(8, 'Green Residence sh.p.k', 'Rruga Uran Tinova P.N, Ferizaj', '811474444', '', '', '2025-12-30 23:46:19', '2025-12-30 23:46:19'),
(9, 'Tallku sh.p.k', 'Uçk P.N, Pejë', '810962333', '', '', '2025-12-30 23:48:04', '2025-12-30 23:48:04'),
(10, 'Albi Asset Investments sh.p.k', 'Gjilan', '812168327', '', '', '2025-12-30 23:49:24', '2025-12-30 23:49:24'),
(11, 'Arda Rei Group', 'Zona Industriale Boulevard Bill Clinton, Prishtinë', '810852659', '', '', '2025-12-30 23:50:27', '2025-12-30 23:50:27'),
(12, '2 B&A British Building C sh.p.k', 'Prishtinë', '810054388', '', '', '2025-12-30 23:51:27', '2025-12-30 23:51:27'),
(13, 'IBOS IDJ sh.p.k', 'Rr Skenderbeu, Istog', '811890864', '', '', '2025-12-30 23:52:31', '2025-12-30 23:52:31');

DROP TABLE IF EXISTS `companies`;
CREATE TABLE `companies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` text DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `unique_number` varchar(50) DEFAULT NULL,
  `fiscal_number` varchar(50) DEFAULT NULL,
  `account_nib` varchar(50) DEFAULT NULL,
  `logo_path` varchar(500) DEFAULT NULL,
  `smtp_server` varchar(255) DEFAULT 'smtp.gmail.com',
  `smtp_port` int(11) DEFAULT 587,
  `smtp_user` varchar(255) DEFAULT NULL,
  `smtp_password` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `companies` (`id`, `name`, `address`, `phone`, `email`, `unique_number`, `fiscal_number`, `account_nib`, `logo_path`, `smtp_server`, `smtp_port`, `smtp_user`, `smtp_password`, `created_at`, `updated_at`) VALUES
(1, 'HOLKOS', 'Kashice - Istog', '044 224 031', 'holkosmetal@yahoo.com', '811226530', '600610093', '1706017400348068', '', 'smtp.mail.yahoo.com', 587, 'holkosmetal@yahoo.com', 'eakrrxeckipugqll', '2025-12-30 18:59:04', '2025-12-30 19:00:38');

DROP TABLE IF EXISTS `invoice_items`;
CREATE TABLE `invoice_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `invoice_id` int(11) NOT NULL,
  `description` text NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `order_index` int(11) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `invoice_id` (`invoice_id`),
  CONSTRAINT `invoice_items_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `invoice_items` (`id`, `invoice_id`, `description`, `quantity`, `unit_price`, `subtotal`, `order_index`) VALUES
(8, 8, 'Furnizimi dhe montimi i alubondit', '1.00', '847.50', '847.50', 0),
(9, 9, 'Montimi i fasades ventiluese - Frutex', '280.00', '25.00', '7000.00', 0),
(10, 10, 'Montimi i fasades ventiluese', '227.00', '22.00', '4994.00', 0),
(11, 11, 'Montimi i fasades ventiluese - Frutex', '280.00', '25.00', '7000.00', 0),
(12, 12, 'Furnizimi + Montimi i elementeve dekoruese', '1.00', '3813.56', '3813.56', 0),
(13, 13, 'Montimi i fasades ventiluese', '682.00', '22.00', '15004.00', 0),
(14, 14, 'Punimi dhe montimi i fasades ventiluese', '600.00', '26.00', '15600.00', 0),
(15, 15, 'Montimi i fasades ventiluese - Frutex', '304.35', '23.00', '7000.05', 0),
(16, 16, 'Montimi dhe furnizimi i fasades ventiluese', '150.00', '101.70', '15255.00', 0),
(17, 17, 'Montimi i fasades ventiluese', '227.28', '22.00', '5000.16', 0),
(18, 18, 'Montimi i fasades ventiluese - Panorama', '521.74', '23.00', '12000.02', 0),
(19, 19, 'Montimi i fasades ventiluese', '454.55', '22.00', '10000.08', 0),
(20, 20, 'Montimi i fasades ventiluese - Panorama', '304.35', '23.00', '7000.05', 0),
(21, 21, 'Punet e perfunduara allubond', '3452.00', '1.00', '3452.00', 0),
(22, 22, 'Montimi i fasades ventiluese', '454.55', '22.00', '10000.08', 0),
(23, 23, 'Renovimi dhe furnizimi i banjove', '720.34', '1.00', '720.34', 0),
(24, 24, 'Punimi dhe montimi i konstruksionit të çeliktë', '6488.00', '2.50', '16220.00', 0),
(25, 25, 'Montimi i fasades ventiluese', '227.27', '22.00', '5000.03', 0),
(26, 26, 'Montimi i fasades ventiluese', '227.27', '22.00', '5000.03', 0),
(27, 27, 'Montimi i fasades ventiluese', '325.95', '26.00', '8474.70', 0),
(28, 28, 'Montimi dhe furnizimi i fasades ventiluese', '248.00', '101.70', '25221.60', 0),
(29, 29, 'Montimi i fasades ventiluese', '227.28', '22.00', '5000.16', 0),
(30, 30, 'Montimi i fasades ventiluese - qeramikë', '400.00', '28.00', '11200.00', 0),
(32, 32, 'Montimi furnizimi i fasades ventiluese', '105.00', '76.27', '8008.35', 0),
(34, 34, 'Montimi i fasades ventiluese', '227.28', '22.00', '5000.16', 0),
(35, 35, 'Montimi i fasades ventiluese', '227.28', '22.00', '5000.16', 0),
(38, 38, 'Montimi i fasades ventiluese', '227.27', '22.00', '5000.01', 0),
(39, 39, 'Montimi dhe furnizimi i fasades ventiluese', '1.00', '3176.58', '3176.58', 0),
(40, 39, 'Montimi i alubondit dhe furnizimi i profilave dhe', '0.00', '0.00', '0.00', 1),
(41, 39, 'pjeseve percjellese per shterngim', '0.00', '0.00', '0.00', 2);

DROP TABLE IF EXISTS `invoices`;
CREATE TABLE `invoices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `invoice_number` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `payment_due_date` date DEFAULT NULL,
  `client_id` int(11) NOT NULL,
  `template_id` int(11) DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT 0.00,
  `vat_percentage` decimal(5,2) DEFAULT 18.00,
  `vat_amount` decimal(10,2) DEFAULT 0.00,
  `total` decimal(10,2) DEFAULT 0.00,
  `status` enum('draft','sent','paid') DEFAULT 'draft',
  `pdf_path` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  KEY `template_id` (`template_id`),
  CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`),
  CONSTRAINT `invoices_ibfk_2` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `invoices` (`id`, `invoice_number`, `date`, `payment_due_date`, `client_id`, `template_id`, `subtotal`, `vat_percentage`, `vat_amount`, `total`, `status`, `pdf_path`, `created_at`, `updated_at`) VALUES
(8, 'FATURA NR.1', '2025-01-27', NULL, 3, NULL, '847.50', '18.00', '152.55', '1000.05', 'sent', NULL, '2025-12-30 23:54:24', '2025-12-30 23:54:34'),
(9, 'FATURA NR.2', '2025-02-01', NULL, 5, NULL, '7000.00', '0.00', '0.00', '7000.00', 'sent', NULL, '2025-12-30 23:55:27', '2025-12-30 23:55:36'),
(10, 'FATURA NR.3', '2025-02-06', NULL, 4, NULL, '4994.00', '0.00', '0.00', '4994.00', 'sent', NULL, '2025-12-30 23:56:27', '2025-12-30 23:56:37'),
(11, 'FATURA NR.4', '2025-03-01', NULL, 5, NULL, '7000.00', '0.00', '0.00', '7000.00', 'sent', NULL, '2025-12-30 23:57:00', '2025-12-30 23:57:10'),
(12, 'FATURA NR.5', '2025-03-03', NULL, 6, NULL, '3813.56', '18.00', '686.44', '4500.00', 'sent', NULL, '2025-12-30 23:57:53', '2025-12-30 23:58:02'),
(13, 'FATURA NR.6', '2025-04-02', NULL, 4, NULL, '15004.00', '0.00', '0.00', '15004.00', 'sent', NULL, '2025-12-30 23:58:30', '2025-12-30 23:58:40'),
(14, 'FATURA NR.7', '2025-04-23', NULL, 7, NULL, '15600.00', '18.00', '2808.00', '18408.00', 'sent', NULL, '2025-12-30 23:59:23', '2025-12-30 23:59:33'),
(15, 'FATURA NR.8', '2025-05-02', NULL, 5, NULL, '7000.05', '0.00', '0.00', '7000.05', 'sent', NULL, '2025-12-31 00:00:03', '2025-12-31 00:00:14'),
(16, 'FATURA NR.9', '2025-05-12', NULL, 8, NULL, '15255.00', '18.00', '2745.90', '18000.90', 'sent', NULL, '2025-12-31 00:00:51', '2025-12-31 00:01:01'),
(17, 'FATURA NR.10', '2025-05-12', NULL, 4, NULL, '5000.16', '0.00', '0.00', '5000.16', 'sent', NULL, '2025-12-31 00:01:28', '2025-12-31 00:01:38'),
(18, 'FATURA NR.11', '2025-06-03', NULL, 5, NULL, '12000.02', '0.00', '0.00', '12000.02', 'sent', NULL, '2025-12-31 00:03:56', '2025-12-31 00:04:06'),
(19, 'FATURA NR.12', '2025-06-04', NULL, 4, NULL, '10000.08', '0.00', '0.00', '10000.08', 'sent', NULL, '2025-12-31 00:12:44', '2025-12-31 00:12:54'),
(20, 'FATURA NR.13', '2025-07-07', NULL, 5, NULL, '7000.05', '0.00', '0.00', '7000.05', 'sent', NULL, '2025-12-31 00:13:30', '2025-12-31 00:13:40'),
(21, 'FATURA NR.14', '2025-07-17', NULL, 9, NULL, '3452.00', '18.00', '621.36', '4073.36', 'sent', NULL, '2025-12-31 00:14:45', '2025-12-31 00:14:55'),
(22, 'FATURA NR.15', '2025-07-10', NULL, 4, NULL, '10000.08', '0.00', '0.00', '10000.08', 'sent', NULL, '2025-12-31 00:16:18', '2025-12-31 00:16:27'),
(23, 'FATURA NR.16', '2025-07-31', NULL, 10, NULL, '720.34', '18.00', '129.66', '850.00', 'sent', NULL, '2025-12-31 00:17:00', '2025-12-31 00:17:10'),
(24, 'FATURA NR.17', '2025-08-07', NULL, 11, NULL, '16220.00', '18.00', '2919.60', '19139.60', 'sent', NULL, '2025-12-31 00:18:28', '2025-12-31 00:18:38'),
(25, 'FATURA NR.18', '2025-08-08', NULL, 4, NULL, '5000.03', '0.00', '0.00', '5000.03', 'sent', NULL, '2025-12-31 00:19:16', '2025-12-31 00:19:27'),
(26, 'FATURA NR.20', '2025-09-03', NULL, 4, NULL, '5000.03', '0.00', '0.00', '5000.03', 'sent', NULL, '2025-12-31 00:21:15', '2025-12-31 00:21:25'),
(27, 'FATURA NR.21', '2025-09-18', NULL, 7, NULL, '8474.70', '18.00', '1525.45', '10000.15', 'sent', NULL, '2025-12-31 00:22:06', '2025-12-31 00:22:16'),
(28, 'FATURA NR.22', '2025-10-01', NULL, 8, NULL, '25221.60', '18.00', '4539.89', '29761.49', 'sent', NULL, '2025-12-31 00:23:02', '2025-12-31 00:23:12'),
(29, 'FATURA NR.23', '2025-10-06', NULL, 4, NULL, '5000.16', '0.00', '0.00', '5000.16', 'sent', NULL, '2025-12-31 00:26:05', '2025-12-31 00:26:15'),
(30, 'FATURA NR.24', '2025-10-29', NULL, 12, NULL, '11200.00', '18.00', '2016.00', '13216.00', 'sent', NULL, '2025-12-31 00:26:46', '2025-12-31 00:26:56'),
(32, 'FATURA NR.26', '2025-12-08', NULL, 13, NULL, '8008.35', '18.00', '1441.50', '9449.85', 'sent', NULL, '2025-12-31 00:29:31', '2026-01-11 16:14:47'),
(34, 'FATURA NR.27', '2025-12-18', NULL, 4, NULL, '5000.16', '0.00', '0.00', '5000.16', 'sent', NULL, '2025-12-31 00:32:21', '2025-12-31 00:32:30'),
(35, 'FATURA NR.25', '2025-11-03', NULL, 4, NULL, '5000.16', '0.00', '0.00', '5000.16', 'sent', NULL, '2025-12-31 00:32:52', '2025-12-31 00:33:01'),
(38, 'FATURA NR.29', '2025-12-30', NULL, 4, NULL, '5000.01', '0.00', '0.00', '5000.01', 'sent', NULL, '2025-12-31 00:36:42', '2025-12-31 00:36:52'),
(39, 'FATURA NR.28', '2025-12-25', NULL, 8, NULL, '3176.58', '18.00', '571.78', '3748.36', 'sent', NULL, '2025-12-31 00:56:23', '2025-12-31 00:56:32');

DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `settings` (`id`, `setting_key`, `setting_value`, `created_at`, `updated_at`) VALUES
(1, 'feature_payment_status', 'true', '2026-01-03 21:09:39', '2026-01-03 21:27:12');

DROP TABLE IF EXISTS `templates`;
CREATE TABLE `templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `template_file` varchar(500) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `templates` (`id`, `name`, `description`, `template_file`, `is_active`, `is_default`, `created_at`, `updated_at`) VALUES
(1, 'Shablloni Default', 'Shablloni bazë i faturave bazuar në dizajnin e HOLKOS', 'default', 1, 1, '2025-12-30 19:00:01', '2025-12-30 19:00:01');
