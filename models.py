from decimal import Decimal
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Gym(db.Model):
    """Represents a gym location with its basic information."""
    __tablename__ = 'gyms'
    
    gym_key = db.Column(db.String(20), primary_key=True)
    gym_name = db.Column(db.String(50), nullable=False)
    joining_fee = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationships
    membership_options = db.relationship('MembershipOption', backref='gym', lazy=True)
    discounts = db.relationship('Discount', backref='gym', lazy=True)
    members = db.relationship('Member', backref='gym', lazy=True)
    
    def to_dict(self):
        """Convert gym to dictionary format compatible with existing data.py structure."""
        gym_plans = {}
        addons = {}
        
        for option in self.membership_options:
            if option.option_type == 'gym_plan':
                gym_plans[option.option_key] = {
                    'label': option.label,
                    'price': option.price
                }
            elif option.option_type == 'addon':
                addons[option.option_key] = {
                    'label': option.label,
                    'with_gym': option.price_with_full_gym_access,
                    'without_gym': option.price_for_addons_only
                }
        
        return {
            'key': self.gym_key,
            'name': self.gym_name,
            'joining_fee': self.joining_fee,
            'gym_plans': gym_plans,
            'addons': addons
        }


class MembershipOption(db.Model):
    """Represents gym plans (time bands) and add-ons (swim, classes, etc.)."""
    __tablename__ = 'membership_option'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gym_key = db.Column(db.String(20), db.ForeignKey('gyms.gym_key'), nullable=False)
    option_type = db.Column(db.Enum('gym_plan', 'addon', name='option_type_enum'), nullable=False)
    option_key = db.Column(db.String(30), nullable=False)
    label = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Numeric(10, 2))  # For gym plans
    price_with_full_gym_access = db.Column(db.Numeric(10, 2))  # For addons
    price_for_addons_only = db.Column(db.Numeric(10, 2))  # For addons
    discount_allowed = db.Column(db.Boolean, nullable=False, default=True)
    
    __table_args__ = (
        db.UniqueConstraint('gym_key', 'option_type', 'option_key', name='uq_option'),
    )


class Discount(db.Model):
    """Represents discount rates for different user categories at each gym."""
    __tablename__ = 'discounts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    discount_type = db.Column(db.Enum('student_Discount', 'pensioner_Discount', name='discount_type_enum'), nullable=False)
    gym_key = db.Column(db.String(20), db.ForeignKey('gyms.gym_key'), nullable=False)
    rate = db.Column(db.Numeric(5, 2), nullable=False)  # Stored as decimal (e.g., 0.20 for 20%)
    
    __table_args__ = (
        db.UniqueConstraint('discount_type', 'gym_key', name='uq_discount'),
    )


class Member(db.Model):
    """Represents a gym member with their membership details."""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    membership_id = db.Column(db.String(25), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_sent_at = db.Column(db.DateTime, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    is_student = db.Column(db.Boolean, nullable=False, default=False)
    is_young_adult = db.Column(db.Boolean, nullable=False, default=False)
    is_pensioner = db.Column(db.Boolean, nullable=False, default=False)
    
    # Chosen gym and preferences
    chosen_gym = db.Column(db.String(20), db.ForeignKey('gyms.gym_key'), nullable=False)
    wants_gym = db.Column(db.Boolean, nullable=False)
    gym_band = db.Column(db.String(30))  # e.g., 'super_off_peak', 'off_peak', 'anytime'
    
    # Add-ons
    add_swim = db.Column(db.Boolean, nullable=False, default=False)
    add_classes = db.Column(db.Boolean, nullable=False, default=False)
    add_massage = db.Column(db.Boolean, nullable=False, default=False)
    add_physio = db.Column(db.Boolean, nullable=False, default=False)
    
    # Pricing details
    monthly_total = db.Column(db.Numeric(10, 2), nullable=False)
    joining_fee = db.Column(db.Numeric(10, 2), nullable=False)
    first_payment_total = db.Column(db.Numeric(10, 2), nullable=False)

    # False after register-without-plan; True after checkout (real gym + prices set)
    has_active_membership = db.Column(db.Boolean, nullable=False, default=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert member to dictionary format compatible with existing session structure."""
        from data import GYMS

        if not self.has_active_membership:
            return {
                "membership_id": self.membership_id,
                "gym_key": None,
                "has_active_membership": False,
                "signup": {
                    "full_name": self.full_name,
                    "email": self.email,
                    "age": self.age,
                    "is_student": self.is_student,
                    "is_young_adult": self.is_young_adult,
                    "is_pensioner": self.is_pensioner,
                },
                "email_verified": self.email_verified,
                "preferences": {
                    "wants_gym": self.wants_gym,
                    "gym_band": self.gym_band,
                    "add_swim": self.add_swim,
                    "add_classes": self.add_classes,
                    "add_massage": self.add_massage,
                    "add_physio": self.add_physio,
                },
                "pricing": {
                    "gym_name": "No plan selected yet",
                    "gym_plan_label": None,
                    "wants_gym": False,
                    "addons": [],
                    "monthly_total": Decimal("0.00"),
                    "monthly_total_after_discount": Decimal("0.00"),
                    "joining_fee": Decimal("0.00"),
                    "first_payment_total": Decimal("0.00"),
                },
                "created_at": self.created_at,
            }
        
        # Get gym name
        gym_name = GYMS.get(self.chosen_gym, {}).get('name', 'Unknown Gym')
        
        # Get gym plan label if applicable
        gym_plan_label = None
        if self.wants_gym and self.gym_band:
            gym_plans = GYMS.get(self.chosen_gym, {}).get('gym_plans', {})
            gym_plan_label = gym_plans.get(self.gym_band, {}).get('label', self.gym_band)
        
        # Build addons list
        addons = []
        addon_map = GYMS.get(self.chosen_gym, {}).get('addons', {})
        if self.add_swim and 'swim' in addon_map:
            addons.append({
                'label': addon_map['swim']['label'],
                'context': 'Swimming pool access',
                'final_price': self.monthly_total  # Simplified, actual calculation would be more complex
            })
        if self.add_classes and 'classes' in addon_map:
            addons.append({
                'label': addon_map['classes']['label'],
                'context': 'Fitness classes',
                'final_price': self.monthly_total
            })
        if self.add_massage and 'massage' in addon_map:
            addons.append({
                'label': addon_map['massage']['label'],
                'context': 'Massage therapy',
                'final_price': self.monthly_total
            })
        if self.add_physio and 'physio' in addon_map:
            addons.append({
                'label': addon_map['physio']['label'],
                'context': 'Physiotherapy',
                'final_price': self.monthly_total
            })
        
        return {
            'membership_id': self.membership_id,
            'gym_key': self.chosen_gym,
            'has_active_membership': True,
            'signup': {
                'full_name': self.full_name,
                'email': self.email,
                'age': self.age,
                'is_student': self.is_student,
                'is_young_adult': self.is_young_adult,
                'is_pensioner': self.is_pensioner,
            },
            'email_verified': self.email_verified,
            'preferences': {
                'wants_gym': self.wants_gym,
                'gym_band': self.gym_band,
                'add_swim': self.add_swim,
                'add_classes': self.add_classes,
                'add_massage': self.add_massage,
                'add_physio': self.add_physio,
            },
            'pricing': {
                'gym_name': gym_name,
                'gym_plan_label': gym_plan_label,
                'wants_gym': self.wants_gym,
                'addons': addons,
                'monthly_total': self.monthly_total,
                'monthly_total_after_discount': self.monthly_total,  # Same as monthly_total (already discounted)
                'joining_fee': self.joining_fee,
                'first_payment_total': self.first_payment_total,
            },
            'created_at': self.created_at,
        }
