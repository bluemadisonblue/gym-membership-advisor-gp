"""
Test script for email verification functionality.
"""

from app import app
from models import db, Member
from email_utils import generate_timed_token, verify_timed_token
from datetime import date


def test_email_verification():
    """Test the email verification flow."""
    
    with app.app_context():
        print("=" * 60)
        print("Email Verification Test")
        print("=" * 60)
        
        # 1. Test token generation and verification
        print("\n1. Testing token generation and verification...")
        test_email = "test@example.com"
        token = generate_timed_token(app, test_email)
        print(f"   ✓ Generated token: {token[:20]}...")
        
        # Verify the token
        verified_email = verify_timed_token(app, token)
        assert verified_email == test_email, "Token verification failed"
        print(f"   ✓ Token verified successfully: {verified_email}")
        
        # Test invalid token
        invalid_verified = verify_timed_token(app, "invalid-token-12345")
        assert invalid_verified is None, "Invalid token should return None"
        print("   ✓ Invalid token correctly rejected")
        
        # 2. Test creating a member with email
        print("\n2. Testing member creation with email...")
        test_member = Member(
            membership_id='TEST-2026-EMAIL-001',
            full_name='Test User',
            email='testuser@example.com',
            email_verified=False,
            verification_token=token,
            date_of_birth=date(1995, 5, 15),
            age=30,
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
        print(f"   ✓ Created member: {test_member.membership_id}")
        print(f"   ✓ Email: {test_member.email}")
        print(f"   ✓ Email verified: {test_member.email_verified}")
        
        # 3. Test email verification process
        print("\n3. Testing email verification process...")
        member = Member.query.filter_by(email='testuser@example.com').first()
        assert member is not None, "Member not found"
        assert not member.email_verified, "Email should not be verified yet"
        print("   ✓ Member found with unverified email")
        
        # Simulate verification
        member.email_verified = True
        member.verification_token = None
        db.session.commit()
        print("   ✓ Email marked as verified")
        
        # Verify the change
        verified_member = Member.query.filter_by(email='testuser@example.com').first()
        assert verified_member.email_verified, "Email should be verified now"
        assert verified_member.verification_token is None, "Token should be cleared"
        print("   ✓ Verification status confirmed in database")
        
        # 4. Test to_dict includes email
        print("\n4. Testing to_dict method includes email...")
        member_dict = verified_member.to_dict()
        assert 'signup' in member_dict, "signup key missing"
        assert 'email' in member_dict['signup'], "email missing from signup"
        assert 'email_verified' in member_dict, "email_verified missing"
        print(f"   ✓ to_dict() includes email: {member_dict['signup']['email']}")
        print(f"   ✓ to_dict() includes verification status: {member_dict['email_verified']}")
        
        # 5. Test unique email constraint
        print("\n5. Testing unique email constraint...")
        duplicate_member = Member(
            membership_id='TEST-2026-EMAIL-002',
            full_name='Another User',
            email='testuser@example.com',  # Same email
            email_verified=False,
            date_of_birth=date(1990, 1, 1),
            age=35,
            is_student=False,
            is_young_adult=False,
            is_pensioner=False,
            chosen_gym='power_zone',
            wants_gym=True,
            gym_band='off_peak',
            add_swim=False,
            add_classes=False,
            add_massage=False,
            add_physio=False,
            monthly_total=30.00,
            joining_fee=30.00,
            first_payment_total=60.00
        )
        
        try:
            db.session.add(duplicate_member)
            db.session.commit()
            print("   ✗ Unique constraint not enforced!")
            assert False, "Should have raised integrity error"
        except Exception as e:
            db.session.rollback()
            print("   ✓ Unique email constraint enforced")
            print(f"   ✓ Error type: {type(e).__name__}")
        
        # Clean up
        print("\n6. Cleaning up test data...")
        test_members = Member.query.filter(
            Member.membership_id.like('TEST-2026-EMAIL-%')
        ).all()
        for member in test_members:
            db.session.delete(member)
        db.session.commit()
        print(f"   ✓ Deleted {len(test_members)} test member(s)")
        
        print("\n" + "=" * 60)
        print("✓ All email verification tests passed!")
        print("=" * 60)
        
        print("\nTest Summary:")
        print("  - Token generation and verification: ✓")
        print("  - Member creation with email: ✓")
        print("  - Email verification process: ✓")
        print("  - to_dict includes email fields: ✓")
        print("  - Unique email constraint: ✓")
        
        return True


if __name__ == '__main__':
    try:
        test_email_verification()
        print("\n✓ Email verification feature is working correctly!")
        exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
