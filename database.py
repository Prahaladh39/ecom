import os
import sqlite3
import socket
import re
from config import Config

# DB Mode tracking: 'mysql' or 'sqlite'
CURRENT_DB_TYPE = None

def is_mysql_server_running(host, port, timeout=0.3):
    """Quick socket check to see if MySQL server port is actively listening."""
    target_host = '127.0.0.1' if host in ('localhost', '127.0.0.1') else host
    try:
        with socket.create_connection((target_host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def get_mysql_connection(include_database=True):
    """Attempt to establish a MySQL connection using mysql.connector or pymysql."""
    # Fast pre-check: verify host & port are reachable
    if not is_mysql_server_running(Config.MYSQL_HOST, Config.MYSQL_PORT):
        return None, None

    # Try mysql.connector first
    try:
        import mysql.connector
        conn_params = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'connect_timeout': 2
        }
        if include_database:
            conn_params['database'] = Config.MYSQL_DB
        return mysql.connector.connect(**conn_params), 'mysql.connector'
    except Exception:
        pass

    # Try pymysql as second choice
    try:
        import pymysql
        conn_params = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'connect_timeout': 2,
            'cursorclass': pymysql.cursors.DictCursor
        }
        if include_database:
            conn_params['database'] = Config.MYSQL_DB
        return pymysql.connect(**conn_params), 'pymysql'
    except Exception:
        pass

    return None, None

def get_sqlite_connection():
    """Establish a connection to the SQLite fallback database."""
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_db_connection():
    """Returns an active database connection, automatically falling back to SQLite if MySQL is offline."""
    global CURRENT_DB_TYPE
    
    # Try MySQL first
    mysql_conn, driver = get_mysql_connection(include_database=True)
    if mysql_conn is not None:
        CURRENT_DB_TYPE = 'mysql'
        return mysql_conn, 'mysql'

    # Fallback to SQLite if enabled
    if Config.USE_SQLITE_FALLBACK:
        CURRENT_DB_TYPE = 'sqlite'
        return get_sqlite_connection(), 'sqlite'

    raise ConnectionError("Could not connect to MySQL server, and SQLite fallback is disabled.")

def get_active_db_type():
    """Returns 'mysql' or 'sqlite'."""
    global CURRENT_DB_TYPE
    if CURRENT_DB_TYPE is None:
        try:
            _, db_type = get_db_connection()
            return db_type
        except Exception:
            return 'sqlite'
    return CURRENT_DB_TYPE

def init_db():
    """Initializes the database tables (creates them if they do not exist)."""
    global CURRENT_DB_TYPE
    
    # First, test if MySQL server is running and can create database if missing
    mysql_server_conn, _ = get_mysql_connection(include_database=False)
    if mysql_server_conn is not None:
        try:
            cursor = mysql_server_conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}`;")
            mysql_server_conn.commit()
            cursor.close()
            mysql_server_conn.close()
            CURRENT_DB_TYPE = 'mysql'
            print(f"[Database] Connected to MySQL database '{Config.MYSQL_DB}' successfully.")
        except Exception as e:
            print(f"[Database] MySQL database creation warning: {e}")

    conn, db_type = get_db_connection()

    if db_type == 'mysql':
        try:
            cursor = conn.cursor()
            schema_sql = f"""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                student_class VARCHAR(50) DEFAULT 'Class 12',
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                title VARCHAR(150) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                image_1 VARCHAR(255),
                image_2 VARCHAR(255),
                image_3 VARCHAR(255),
                status VARCHAR(20) DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE KEY user_prod (user_id, product_id)
            );
            """
            for statement in schema_sql.split(';'):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
            cursor.close()
            conn.close()
            print("[Database] MySQL tables verified.")
        except Exception as e:
            print(f"[Database] Error initializing MySQL tables: {e}")
            if Config.USE_SQLITE_FALLBACK:
                print("[Database] Switching to SQLite fallback...")
                CURRENT_DB_TYPE = 'sqlite'
                init_sqlite_tables()
    else:
        init_sqlite_tables()

def init_sqlite_tables():
    """Initializes SQLite schema."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        student_class TEXT DEFAULT 'Class 12',
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        phone TEXT NOT NULL,
        description TEXT NOT NULL,
        image_1 TEXT,
        image_2 TEXT,
        image_3 TEXT,
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE(user_id, product_id)
    );
    """)
    conn.commit()
    conn.close()
    print(f"[Database] SQLite fallback database verified at '{Config.SQLITE_DB_PATH}'.")

def execute_query(query, params=(), commit=False, fetchone=False, fetchall=False):
    """
    Executes a query seamlessly on either MySQL or SQLite.
    Translates '%s' placeholders to '?' automatically if in SQLite mode.
    Always returns dictionaries for row data.
    """
    conn, db_type = get_db_connection()
    result = None
    last_id = None

    try:
        if db_type == 'mysql':
            # Check if connection is mysql.connector or pymysql
            if hasattr(conn, 'cursor'):
                try:
                    cursor = conn.cursor(dictionary=True)
                except TypeError:
                    cursor = conn.cursor()
            else:
                cursor = conn.cursor()

            cursor.execute(query, params)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
            if fetchone:
                result = cursor.fetchone()
                # If pymysql/tuple, ensure it's a dict
                if result and not isinstance(result, dict) and hasattr(cursor, 'description'):
                    cols = [col[0] for col in cursor.description]
                    result = dict(zip(cols, result))
            elif fetchall:
                rows = cursor.fetchall()
                if rows and not isinstance(rows[0], dict) and hasattr(cursor, 'description'):
                    cols = [col[0] for col in cursor.description]
                    result = [dict(zip(cols, row)) for row in rows]
                else:
                    result = rows
            cursor.close()
        else:
            # SQLite mode: translate %s to ?
            sqlite_query = query.replace('%s', '?')
            cursor = conn.cursor()
            cursor.execute(sqlite_query, params)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
            if fetchone:
                row = cursor.fetchone()
                result = dict(row) if row else None
            elif fetchall:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows] if rows else []
            cursor.close()

    finally:
        conn.close()

    if commit:
        return last_id
    return result

# ==============================================================================
# Domain Helper Functions
# ==============================================================================

def get_all_products(category=None, search=None, sort=None):
    """Fetch products with optional category filtering, text search, and sorting."""
    query = """
    SELECT p.*, u.full_name AS seller_name, u.student_class AS seller_class
    FROM products p
    LEFT JOIN users u ON p.user_id = u.id
    WHERE p.status = 'available'
    """
    params = []

    if category and category != 'all':
        query += " AND p.category = %s"
        params.append(category)

    if search:
        query += " AND (p.title LIKE %s OR p.description LIKE %s OR p.category LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if sort == 'price_low':
        query += " ORDER BY p.price ASC"
    elif sort == 'price_high':
        query += " ORDER BY p.price DESC"
    else:
        query += " ORDER BY p.id DESC"

    return execute_query(query, tuple(params), fetchall=True) or []

def get_product_by_id(product_id):
    """Retrieve single product by ID with seller details."""
    query = """
    SELECT p.*, u.full_name AS seller_name, u.student_class AS seller_class, u.email AS seller_email
    FROM products p
    LEFT JOIN users u ON p.user_id = u.id
    WHERE p.id = %s
    """
    return execute_query(query, (product_id,), fetchone=True)

def create_product(user_id, title, category, price, phone, description, img1=None, img2=None, img3=None):
    """Insert a new product listing into the database."""
    query = """
    INSERT INTO products (user_id, title, category, price, phone, description, image_1, image_2, image_3, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available')
    """
    return execute_query(query, (user_id, title, category, price, phone, description, img1, img2, img3), commit=True)

def update_product(product_id, user_id, title, category, price, phone, description, img1=None, img2=None, img3=None):
    """Update an existing product listing owned by the student user."""
    query = """
    UPDATE products
    SET title = %s, category = %s, price = %s, phone = %s, description = %s,
        image_1 = %s, image_2 = %s, image_3 = %s
    WHERE id = %s AND user_id = %s
    """
    execute_query(query, (title, category, price, phone, description, img1, img2, img3, product_id, user_id), commit=True)
    return True

def delete_product(product_id, user_id):
    """Delete product owned by the student user."""
    query = "DELETE FROM products WHERE id = %s AND user_id = %s"
    execute_query(query, (product_id, user_id), commit=True)
    return True

def get_user_products(user_id):
    """Retrieve all listings uploaded by a particular user."""
    query = "SELECT * FROM products WHERE user_id = %s ORDER BY id DESC"
    return execute_query(query, (user_id,), fetchall=True) or []

def get_user_by_email(email):
    """Fetch user by unique email."""
    query = "SELECT * FROM users WHERE email = %s"
    return execute_query(query, (email.lower().strip(),), fetchone=True)

def get_user_by_id(user_id):
    """Fetch user by primary key ID."""
    query = "SELECT * FROM users WHERE id = %s"
    return execute_query(query, (user_id,), fetchone=True)

def create_user(full_name, student_class, email, phone, password_hash):
    """Register a new student user."""
    query = """
    INSERT INTO users (full_name, student_class, email, phone, password_hash)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (full_name, student_class, email.lower().strip(), phone, password_hash), commit=True)

def get_cart_items(user_id):
    """Fetch all cart items for a user with product and seller information."""
    query = """
    SELECT c.id AS cart_id, c.quantity, p.id AS product_id, p.title, p.price, p.phone AS seller_phone,
           p.image_1, p.category, u.full_name AS seller_name
    FROM cart_items c
    JOIN products p ON c.product_id = p.id
    LEFT JOIN users u ON p.user_id = u.id
    WHERE c.user_id = %s
    ORDER BY c.id DESC
    """
    return execute_query(query, (user_id,), fetchall=True) or []

def add_to_cart(user_id, product_id):
    """Add a product to cart or increment quantity if already present."""
    check_query = "SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s"
    existing = execute_query(check_query, (user_id, product_id), fetchone=True)
    if existing:
        update_query = "UPDATE cart_items SET quantity = quantity + 1 WHERE id = %s"
        execute_query(update_query, (existing['id'],), commit=True)
    else:
        insert_query = "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, 1)"
        execute_query(insert_query, (user_id, product_id), commit=True)
    return True

def remove_from_cart(user_id, product_id):
    """Remove a product from user's cart."""
    query = "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s"
    execute_query(query, (user_id, product_id), commit=True)
    return True

def clear_cart(user_id):
    """Clear all items in cart for a user."""
    query = "DELETE FROM cart_items WHERE user_id = %s"
    execute_query(query, (user_id,), commit=True)
    return True

def get_cart_count(user_id):
    """Get the total count of distinct items in cart."""
    if not user_id:
        return 0
    query = "SELECT COUNT(*) as count FROM cart_items WHERE user_id = %s"
    row = execute_query(query, (user_id,), fetchone=True)
    return row['count'] if row else 0
