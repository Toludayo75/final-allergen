from functools import wraps
from flask import abort
from flask_login import current_user
from models import Product, UserAllergen, ProductAllergen, Allergen
from app import db
import re

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_safe_products_for_user(user):
    """Get products that are safe for the user (don't contain user's allergens)"""
    if not user.is_authenticated:
        return []
    
    user_allergens = user.get_allergens()
    
    if not user_allergens:
        # User has no allergens, all products are safe
        return Product.query.order_by(Product.created_at.desc()).limit(20).all()
    
    # Get all products and check each one for safety
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    safe_products = []
    
    for product in all_products:
        # Use new method to check if product has allergens for this user
        if not product.has_allergen_for_user(user):  # No allergens detected = safe
            safe_products.append(product)
            
        # Limit to 20 products for performance
        if len(safe_products) >= 20:
            break
    
    return safe_products

def get_alternative_products(product, user):
    """Get alternative products that are safe for user - first try same category, then other categories"""
    if not user.is_authenticated:
        return []
    
    user_allergens = user.get_allergens()
    
    if not user_allergens:
        # User has no allergens, get products in same category
        return Product.query.filter(
            Product.category == product.category,
            Product.id != product.id
        ).limit(5).all()
    
    safe_alternatives = []
    
    # First, try same category
    same_category_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).all()
    
    for candidate in same_category_products:
        # Use new method to check if product has allergens for this user
        if not candidate.has_allergen_for_user(user):  # No allergens detected = safe
            safe_alternatives.append(candidate)
            
        if len(safe_alternatives) >= 5:
            break
    
    # If no safe alternatives in same category, try other categories (limit to improve performance)
    if len(safe_alternatives) == 0:
        # Get a sample of products from different categories
        other_products = Product.query.filter(
            Product.id != product.id,
            Product.category != product.category
        ).limit(100).all()  # Limit for performance
        
        for candidate in other_products:
            # Use new method to check if product has allergens for this user
            if not candidate.has_allergen_for_user(user):  # No allergens detected = safe
                safe_alternatives.append(candidate)
                
            # Limit to 3 cross-category alternatives
            if len(safe_alternatives) >= 3:
                break
    
    return safe_alternatives

def highlight_allergens_in_ingredients(ingredients_text, user_allergens):
    """Highlight allergens in ingredients text for display"""
    if not user_allergens:
        return ingredients_text
    
    highlighted_text = ingredients_text
    
    for allergen in user_allergens:
        # Case-insensitive replacement with highlighting
        highlighted_text = highlighted_text.replace(
            allergen, 
            f'<mark class="allergen-highlight">{allergen}</mark>'
        )
        highlighted_text = highlighted_text.replace(
            allergen.lower(), 
            f'<mark class="allergen-highlight">{allergen.lower()}</mark>'
        )
        highlighted_text = highlighted_text.replace(
            allergen.upper(), 
            f'<mark class="allergen-highlight">{allergen.upper()}</mark>'
        )
    
    return highlighted_text

def add_ingredient_as_allergen(ingredient_name):
    """Add an ingredient as a user-reported allergen if it doesn't exist"""
    # Clean the ingredient name
    clean_name = ingredient_name.strip().lower()
    
    # Check if allergen already exists (case-insensitive)
    existing_allergen = Allergen.query.filter(
        db.func.lower(Allergen.name) == clean_name
    ).first()
    
    if existing_allergen:
        # Increment usage count
        existing_allergen.user_reported_count += 1
        db.session.commit()
        return existing_allergen
    else:
        # Create new allergen
        new_allergen = Allergen(
            name=clean_name.title(),  # Proper case
            description=f"User-reported allergen: {clean_name}",
            is_common=False,
            user_reported_count=1
        )
        db.session.add(new_allergen)
        db.session.commit()
        return new_allergen

def get_all_product_ingredients():
    """Extract all unique ingredients from products for allergen selection"""
    # Use a more efficient query to get only ingredients column
    ingredients_data = db.session.query(Product.ingredients).filter(Product.ingredients.isnot(None)).all()
    all_ingredients = set()
    
    for (ingredients,) in ingredients_data:
        if ingredients:
            # Split by comma and clean up
            ingredients_list = [ing.strip().title() for ing in ingredients.split(',') if ing.strip()]
            all_ingredients.update(ingredients_list)
    
    return sorted(list(all_ingredients))
