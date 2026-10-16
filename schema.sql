CREATE DATABASE IF NOT EXISTS queue_db_pro;
USE queue_db_pro;

DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS tokens;

CREATE TABLE tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_number VARCHAR(10) NOT NULL,
    customer_name VARCHAR(100) DEFAULT 'Guest',
    customer_phone VARCHAR(20) DEFAULT NULL,
    service_type VARCHAR(50) NOT NULL,
    status ENUM('waiting', 'serving', 'completed', 'cancelled') DEFAULT 'waiting',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    served_at DATETIME NULL,
    completed_at DATETIME NULL,
    INDEX idx_status_date (status, created_at)
) ENGINE=InnoDB;

CREATE TABLE ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_id) REFERENCES tokens(id) ON DELETE CASCADE
) ENGINE=InnoDB;