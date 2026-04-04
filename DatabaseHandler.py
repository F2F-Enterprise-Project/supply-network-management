import sqlite3
class DatabaseHandler:

    @staticmethod
    def setup_tables():
        db = sqlite3.connect("supplynetwork.db")
        cursor = db.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER DEFAULT 1,

                vendor_id VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL UNIQUE,
                contact_email VARCHAR(255),
                type VARCHAR(50) CHECK (type IN ('Farm', 'Butcher', 'Dairy')),
                reg_state VARCHAR(50) DEFAULT 'New' CHECK (reg_state IN ('New', 'Active', 'Inactive')),
                order_count INT DEFAULT 0,
                last_order TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
                ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,

                category_id VARCHAR(255) NOT NULL UNIQUE,
                parent_category_id VARCHAR(255) REFERENCES categories(category_id),
                category_name VARCHAR(255) NOT NULL,
                level INT CHECK (level IN (1, 2, 3)),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
                ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER DEFAULT 1,

                product_id VARCHAR(255) NOT NULL UNIQUE,
                vendor_id VARCHAR(255) NOT NULL REFERENCES vendors(vendor_id),
                category_id VARCHAR(255) NOT NULL REFERENCES categories(category_id),
                product_name VARCHAR(255) NOT NULL,
                unit VARCHAR(10) CHECK (unit IN ('kg', 'l')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
                ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,

                shipment_id VARCHAR(255) NOT NULL UNIQUE,
                vendor_id VARCHAR(255) NOT NULL REFERENCES vendors(vendor_id),
                shipment_date TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
                ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shipment_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER DEFAULT 1,

                lot_id TEXT NOT NULL UNIQUE,
                shipment_id VARCHAR(255) NOT NULL REFERENCES shipments(shipment_id),
                product_id VARCHAR(255) NOT NULL REFERENCES products(product_id),
                quantity_on_hand DECIMAL(14, 3) NOT NULL CHECK (quantity_on_hand >= 0),
                unit VARCHAR(10) CHECK (unit IN ('kg', 'l')),
                last_restocked_date TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
                ''')
        db.commit()
        db.close()