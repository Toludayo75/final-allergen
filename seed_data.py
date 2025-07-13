
from app import db
from models import Product, Allergen, ProductAllergen
from utils import add_ingredient_as_allergen

def seed_database():
    """Seed the database with initial data if it's empty"""
    
    # Check if database is already seeded
    if Product.query.first() is not None:
        print("INFO:root:Database already seeded, skipping...")
        return
    
    print("Seeding database with initial products...")
    
    # Clean authentic products without duplicates
    authentic_products = [
        {"name": "BUA Brown Sugar", "nafdac_number": "B1-1002", "manufacturer": "BUA Foods Plc", "category": "Sweeteners", "description": "Natural brown sugar with molasses", "ingredients": "Raw sugar, molasses, natural minerals"},
        {"name": "BUA Industrial Sugar", "nafdac_number": "B1-1003", "manufacturer": "BUA Foods Plc", "category": "Sweeteners", "description": "Industrial grade sugar for food manufacturing", "ingredients": "Refined sugar"},
        {"name": "BUA Palm Olein Oil", "nafdac_number": "B5-5001", "manufacturer": "BUA Foods Plc", "category": "Oils", "description": "Premium palm olein cooking oil", "ingredients": "Refined palm olein, vitamin A, vitamin E"},
        {"name": "BUA Premium Sugar", "nafdac_number": "B1-1001", "manufacturer": "BUA Foods Plc", "category": "Sweeteners", "description": "Premium refined sugar, vitamin A fortified", "ingredients": "Refined sugar, vitamin A"},
        {"name": "Dangote Flour", "nafdac_number": "F1-6789", "manufacturer": "Dangote Group", "category": "Flour", "description": "Premium wheat flour", "ingredients": "Wheat flour, vitamins, minerals"},
        {"name": "Peak Milk Powder", "nafdac_number": "A1-2345", "manufacturer": "FrieslandCampina WAMCO", "category": "Dairy", "description": "Full cream milk powder", "ingredients": "Whole milk powder, vitamins A, D"},
        {"name": "Milo", "nafdac_number": "A2-1000", "manufacturer": "Nestle Nigeria", "category": "Beverages", "description": "Chocolate malt drink", "ingredients": "Malt extract, cocoa, milk solids, sugar, vitamins"},
        {"name": "Golden Penny Spaghetti", "nafdac_number": "D1-4567", "manufacturer": "Flour Mills of Nigeria", "category": "Pasta", "description": "Premium wheat spaghetti", "ingredients": "Durum wheat semolina"},
        {"name": "Bournvita", "nafdac_number": "A1-0890", "manufacturer": "Mondelez Nigeria", "category": "Beverages", "description": "Chocolate health drink", "ingredients": "Cocoa, malt extract, milk solids, sugar, vitamins"},
        {"name": "Honeywell Flour", "nafdac_number": "H1-4000", "manufacturer": "Honeywell Group", "category": "Flour", "description": "Enriched wheat flour", "ingredients": "Wheat flour, iron, folic acid, vitamins"},
    ]
    
    # Add products to database
    for product_data in authentic_products:
        try:
            product = Product(
                name=product_data['name'],
                nafdac_number=product_data['nafdac_number'],
                manufacturer=product_data['manufacturer'],
                category=product_data['category'],
                description=product_data['description'],
                ingredients=product_data['ingredients']
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Add ingredients as allergens
            if product_data.get('ingredients'):
                add_ingredient_as_allergen(product, product_data['ingredients'])
            
        except Exception as e:
            print(f"Error adding product {product_data['name']}: {e}")
            db.session.rollback()
            continue
    
    try:
        db.session.commit()
        print(f"Successfully seeded database with {len(authentic_products)} products")
    except Exception as e:
        print(f"Error committing to database: {e}")
        db.session.rollback()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        seed_database()
