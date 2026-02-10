"""
Simple test script to verify database integration is working correctly.
"""

from app import app
from models import db, Gym, Member, MembershipOption, Discount
import data
from pricing import calculate_pricing_for_selection
from datetime import date


def test_database_connection():
    """Test basic database connectivity."""
    with app.app_context():
        print("Testing database connection...")
        gyms_count = Gym.query.count()
        print(f"✓ Found {gyms_count} gyms in database")
        
        options_count = MembershipOption.query.count()
        print(f"✓ Found {options_count} membership options")
        
        discounts_count = Discount.query.count()
        print(f"✓ Found {discounts_count} discount configurations")
        
        return True


def test_gym_data_loading():
    """Test loading gym data from database."""
    with app.app_context():
        print("\nTesting gym data loading...")
        gyms = data.load_gyms_from_db()
        
        assert 'ugym' in gyms, "uGym not found"
        assert 'power_zone' in gyms, "Power Zone not found"
        print(f"✓ Loaded {len(gyms)} gyms")
        
        # Verify uGym structure
        ugym = gyms['ugym']
        assert ugym['name'] == 'uGym', "uGym name incorrect"
        assert 'gym_plans' in ugym, "Gym plans missing"
        assert 'addons' in ugym, "Addons missing"
        print(f"✓ uGym data structure is correct")
        
        # Verify gym plans
        assert 'anytime' in ugym['gym_plans'], "Anytime plan missing"
        print(f"✓ Gym plans loaded correctly")
        
        return True


def test_discount_loading():
    """Test loading discount data from database."""
    with app.app_context():
        print("\nTesting discount loading...")
        discounts = data.load_discounts_from_db()
        
        assert 'student_young' in discounts, "Student/young discount missing"
        assert 'pensioner' in discounts, "Pensioner discount missing"
        print(f"✓ Loaded discount categories")
        
        # Verify discount values
        from decimal import Decimal
        student_ugym = discounts['student_young']['ugym']
        assert student_ugym == Decimal('0.20'), f"Student discount for uGym incorrect: {student_ugym}"
        print(f"✓ Discount values are correct")
        
        return True


def test_pricing_calculation():
    """Test pricing calculation with database data."""
    with app.app_context():
        print("\nTesting pricing calculation...")
        
        # Load data first
        data.load_gyms_from_db()
        data.load_discounts_from_db()
        
        # Sample signup and preferences
        signup = {
            'full_name': 'Test User',
            'age': 20,
            'is_student': True,
            'is_young_adult': True,
            'is_pensioner': False,
        }
        
        preferences = {
            'wants_gym': True,
            'gym_band': 'anytime',
            'add_swim': True,
            'add_classes': False,
            'add_massage': False,
            'add_physio': False,
        }
        
        result = calculate_pricing_for_selection(signup, preferences)
        
        assert 'gyms' in result, "Gyms missing from result"
        assert 'recommended_gym' in result, "Recommended gym missing"
        print(f"✓ Pricing calculation successful")
        print(f"  Recommended gym: {result['recommended_gym']}")
        
        # Verify pricing structure
        ugym_pricing = result['gyms']['ugym']
        assert 'monthly_total_after_discount' in ugym_pricing, "Monthly total missing"
        print(f"  uGym monthly total: £{ugym_pricing['monthly_total_after_discount']}")
        
        return True


def test_member_creation():
    """Test creating a member in the database."""
    with app.app_context():
        print("\nTesting member creation...")
        
        # Create a test member
        test_member = Member(
            membership_id='TEST-2026-000001',
            full_name='Test User',
            date_of_birth=date(2000, 1, 1),
            age=26,
            is_student=False,
            is_young_adult=False,
            is_pensioner=False,
            chosen_gym='ugym',
            wants_gym=True,
            gym_band='anytime',
            add_swim=True,
            add_classes=False,
            add_massage=False,
            add_physio=False,
            monthly_total=45.00,
            joining_fee=10.00,
            first_payment_total=55.00
        )
        
        db.session.add(test_member)
        db.session.commit()
        print(f"✓ Created test member: {test_member.membership_id}")
        
        # Verify member was saved
        retrieved = Member.query.filter_by(membership_id='TEST-2026-000001').first()
        assert retrieved is not None, "Member not found after creation"
        assert retrieved.full_name == 'Test User', "Member name incorrect"
        print(f"✓ Successfully retrieved member from database")
        
        # Test to_dict method
        member_dict = retrieved.to_dict()
        assert 'membership_id' in member_dict, "membership_id missing from dict"
        assert 'signup' in member_dict, "signup missing from dict"
        assert 'preferences' in member_dict, "preferences missing from dict"
        print(f"✓ Member to_dict() working correctly")
        
        # Clean up test member
        db.session.delete(retrieved)
        db.session.commit()
        print(f"✓ Cleaned up test member")
        
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Integration Test Suite")
    print("=" * 60)
    
    try:
        test_database_connection()
        test_gym_data_loading()
        test_discount_loading()
        test_pricing_calculation()
        test_member_creation()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        print("\nDatabase integration is working correctly.")
        print("You can now run the application with: python app.py")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
