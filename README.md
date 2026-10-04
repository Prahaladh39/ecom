# 🎓 SchoolMart - School E-Commerce Marketplace
### Class 12 CBSE Computer Science Project (Python + MySQL)

A simple, modern peer-to-peer student marketplace where students can buy, sell, and trade textbooks, study notes, project electronics, and school stationery.

---

## ✨ Features Implemented

1. **Product Browsing & Search**:
   - Homepage grid with instant category filtering (Textbooks, Notes, Electronics, Project Kits, etc.).
   - Keyword search across title, description, and category.
   - Price sorting (Low to High, High to Low, Newest).

2. **Top-Right "Sell Your Product" Button**:
   - Dedicated listing form.
   - Upload **up to 3 images** with instant client-side preview thumbnails.
   - Set Title, Category, Price, Seller WhatsApp Phone Number, and Detailed Description.

3. **Direct WhatsApp "Buy Now"**:
   - Clicking **Buy Now** immediately opens a WhatsApp chat with the student seller (`https://wa.me/...`).
   - Automatically pre-fills a polite purchase message with the item title and price.

4. **Shopping Cart & Live AJAX**:
   - Clicking **Add to Cart** updates the navbar badge count in real-time without reloading the page.
   - Animated toast notification confirms addition.
   - Cart summary page calculates grand total and provides individual checkout buttons.

5. **Student Authentication & Listing Management**:
   - **Sign Up**: Full name, class/grade, school email, phone number, and password.
   - **Sign In**: Secure hashed password verification (`Werkzeug`).
   - **My Listings**: Student dashboard to view, **edit**, and delete their own posted items.
   - **Edit Listings**: Students can update title, category, price, WhatsApp phone number, description, and replace or keep existing photos at any time.

6. **Dual Database Architecture (MySQL + Auto SQLite Fallback)**:
   - Connects to **MySQL Server** using `mysql-connector-python` or `pymysql`.
   - Includes automatic SQLite fallback (`school_ecom.db`) so the project runs on **any computer** even if MySQL is offline or not installed!

---

## 🚀 How to Run the Project

### Step 1: Open Terminal in the Project Folder
Open PowerShell or Command Prompt in:
```bash
c:\Users\venkat66\OneDrive\Desktop\ecom
```

### Step 2: (Optional) Install Dependencies
Dependencies (`Flask`, `mysql-connector-python`, `pymysql`, `Werkzeug`) are already installed. If running on another computer:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
Simply execute:
```bash
python run.py
```
*(Or alternatively: `python app.py`)*

### Step 4: Open in Your Browser
Open any web browser and go to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Demo Login Credentials (For Evaluator/Teacher)
- **Email:** `arjun@school.edu`
- **Password:** `password123`

*(Or register a new student account using the Sign Up page)*

---

## 🗄️ MySQL Database Setup (Optional)
If you have MySQL running locally on your computer:
1. Open [`config.py`](config.py) and adjust your credentials if needed:
   ```python
   MYSQL_HOST = 'localhost'
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = '' # Your MySQL password (or leave empty if no password)
   MYSQL_DB = 'school_ecom_db'
   ```
2. The application will automatically create the database and tables upon startup.
3. You can also manually import the schema using [`schema.sql`](schema.sql) in **MySQL Workbench** or **phpMyAdmin**.
