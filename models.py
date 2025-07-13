from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with user allergens
    user_allergens = db.relationship('UserAllergen', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_allergens(self):
        """Get list of allergen names this user is allergic to"""
        return [ua.allergen.name for ua in self.user_allergens.all()]
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'allergens': self.get_allergens()
        }

class Allergen(db.Model):
    """Allergen model for storing user-reported allergens and common ones"""
    __tablename__ = 'allergens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    is_common = db.Column(db.Boolean, default=False, nullable=False)  # For registration display
    user_reported_count = db.Column(db.Integer, default=0, nullable=False)  # Track usage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Allergen {self.name}>'
    
    def to_dict(self):
        """Convert allergen to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    """Product model for storing Nigerian products"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    nafdac_number = db.Column(db.String(50), unique=True, nullable=False)
    manufacturer = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)  # Comma-separated list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with product allergens
    product_allergens = db.relationship('ProductAllergen', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def get_allergens_for_user(self, user):
        """Get list of allergens in this product that affect a specific user"""
        if not user.is_authenticated:
            return []
        
        # Get user's selected allergens
        user_allergens = user.get_allergens()
        if not user_allergens:
            return []
        
        # Get product ingredients
        ingredients = self.get_ingredients_list()
        
        # Check which user allergens are present in product ingredients
        detected_allergens = []
        for user_allergen in user_allergens:
            for ingredient in ingredients:
                # Case-insensitive partial matching
                if user_allergen.lower() in ingredient.lower() or ingredient.lower() in user_allergen.lower():
                    if user_allergen not in detected_allergens:
                        detected_allergens.append(user_allergen)
                    break
        
        return detected_allergens
    
    def get_allergens(self):
        """Get list of potential allergen names in this product - returns ingredients for display"""
        # For general display, just return the ingredients list as potential allergens
        return self.get_ingredients_list()
    
    def get_common_allergens(self):
        """Get list of common allergens detected in this product's ingredients"""
        # Common allergen keywords to check against
        common_allergens = {
            'milk': ['milk', 'dairy', 'cream', 'butter', 'cheese', 'yogurt', 'whey', 'casein', 'lactose'],
            'wheat': ['wheat', 'flour', 'gluten', 'bread', 'pasta', 'semolina', 'durum'],
            'eggs': ['egg', 'albumin', 'lecithin'],
            'soy': ['soy', 'soya', 'soybean', 'tofu'],
            'peanuts': ['peanut', 'groundnut', 'arachis'],
            'tree nuts': ['almond', 'cashew', 'walnut', 'pecan', 'hazelnut', 'pistachio', 'macadamia', 'brazil nut'],
            'fish': ['fish', 'tuna', 'salmon', 'cod', 'sardine', 'anchovy'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'mussel', 'clam'],
            'sesame': ['sesame', 'tahini']
        }
        
        detected_allergens = []
        ingredients = self.get_ingredients_list()
        
        for allergen_name, keywords in common_allergens.items():
            for ingredient in ingredients:
                ingredient_lower = ingredient.lower()
                for keyword in keywords:
                    if keyword in ingredient_lower:
                        if allergen_name not in detected_allergens:
                            detected_allergens.append(allergen_name)
                        break
                if allergen_name in detected_allergens:
                    break
        
        return detected_allergens
    
    def get_ingredients_list(self):
        """Get ingredients as a list"""
        return [ingredient.strip() for ingredient in self.ingredients.split(',') if ingredient.strip()]
    
    def has_allergen_for_user(self, user):
        """Check if product contains any allergens for specific user"""
        detected_allergens = self.get_allergens_for_user(user)
        return len(detected_allergens) > 0
    
    def to_dict(self):
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'nafdac_number': self.nafdac_number,
            'manufacturer': self.manufacturer,
            'category': self.category,
            'description': self.description,
            'ingredients': self.ingredients,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'allergens': self.get_allergens(),
            'ingredients_list': self.get_ingredients_list()
        }

class UserAllergen(db.Model):
    """Junction table for user-allergen many-to-many relationship"""
    __tablename__ = 'user_allergens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergens.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    allergen = db.relationship('Allergen', backref='user_allergen_associations')
    
    # Unique constraint to prevent duplicate user-allergen pairs
    __table_args__ = (db.UniqueConstraint('user_id', 'allergen_id'),)

class ProductAllergen(db.Model):
    """Junction table for product-allergen many-to-many relationship"""
    __tablename__ = 'product_allergens'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergens.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    allergen = db.relationship('Allergen', backref='product_allergen_associations')
    
    # Unique constraint to prevent duplicate product-allergen pairs
    __table_args__ = (db.UniqueConstraint('product_id', 'allergen_id'),)

# Relationships are defined in the models themselves

class HealthNews(db.Model):
    """Health news model for storing health-related articles"""
    __tablename__ = 'health_news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<HealthNews {self.title}>'
    
    def to_dict(self):
        """Convert health news to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_published': self.is_published
        }
