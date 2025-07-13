from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from app import db, login_manager, csrf
from models import User, Product, Allergen, UserAllergen, ProductAllergen, HealthNews
from forms import RegistrationForm, LoginForm, ProfileForm, AllergenForm, ProductForm, HealthNewsForm
from utils import admin_required, get_safe_products_for_user, get_alternative_products, highlight_allergens_in_ingredients, add_ingredient_as_allergen, get_all_product_ingredients
import logging

# Configure login manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def register_routes(app):
    """Register all application routes"""
    
    # Home page - simple welcome page
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # User registration with Duolingo-style allergen selection
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        
        if form.validate_on_submit():
            try:
                # Create new user
                user = User()
                user.first_name = form.first_name.data.strip()
                user.last_name = form.last_name.data.strip()
                user.email = form.email.data.lower().strip()
                user.password_hash = generate_password_hash(form.password.data)
                
                db.session.add(user)
                db.session.flush()  # Get user ID without committing
                
                # Add selected allergens
                for allergen_id in form.allergens.data:
                    user_allergen = UserAllergen()
                    user_allergen.user_id = user.id
                    user_allergen.allergen_id = allergen_id
                    db.session.add(user_allergen)
                
                db.session.commit()
                
                # Automatically log in the user after registration
                login_user(user)
                flash(f'Welcome to Allergen Alert, {user.first_name}!', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Registration error: {e}")
                flash('Registration failed. Please try again.', 'error')
        
        return render_template('register.html', form=form)
    
    # User login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower().strip()).first()
            
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember_me.data)
                
                # Redirect based on user role
                if user.is_admin:
                    flash(f'Welcome back, Admin!', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash(f'Welcome back, {user.first_name}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')
        
        return render_template('login.html', form=form)
    
    # User logout
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    # User profile management
    @app.route('/profile')
    @login_required
    def profile():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        # Get statistics for the profile
        safe_products_count = len(get_safe_products_for_user(current_user))
        total_products_count = Product.query.count()
        
        return render_template('profile_view.html', 
                             safe_products_count=safe_products_count,
                             total_products_count=total_products_count)
    
    @app.route('/edit-profile', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        form = ProfileForm(original_email=current_user.email)
        
        if form.validate_on_submit():
            try:
                current_user.first_name = form.first_name.data.strip()
                current_user.last_name = form.last_name.data.strip()
                current_user.email = form.email.data.lower().strip()
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
                
            except Exception as e:
                db.session.rollback()
                flash('Profile update failed. Please try again.', 'error')
        
        # Pre-populate form with current user data
        if request.method == 'GET':
            form.first_name.data = current_user.first_name
            form.last_name.data = current_user.last_name
            form.email.data = current_user.email
        
        return render_template('edit_profile.html', form=form)
    
    @app.route('/manage-allergens', methods=['GET', 'POST'])
    @login_required
    def manage_allergens():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            # Handle form submission
            selected_allergens = request.form.getlist('allergens')
            
            try:
                # Clear existing allergens
                UserAllergen.query.filter_by(user_id=current_user.id).delete()
                
                # Add selected allergens
                for allergen_name in selected_allergens:
                    allergen = Allergen.query.filter_by(name=allergen_name).first()
                    if not allergen:
                        # Create new allergen
                        allergen = Allergen(
                            name=allergen_name,
                            description='',
                            is_common=False,
                            user_reported_count=1
                        )
                        db.session.add(allergen)
                        db.session.flush()
                    
                    # Add user-allergen relationship
                    user_allergen = UserAllergen(
                        user_id=current_user.id,
                        allergen_id=allergen.id
                    )
                    db.session.add(user_allergen)
                
                db.session.commit()
                flash('Allergens updated successfully!', 'success')
                return redirect(url_for('profile'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating allergens: {str(e)}', 'error')
        
        # Get all available allergens (existing + ingredients)
        existing_allergens = Allergen.query.order_by(Allergen.name).all()
        product_ingredients = get_all_product_ingredients()
        
        # Combine all options
        all_options = set()
        for allergen in existing_allergens:
            all_options.add(allergen.name)
        all_options.update(product_ingredients)
        
        # Create sorted list
        available_allergens = []
        for name in sorted(all_options):
            existing = next((a for a in existing_allergens if a.name.lower() == name.lower()), None)
            available_allergens.append({
                'name': name,
                'description': existing.description if existing else f"Ingredient from products",
                'is_common': existing.is_common if existing else False
            })
        
        user_allergens = set(current_user.get_allergens())
        
        return render_template('manage_allergens.html', 
                             available_allergens=available_allergens,
                             user_allergens=user_allergens)
    
    # Product detail page with allergen analysis
    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        
        user_allergens = []
        product_allergens = product.get_common_allergens()  # Returns only common allergens
        conflicting_allergens = []
        is_safe = True
        alternatives = []
        
        if current_user.is_authenticated and not current_user.is_admin:
            user_allergens = current_user.get_allergens()
            # Use new method to get user-specific allergens detected in product
            conflicting_allergens = product.get_allergens_for_user(current_user)
            is_safe = len(conflicting_allergens) == 0
            
            # Get alternative products if this product is unsafe
            if not is_safe:
                alternatives = get_alternative_products(product, current_user)
        
        return render_template('product_detail.html', 
                             product=product, 
                             user_allergens=user_allergens,
                             product_allergens=product_allergens,
                             conflicting_allergens=conflicting_allergens,
                             is_safe=is_safe,
                             alternatives=alternatives)
    
    # Dedicated search page
    @app.route('/search')
    def search():
        return render_template('search.html')
    
    # Search results page
    @app.route('/search/results')
    def search_results():
        search_query = request.args.get('q', '')
        
        if not search_query:
            return redirect(url_for('search'))
        
        # Search local Nigerian products only
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.nafdac_number.ilike(f'%{search_query}%'),
                Product.manufacturer.ilike(f'%{search_query}%'),
                Product.ingredients.ilike(f'%{search_query}%')
            )
        ).all()
        
        # Add safety information for authenticated users
        local_products = []
        for product in products:
            product_data = product.to_dict()
            if current_user.is_authenticated and not current_user.is_admin:
                product_data['has_allergen_for_user'] = product.has_allergen_for_user(current_user)
                product_data['safety_status'] = 'warning' if product_data['has_allergen_for_user'] else 'safe'
            local_products.append(product_data)
        
        return render_template('search_results.html', 
                             local_products=local_products,
                             off_products=[],
                             search_query=search_query,
                             total_count=len(products),
                             sources=['Local Nigerian Database'],
                             include_global=False)
    
    # Health news page
    @app.route('/health-news')
    def health_news():
        if current_user.is_authenticated and current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        news = HealthNews.query.filter_by(is_published=True).order_by(HealthNews.published_at.desc()).all()
        return render_template('health_news.html', news=news)
    
    # Product recommendations for users
    @app.route('/recommendations')
    @login_required
    def recommendations():
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
        safe_products = get_safe_products_for_user(current_user)
        return render_template('recommendations.html', products=safe_products)
    
    # Admin Dashboard Routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Get dashboard statistics
        total_users = User.query.filter_by(is_admin=False).count()
        total_products = Product.query.count()
        total_allergens = Allergen.query.count()
        total_health_news = HealthNews.query.count()
        
        # Recent activity
        recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(5).all()
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_products=total_products,
                             total_allergens=total_allergens,
                             total_health_news=total_health_news,
                             recent_users=recent_users,
                             recent_products=recent_products)
    
    # Admin allergen management
    @app.route('/admin/allergens')
    @login_required
    @admin_required
    def admin_allergens():
        allergens = Allergen.query.order_by(Allergen.name).all()
        return render_template('admin/allergens.html', allergens=allergens)
    

    
    @app.route('/admin/allergens/delete/<int:allergen_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_allergen(allergen_id):
        allergen = Allergen.query.get_or_404(allergen_id)
        
        try:
            # Delete related records first
            UserAllergen.query.filter_by(allergen_id=allergen_id).delete()
            ProductAllergen.query.filter_by(allergen_id=allergen_id).delete()
            
            allergen_name = allergen.name
            db.session.delete(allergen)
            db.session.commit()
            
            flash(f'Allergen "{allergen_name}" deleted successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Delete allergen error: {e}")
            flash('Failed to delete allergen. Please try again.', 'error')
        
        return redirect(url_for('admin_allergens'))
    
    # Admin product management
    @app.route('/admin/products')
    @login_required
    @admin_required
    def admin_products():
        page = request.args.get('page', 1, type=int)
        products = Product.query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('admin/products.html', products=products)
    
    @app.route('/admin/products/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_add_product():
        form = ProductForm()
        
        if form.validate_on_submit():
            try:
                product = Product(
                    name=form.name.data.strip(),
                    nafdac_number=form.nafdac_number.data.strip(),
                    manufacturer=form.manufacturer.data.strip(),
                    category=form.category.data.strip(),
                    description=form.description.data.strip() if form.description.data else None,
                    ingredients=form.ingredients.data.strip()
                )
                
                db.session.add(product)
                db.session.commit()
                
                flash(f'Product "{product.name}" added successfully!', 'success')
                return redirect(url_for('admin_products'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Add product error: {e}")
                flash('Failed to add product. Please try again.', 'error')
        
        page = request.args.get('page', 1, type=int)
        products = Product.query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('admin/products.html', products=products, form=form, action='add')
    
    @app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_product(product_id):
        product = Product.query.get_or_404(product_id)
        form = ProductForm(original_nafdac=product.nafdac_number)
        
        if form.validate_on_submit():
            try:
                product.name = form.name.data.strip()
                product.nafdac_number = form.nafdac_number.data.strip()
                product.manufacturer = form.manufacturer.data.strip()
                product.category = form.category.data.strip()
                product.description = form.description.data.strip() if form.description.data else None
                product.ingredients = form.ingredients.data.strip()
                
                db.session.commit()
                
                flash(f'Product "{product.name}" updated successfully!', 'success')
                return redirect(url_for('admin_products'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Edit product error: {e}")
                flash('Failed to update product. Please try again.', 'error')
        
        # Pre-populate form
        if request.method == 'GET':
            form.name.data = product.name
            form.nafdac_number.data = product.nafdac_number
            form.manufacturer.data = product.manufacturer
            form.category.data = product.category
            form.description.data = product.description
            form.ingredients.data = product.ingredients
        
        page = request.args.get('page', 1, type=int)
        products = Product.query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('admin/products.html', products=products, form=form, action='edit', edit_product=product)
    
    @app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        
        try:
            # Delete related records first
            ProductAllergen.query.filter_by(product_id=product_id).delete()
            
            product_name = product.name
            db.session.delete(product)
            db.session.commit()
            
            flash(f'Product "{product_name}" deleted successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Delete product error: {e}")
            flash('Failed to delete product. Please try again.', 'error')
        
        return redirect(url_for('admin_products'))
    
    # Admin health news management
    @app.route('/admin/health-news')
    @login_required
    @admin_required
    def admin_health_news():
        news = HealthNews.query.order_by(HealthNews.created_at.desc()).all()
        return render_template('admin/health_news.html', news=news)
    
    @app.route('/admin/health-news/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_add_health_news():
        form = HealthNewsForm()
        
        if form.validate_on_submit():
            try:
                news = HealthNews(
                    title=form.title.data.strip(),
                    content=form.content.data.strip(),
                    author=form.author.data.strip(),
                    is_published=form.is_published.data
                )
                
                db.session.add(news)
                db.session.commit()
                
                flash(f'Health news "{news.title}" added successfully!', 'success')
                return redirect(url_for('admin_health_news'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Add health news error: {e}")
                flash('Failed to add health news. Please try again.', 'error')
        
        news = HealthNews.query.order_by(HealthNews.created_at.desc()).all()
        return render_template('admin/health_news.html', news=news, form=form, action='add')
    
    @app.route('/admin/health-news/edit/<int:news_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_health_news(news_id):
        news_item = HealthNews.query.get_or_404(news_id)
        form = HealthNewsForm()
        
        if form.validate_on_submit():
            try:
                news_item.title = form.title.data.strip()
                news_item.content = form.content.data.strip()
                news_item.author = form.author.data.strip()
                news_item.is_published = form.is_published.data
                
                db.session.commit()
                
                flash(f'Health news "{news_item.title}" updated successfully!', 'success')
                return redirect(url_for('admin_health_news'))
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Edit health news error: {e}")
                flash('Failed to update health news. Please try again.', 'error')
        
        # Pre-populate form
        if request.method == 'GET':
            form.title.data = news_item.title
            form.content.data = news_item.content
            form.author.data = news_item.author
            form.is_published.data = news_item.is_published
        
        news = HealthNews.query.order_by(HealthNews.created_at.desc()).all()
        return render_template('admin/health_news.html', news=news, form=form, action='edit', edit_news=news_item)
    
    @app.route('/admin/health-news/delete/<int:news_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_health_news(news_id):
        news = HealthNews.query.get_or_404(news_id)
        
        try:
            news_title = news.title
            db.session.delete(news)
            db.session.commit()
            
            flash(f'Health news "{news_title}" deleted successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Delete health news error: {e}")
            flash('Failed to delete health news. Please try again.', 'error')
        
        return redirect(url_for('admin_health_news'))
    
    # Admin user management
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        try:
            page = request.args.get('page', 1, type=int)
            users_pagination = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).paginate(
                page=page, per_page=20, error_out=False
            )
            
            # Convert users to dictionaries for JSON serialization
            users_dict = [user.to_dict() for user in users_pagination.items]
            
            return render_template('admin/users.html', users=users_pagination, users_json=users_dict)
        except Exception as e:
            logging.error(f"Admin users page error: {e}")
            flash('Error loading users page', 'error')
            return redirect(url_for('admin_dashboard'))
    
