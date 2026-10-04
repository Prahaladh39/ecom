import os
import re
import uuid
import urllib.parse
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
import database

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def format_whatsapp_url(phone, product_title, price, seller_name=""):
    """
    Cleans phone number and formats a direct wa.me link with encoded inquiry message.
    """
    cleaned_phone = re.sub(r'[^0-9]', '', str(phone or ''))
    # If 10 digit Indian mobile number, prefix with 91 country code
    if len(cleaned_phone) == 10:
        cleaned_phone = '91' + cleaned_phone

    greeting = f"Hello {seller_name}," if seller_name else "Hello,"
    message = (
        f"{greeting} I found your listing for \"{product_title}\" "
        f"priced at ₹{price:,.2f} on School Marketplace. "
        f"Is it still available? I'd like to buy it!"
    )
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{cleaned_phone}?text={encoded_message}"

@app.context_processor
def inject_global_vars():
    """Inject active user and cart count into all Jinja templates."""
    user = None
    cart_count = 0
    if 'user_id' in session:
        user = database.get_user_by_id(session['user_id'])
        cart_count = database.get_cart_count(session['user_id'])
    else:
        # Session-based guest cart count
        guest_cart = session.get('guest_cart', {})
        cart_count = sum(guest_cart.values())

    return {
        'current_user': user,
        'cart_count': cart_count,
        'db_engine': database.get_active_db_type().upper()
    }

# ==============================================================================
# Routes
# ==============================================================================

@app.route('/')
def index():
    """Home page: Displays product grid, search, and category filters."""
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'newest')

    products = database.get_all_products(category=category, search=search, sort=sort)

    # Attach WhatsApp URL to each product for one-click action
    for p in products:
        p['whatsapp_url'] = format_whatsapp_url(
            phone=p.get('phone'),
            product_title=p.get('title'),
            price=p.get('price', 0),
            seller_name=p.get('seller_name')
        )

    categories = [
        {"id": "all", "name": "All Items", "icon": "bi-grid"},
        {"id": "Textbooks", "name": "Textbooks", "icon": "bi-book"},
        {"id": "Study Notes", "name": "Study Notes", "icon": "bi-journal-text"},
        {"id": "Electronics", "name": "Electronics", "icon": "bi-cpu"},
        {"id": "Project Kits", "name": "Project Kits", "icon": "bi-tools"},
        {"id": "Uniforms", "name": "Uniforms", "icon": "bi-person-badge"},
        {"id": "Stationery", "name": "Stationery", "icon": "bi-pencil"},
        {"id": "Other", "name": "Other", "icon": "bi-tag"}
    ]

    return render_template(
        'index.html',
        products=products,
        categories=categories,
        current_category=category,
        current_search=search,
        current_sort=sort
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Detailed view for a single product listing."""
    product = database.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('index'))

    # Gather images into a clean list
    images = []
    for key in ['image_1', 'image_2', 'image_3']:
        if product.get(key):
            images.append(product[key])

    product['images'] = images
    product['whatsapp_url'] = format_whatsapp_url(
        phone=product.get('phone'),
        product_title=product.get('title'),
        price=product.get('price', 0),
        seller_name=product.get('seller_name')
    )

    return render_template('product_detail.html', product=product)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    """Sell Your Product page (supports uploading up to 3 images, title, price, description, phone)."""
    if 'user_id' not in session:
        flash("Please sign in or create an account to list your product for sale.", "info")
        return redirect(url_for('login', next=url_for('sell')))

    user = database.get_user_by_id(session['user_id'])

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        phone = request.form.get('phone', '').strip()
        description = request.form.get('description', '').strip()

        # Basic validations
        if not title or not category or not price or not phone or not description:
            flash("All fields are required. Please fill in the complete form.", "danger")
            return redirect(url_for('sell'))

        try:
            price_val = float(price)
            if price_val < 0:
                raise ValueError()
        except ValueError:
            flash("Please enter a valid positive price.", "danger")
            return redirect(url_for('sell'))

        # Handle up to 3 uploaded images
        saved_images = [None, None, None]
        files = request.files.getlist('images')

        image_count = 0
        for i, file in enumerate(files):
            if image_count >= 3:
                break
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(file_path)
                saved_images[image_count] = unique_name
                image_count += 1

        # Fallback placeholder if no image uploaded
        if image_count == 0:
            saved_images[0] = 'sample_books_1.jpg'

        # Insert into DB
        product_id = database.create_product(
            user_id=session['user_id'],
            title=title,
            category=category,
            price=price_val,
            phone=phone,
            description=description,
            img1=saved_images[0],
            img2=saved_images[1],
            img3=saved_images[2]
        )

        flash(f"🎉 Awesome! Your product '{title}' is now live on the marketplace.", "success")
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('sell.html', user=user)

@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Edit an existing listing owned by the student."""
    if 'user_id' not in session:
        flash("Please log in to edit your product listing.", "warning")
        return redirect(url_for('login', next=url_for('edit_product', product_id=product_id)))

    product = database.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('my_listings'))

    if product['user_id'] != session['user_id']:
        flash("You are not authorized to edit this listing.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        phone = request.form.get('phone', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not category or not price or not phone or not description:
            flash("All fields are required. Please fill in the complete form.", "danger")
            return redirect(url_for('edit_product', product_id=product_id))

        try:
            price_val = float(price)
            if price_val < 0:
                raise ValueError()
        except ValueError:
            flash("Please enter a valid positive price.", "danger")
            return redirect(url_for('edit_product', product_id=product_id))

        # Start with existing images
        saved_images = [product.get('image_1'), product.get('image_2'), product.get('image_3')]

        # Check for new image uploads
        files = request.files.getlist('images')
        uploaded_valid = [f for f in files if f and f.filename and allowed_file(f.filename)]

        if uploaded_valid:
            # Replace images with the newly uploaded set (up to 3)
            saved_images = [None, None, None]
            for idx, file in enumerate(uploaded_valid[:3]):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(file_path)
                saved_images[idx] = unique_name

        database.update_product(
            product_id=product_id,
            user_id=session['user_id'],
            title=title,
            category=category,
            price=price_val,
            phone=phone,
            description=description,
            img1=saved_images[0],
            img2=saved_images[1],
            img3=saved_images[2]
        )

        flash(f"Listing '{title}' has been successfully updated!", "success")
        return redirect(url_for('product_detail', product_id=product_id))

    return render_template('edit_product.html', product=product)

@app.route('/buy-now/<int:product_id>')
def buy_now(product_id):
    """Directly redirects to WhatsApp with a pre-filled purchase message for the seller."""
    product = database.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('index'))

    wa_url = format_whatsapp_url(
        phone=product.get('phone'),
        product_title=product.get('title'),
        price=product.get('price', 0),
        seller_name=product.get('seller_name')
    )
    return redirect(wa_url)

# ==============================================================================
# Cart Management
# ==============================================================================

@app.route('/cart')
def cart():
    """Displays cart items, total calculation, and WhatsApp checkout option."""
    cart_items = []
    grand_total = 0.0

    if 'user_id' in session:
        items = database.get_cart_items(session['user_id'])
        for item in items:
            item_total = float(item['price']) * item['quantity']
            grand_total += item_total
            wa_link = format_whatsapp_url(
                phone=item.get('seller_phone'),
                product_title=item.get('title'),
                price=item.get('price', 0),
                seller_name=item.get('seller_name')
            )
            item['item_total'] = item_total
            item['whatsapp_url'] = wa_link
            cart_items.append(item)
    else:
        # Guest session cart
        guest_cart = session.get('guest_cart', {})
        for prod_id_str, qty in guest_cart.items():
            p = database.get_product_by_id(int(prod_id_str))
            if p:
                item_total = float(p['price']) * qty
                grand_total += item_total
                wa_link = format_whatsapp_url(
                    phone=p.get('phone'),
                    product_title=p.get('title'),
                    price=p.get('price', 0),
                    seller_name=p.get('seller_name')
                )
                cart_items.append({
                    'product_id': p['id'],
                    'title': p['title'],
                    'category': p['category'],
                    'price': p['price'],
                    'quantity': qty,
                    'image_1': p['image_1'],
                    'seller_name': p.get('seller_name', 'Student Seller'),
                    'seller_phone': p.get('phone'),
                    'item_total': item_total,
                    'whatsapp_url': wa_link
                })

    return render_template('cart.html', items=cart_items, grand_total=grand_total)

@app.route('/cart/add/<int:product_id>', methods=['POST', 'GET'])
def add_to_cart_route(product_id):
    """Adds product to user's cart (supports both AJAX JSON and normal form submission)."""
    product = database.get_product_by_id(product_id)
    if not product:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        flash("Product not found.", "warning")
        return redirect(url_for('index'))

    if 'user_id' in session:
        database.add_to_cart(session['user_id'], product_id)
        count = database.get_cart_count(session['user_id'])
    else:
        # Guest cart in session
        guest_cart = session.get('guest_cart', {})
        str_id = str(product_id)
        guest_cart[str_id] = guest_cart.get(str_id, 0) + 1
        session['guest_cart'] = guest_cart
        session.modified = True
        count = sum(guest_cart.values())

    msg = f"'{product['title']}' added to your cart!"

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': msg,
            'cart_count': count,
            'product_title': product['title']
        })

    flash(msg, "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/cart/remove/<int:product_id>', methods=['POST', 'GET'])
def remove_from_cart_route(product_id):
    """Removes a product from the shopping cart."""
    if 'user_id' in session:
        database.remove_from_cart(session['user_id'], product_id)
    else:
        guest_cart = session.get('guest_cart', {})
        str_id = str(product_id)
        if str_id in guest_cart:
            del guest_cart[str_id]
            session['guest_cart'] = guest_cart
            session.modified = True

    flash("Item removed from your cart.", "info")
    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST', 'GET'])
def clear_cart_route():
    """Clears all items in the shopping cart."""
    if 'user_id' in session:
        database.clear_cart(session['user_id'])
    else:
        session['guest_cart'] = {}
        session.modified = True

    flash("Shopping cart cleared.", "info")
    return redirect(url_for('cart'))

# ==============================================================================
# User Listings Dashboard
# ==============================================================================

@app.route('/my-listings')
def my_listings():
    """Shows all products uploaded by the current student."""
    if 'user_id' not in session:
        flash("Please log in to view your listings.", "warning")
        return redirect(url_for('login'))

    products = database.get_user_products(session['user_id'])
    return render_template('my_listings.html', products=products)

@app.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product_route(product_id):
    """Allows student seller to delete their own product."""
    if 'user_id' not in session:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('login'))

    database.delete_product(product_id, session['user_id'])
    flash("Product listing deleted successfully.", "success")
    return redirect(url_for('my_listings'))

# ==============================================================================
# Authentication (Sign In & Sign Up)
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Sign Up page for students."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        student_class = request.form.get('student_class', '').strip() or 'Class 12'
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not phone or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template('register.html')

        if len(password) < 4:
            flash("Password should be at least 4 characters long.", "warning")
            return render_template('register.html')

        existing = database.get_user_by_email(email)
        if existing:
            flash("An account with this email already exists. Please Sign In.", "warning")
            return redirect(url_for('login'))

        pwd_hash = generate_password_hash(password)
        new_user_id = database.create_user(full_name, student_class, email, phone, pwd_hash)

        # Automatically log user in
        session['user_id'] = new_user_id
        session['user_name'] = full_name

        # Migrate guest cart if any
        guest_cart = session.get('guest_cart', {})
        for prod_id, qty in guest_cart.items():
            for _ in range(qty):
                database.add_to_cart(new_user_id, int(prod_id))
        session.pop('guest_cart', None)

        flash(f"🎉 Welcome {full_name}! Your student account is now active.", "success")
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sign In page for students."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = database.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']

            # Migrate guest cart items to user account
            guest_cart = session.get('guest_cart', {})
            for prod_id, qty in guest_cart.items():
                for _ in range(qty):
                    database.add_to_cart(user['id'], int(prod_id))
            session.pop('guest_cart', None)

            flash(f"Welcome back, {user['full_name']}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash("Invalid email address or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Sign Out."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('index'))

# ==============================================================================
# Project Overview / Examiner Info Page
# ==============================================================================

@app.route('/project-info')
def project_info():
    """Project details page for Class 12 evaluation & viva."""
    return render_template('project_info.html')

if __name__ == '__main__':
    # Initialize database on startup
    database.init_db()
    print("=" * 60)
    print("Starting School E-Commerce Marketplace...")
    print("Database Engine:", database.get_active_db_type().upper())
    print("Access application at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
