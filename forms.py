from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SelectMultipleField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Allergen
from app import db

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class RegistrationForm(FlaskForm):
    """User registration form with allergen selection"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    allergens = MultiCheckboxField('Select Allergens You React To', coerce=int)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate allergen choices from database - only common ones for registration
        self.allergens.choices = [(a.id, a.name) for a in Allergen.query.filter_by(is_common=True).order_by(Allergen.name).limit(20).all()]
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email address already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class ProfileForm(FlaskForm):
    """User profile editing form"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    
    def __init__(self, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        if email.data.lower() != self.original_email:
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('Email address already in use. Please choose a different one.')

class AllergenForm(FlaskForm):
    """Form for managing allergens (admin)"""
    name = StringField('Allergen Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    
    def __init__(self, original_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_name = original_name
    
    def validate_name(self, name):
        if name.data.lower() != (self.original_name.lower() if self.original_name else ''):
            allergen = Allergen.query.filter_by(name=name.data).first()
            if allergen:
                raise ValidationError('Allergen name already exists. Please choose a different one.')

class ProductForm(FlaskForm):
    """Form for managing products (admin)"""
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=200)])
    nafdac_number = StringField('NAFDAC Number', validators=[DataRequired(), Length(min=2, max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(min=2, max=200)])
    category = StringField('Category', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    ingredients = TextAreaField('Ingredients (comma-separated)', validators=[DataRequired()])
    
    def __init__(self, original_nafdac=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_nafdac = original_nafdac
    
    def validate_nafdac_number(self, nafdac_number):
        if nafdac_number.data != self.original_nafdac:
            from models import Product
            product = Product.query.filter_by(nafdac_number=nafdac_number.data).first()
            if product:
                raise ValidationError('NAFDAC number already exists. Please use a different number.')

class HealthNewsForm(FlaskForm):
    """Form for managing health news (admin)"""
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=300)])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=50)])
    author = StringField('Author', validators=[DataRequired(), Length(min=2, max=100)])
    is_published = BooleanField('Published')
