"""
Test script to verify login functionality works correctly with the database.
"""
from app import app, db
from models import Member
from datetime import date

def test_database_operations():
    """Test all database operations for login functionality."""
    with app.app_context():
        print("=" * 60)
        print("TESTING LOGIN FUNCTIONALITY")
        print("=" * 60)
        
        # 1. Test creating a member with password
        print("\n1. Testing Member Creation with Password...")
        test_member = Member(
            membership_id="TEST-2026-000001",
            full_name="Test User",
            email="test@example.com",
            password_hash='',  # Will be set with set_password
            email_verified=False,
            date_of_birth=date(1990, 1, 1),
            age=36,
            is_student=False,
            is_young_adult=False,
            is_pensioner=False,
            chosen_gym="ugym",
            wants_gym=True,
            gym_band="anytime",
            add_swim=False,
            add_classes=False,
            add_massage=False,
            add_physio=False,
            monthly_total=50.00,
            joining_fee=25.00,
            first_payment_total=75.00
        )
        
        # Set password using helper method
        test_member.set_password("TestPassword123!")
        
        try:
            db.session.add(test_member)
            db.session.commit()
            print("   ✓ Member created successfully")
            print(f"   - Email: {test_member.email}")
            print(f"   - Membership ID: {test_member.membership_id}")
            print(f"   - Password hash length: {len(test_member.password_hash)}")
        except Exception as e:
            print(f"   ✗ Error creating member: {e}")
            db.session.rollback()
            return False
        
        # 2. Test retrieving member by email
        print("\n2. Testing Member Retrieval by Email...")
        retrieved_member = Member.query.filter_by(email="test@example.com").first()
        if retrieved_member:
            print("   ✓ Member retrieved successfully")
            print(f"   - Name: {retrieved_member.full_name}")
            print(f"   - Email: {retrieved_member.email}")
        else:
            print("   ✗ Failed to retrieve member")
            return False
        
        # 3. Test password verification (correct password)
        print("\n3. Testing Password Verification (Correct Password)...")
        if retrieved_member.check_password("TestPassword123!"):
            print("   ✓ Correct password verified successfully")
        else:
            print("   ✗ Password verification failed (should have passed)")
            return False
        
        # 4. Test password verification (incorrect password)
        print("\n4. Testing Password Verification (Incorrect Password)...")
        if not retrieved_member.check_password("WrongPassword"):
            print("   ✓ Incorrect password rejected successfully")
        else:
            print("   ✗ Incorrect password was accepted (security issue!)")
            return False
        
        # 5. Test email uniqueness constraint
        print("\n5. Testing Email Uniqueness Constraint...")
        duplicate_member = Member(
            membership_id="TEST-2026-000002",
            full_name="Duplicate User",
            email="test@example.com",  # Same email
            password_hash='',
            email_verified=False,
            date_of_birth=date(1995, 1, 1),
            age=31,
            is_student=False,
            is_young_adult=True,
            is_pensioner=False,
            chosen_gym="powerzone",
            wants_gym=True,
            gym_band="off_peak",
            add_swim=False,
            add_classes=False,
            add_massage=False,
            add_physio=False,
            monthly_total=40.00,
            joining_fee=25.00,
            first_payment_total=65.00
        )
        duplicate_member.set_password("AnotherPassword123!")
        
        try:
            db.session.add(duplicate_member)
            db.session.commit()
            print("   ✗ Duplicate email was allowed (should have failed)")
            return False
        except Exception as e:
            db.session.rollback()
            print("   ✓ Duplicate email rejected successfully")
            print(f"   - Error type: {type(e).__name__}")
        
        # 6. Test creating second member with different email
        print("\n6. Testing Multiple Members with Different Emails...")
        second_member = Member(
            membership_id="TEST-2026-000003",
            full_name="Second User",
            email="second@example.com",  # Different email
            password_hash='',
            email_verified=True,
            date_of_birth=date(2000, 5, 15),
            age=25,
            is_student=True,
            is_young_adult=True,
            is_pensioner=False,
            chosen_gym="powerzone",
            wants_gym=True,
            gym_band="super_off_peak",
            add_swim=True,
            add_classes=False,
            add_massage=False,
            add_physio=False,
            monthly_total=35.00,
            joining_fee=20.00,
            first_payment_total=55.00
        )
        second_member.set_password("SecondPassword456!")
        
        try:
            db.session.add(second_member)
            db.session.commit()
            print("   ✓ Second member created successfully")
            print(f"   - Email: {second_member.email}")
        except Exception as e:
            print(f"   ✗ Error creating second member: {e}")
            db.session.rollback()
            return False
        
        # 7. Test querying all members
        print("\n7. Testing Member Query...")
        all_members = Member.query.all()
        print(f"   ✓ Found {len(all_members)} members in database")
        for member in all_members:
            print(f"   - {member.email}: {member.full_name}")
        
        # 8. Test password methods exist and work
        print("\n8. Testing Password Helper Methods...")
        test_password = "NewPassword789!"
        test_member_for_methods = Member.query.filter_by(email="test@example.com").first()
        
        # Change password
        old_hash = test_member_for_methods.password_hash
        test_member_for_methods.set_password(test_password)
        new_hash = test_member_for_methods.password_hash
        
        if old_hash != new_hash:
            print("   ✓ set_password() changes the hash")
        else:
            print("   ✗ set_password() did not change the hash")
            return False
        
        if test_member_for_methods.check_password(test_password):
            print("   ✓ check_password() works with new password")
        else:
            print("   ✗ check_password() failed with new password")
            return False
        
        db.session.commit()
        
        # Cleanup - remove test members
        print("\n9. Cleaning Up Test Data...")
        try:
            Member.query.filter(Member.membership_id.like('TEST-%')).delete()
            db.session.commit()
            print("   ✓ Test members cleaned up successfully")
        except Exception as e:
            print(f"   ✗ Error cleaning up: {e}")
            db.session.rollback()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nDatabase is ready for login functionality!")
        return True

if __name__ == "__main__":
    success = test_database_operations()
    exit(0 if success else 1)
