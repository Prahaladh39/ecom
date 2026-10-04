"""
Database Setup and Seeder Script
Initializes the database schema and seeds initial sample listings with real images.
"""
from werkzeug.security import generate_password_hash
import database

def seed_database():
    print("=" * 60)
    print("Initializing School Marketplace Database...")
    print("=" * 60)
    
    # 1. Initialize schema
    database.init_db()
    db_type = database.get_active_db_type()
    print(f"[Info] Active Database Engine: {db_type.upper()}")

    # 2. Seed Demo Users if not present
    demo_users = [
        {
            "name": "Arjun Sharma",
            "class": "Class 12 - Science (PCM)",
            "email": "arjun@school.edu",
            "phone": "919876543210",
            "password": "password123"
        },
        {
            "name": "Riya Patel",
            "class": "Class 12 - Science (PCB)",
            "email": "riya@school.edu",
            "phone": "919876543211",
            "password": "password123"
        }
    ]

    for u in demo_users:
        existing = database.get_user_by_email(u["email"])
        if not existing:
            pwd_hash = generate_password_hash(u["password"])
            database.create_user(u["name"], u["class"], u["email"], u["phone"], pwd_hash)
            print(f"[Seed] Created demo student: {u['name']} ({u['email']})")

    user_arjun = database.get_user_by_email("arjun@school.edu")
    user_riya = database.get_user_by_email("riya@school.edu")

    arjun_id = user_arjun['id'] if user_arjun else 1
    riya_id = user_riya['id'] if user_riya else 1

    # 3. Seed Sample Products if fewer than 4 exist
    existing_products = database.get_all_products()
    if len(existing_products) < 4:
        # Clear existing and cleanly insert the 4 sample products
        database.execute_query("DELETE FROM products", commit=True)
        sample_products = [
            {
                "user_id": arjun_id,
                "title": "CBSE Class 12 NCERT PCM Complete Textbook Set",
                "category": "Textbooks",
                "price": 450.00,
                "phone": "919876543210",
                "description": "Official NCERT Class 12 Part 1 & 2 textbooks for Physics, Chemistry, and Mathematics. Excellent condition with neatly highlighted important derivations, formulas, and solved exercises. Must-have for CBSE Boards & JEE Main preparation.",
                "img1": "sample_books_1.jpg",
                "img2": None,
                "img3": None
            },
            {
                "user_id": riya_id,
                "title": "Casio FX-991EX ClassWiz Advanced Scientific Calculator",
                "category": "Electronics",
                "price": 799.00,
                "phone": "919876543211",
                "description": "Original Casio FX-991EX ClassWiz scientific calculator with 552 functions, natural textbook high-resolution display, and dual solar + battery power. Sparingly used for 6 months, scratch-free screen with slide-on protective hard case.",
                "img1": "sample_calc_1.jpg",
                "img2": None,
                "img3": None
            },
            {
                "user_id": arjun_id,
                "title": "Arduino Uno R3 Ultimate Robotics & Science Exhibition Kit",
                "category": "Project Kits",
                "price": 1250.00,
                "phone": "919876543210",
                "description": "Complete STEM microcontroller electronics kit including genuine Arduino Uno board, breadboard, HC-SR04 ultrasonic distance sensor, 16x2 blue backlit LCD display, jumper wires, LEDs, pushbuttons, and buzzer. Perfect for Class 12 Physics & CS practical projects.",
                "img1": "sample_arduino_1.jpg",
                "img2": None,
                "img3": None
            },
            {
                "user_id": riya_id,
                "title": "Handwritten Class 12 Physics & Chemistry Topper Revision Notes",
                "category": "Study Notes",
                "price": 299.00,
                "phone": "919876543211",
                "description": "Comprehensive color-coded spiral-bound revision notes covering all chapters of CBSE Class 12 Physics & Chemistry. Includes formula sheets, quick concept mind-maps, key diagrams, and past 10-year recurring board questions with step-by-step solutions.",
                "img1": "sample_notes_1.jpg",
                "img2": None,
                "img3": None
            }
        ]

        for p in sample_products:
            database.create_product(
                user_id=p["user_id"],
                title=p["title"],
                category=p["category"],
                price=p["price"],
                phone=p["phone"],
                description=p["description"],
                img1=p["img1"],
                img2=p["img2"],
                img3=p["img3"]
            )
            print(f"[Seed] Added product: {p['title']} (Rs. {p['price']})")

    print("=" * 60)
    print("Database setup & seeding completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
