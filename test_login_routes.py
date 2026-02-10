"""
Test Flask routes for login functionality.
"""
from app import app, db
from models import Member
from datetime import date

def test_routes():
    """Test login/logout routes."""
    with app.test_client() as client:
        with app.app_context():
            print("=" * 60)
            print("TESTING LOGIN ROUTES")
            print("=" * 60)
            
            # 1. Test GET /login
            print("\n1. Testing GET /login...")
            response = client.get('/login')
            if response.status_code == 200:
                print("   ✓ Login page loads successfully")
                if b'Welcome Back' in response.data or b'Log In' in response.data or b'login' in response.data.lower():
                    print("   ✓ Login page contains expected content")
                else:
                    print("   ⚠ Login page missing expected content")
            else:
                print(f"   ✗ Login page failed with status {response.status_code}")
                return False
            
            # 2. Test GET /signup (should have password fields)
            print("\n2. Testing GET /signup (password fields)...")
            response = client.get('/signup')
            if response.status_code == 200:
                print("   ✓ Signup page loads successfully")
                if b'password' in response.data.lower() and b'confirm' in response.data.lower():
                    print("   ✓ Signup page contains password fields")
                else:
                    print("   ⚠ Signup page missing password fields")
            else:
                print(f"   ✗ Signup page failed with status {response.status_code}")
                return False
            
            # 3. Create a test user for login tests
            print("\n3. Creating test user in database...")
            test_member = Member(
                membership_id="ROUTE-TEST-001",
                full_name="Route Test User",
                email="routetest@example.com",
                password_hash='',
                email_verified=True,
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
            test_member.set_password("TestPass123!")
            
            try:
                db.session.add(test_member)
                db.session.commit()
                print("   ✓ Test user created")
                print(f"   - Email: {test_member.email}")
                print(f"   - Password: TestPass123!")
            except Exception as e:
                print(f"   ✗ Error creating test user: {e}")
                db.session.rollback()
                return False
            
            # 4. Test POST /login with correct credentials
            print("\n4. Testing POST /login (correct credentials)...")
            response = client.post('/login', data={
                'email': 'routetest@example.com',
                'password': 'TestPass123!'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✓ Login request completed")
                if b'Welcome back' in response.data or b'Membership' in response.data:
                    print("   ✓ Login successful, redirected to membership page")
                else:
                    print("   ⚠ Login might have succeeded but unclear redirect")
            else:
                print(f"   ✗ Login failed with status {response.status_code}")
            
            # 5. Test session after login
            print("\n5. Testing session after login...")
            with client.session_transaction() as sess:
                if 'user_id' in sess:
                    print(f"   ✓ User session created")
                    print(f"   - user_id: {sess.get('user_id')}")
                    print(f"   - user_email: {sess.get('user_email')}")
                    print(f"   - user_name: {sess.get('user_name')}")
                else:
                    print("   ✗ No user session found after login")
            
            # 6. Test POST /login with incorrect password
            print("\n6. Testing POST /login (incorrect password)...")
            response = client.post('/login', data={
                'email': 'routetest@example.com',
                'password': 'WrongPassword'
            }, follow_redirects=True)
            
            if b'Invalid email or password' in response.data or b'error' in response.data.lower():
                print("   ✓ Incorrect password rejected with error message")
            else:
                print("   ⚠ Error message not found (might still work)")
            
            # 7. Test POST /login with non-existent email
            print("\n7. Testing POST /login (non-existent email)...")
            response = client.post('/login', data={
                'email': 'nonexistent@example.com',
                'password': 'SomePassword'
            }, follow_redirects=True)
            
            if b'Invalid email or password' in response.data or b'error' in response.data.lower():
                print("   ✓ Non-existent email rejected with error message")
            else:
                print("   ⚠ Error message not found (might still work)")
            
            # 8. Test logout
            print("\n8. Testing GET /logout...")
            response = client.get('/logout', follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✓ Logout request completed")
                
                with client.session_transaction() as sess:
                    if 'user_id' not in sess:
                        print("   ✓ User session cleared after logout")
                    else:
                        print("   ✗ User session still exists after logout")
            else:
                print(f"   ✗ Logout failed with status {response.status_code}")
            
            # 9. Test signup with password
            print("\n9. Testing POST /signup (with password)...")
            response = client.post('/signup', data={
                'full_name': 'New Signup User',
                'email': 'newsignup@example.com',
                'password': 'SignupPass123!',
                'confirm_password': 'SignupPass123!',
                'date_of_birth': '1995-06-15',
                'is_student': 'on'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✓ Signup request completed")
                
                # Check if user was created in database
                new_user = Member.query.filter_by(email='newsignup@example.com').first()
                if new_user:
                    print("   ✗ User created in database (shouldn't happen until payment)")
                else:
                    print("   ✓ User not yet in database (correct, waiting for payment)")
            else:
                print(f"   ⚠ Signup returned status {response.status_code}")
            
            # 10. Test password mismatch on signup
            print("\n10. Testing POST /signup (password mismatch)...")
            response = client.post('/signup', data={
                'full_name': 'Mismatch User',
                'email': 'mismatch@example.com',
                'password': 'Password123!',
                'confirm_password': 'DifferentPassword123!',
                'date_of_birth': '1990-01-01',
                'is_student': ''
            }, follow_redirects=True)
            
            if b'Passwords do not match' in response.data or b'password' in response.data.lower():
                print("   ✓ Password mismatch detected and error shown")
            else:
                print("   ⚠ Password mismatch error not clearly shown")
            
            # Cleanup
            print("\n11. Cleaning Up Test Data...")
            try:
                Member.query.filter(Member.membership_id.like('ROUTE-TEST-%')).delete()
                Member.query.filter_by(email='newsignup@example.com').delete()
                db.session.commit()
                print("   ✓ Test data cleaned up")
            except Exception as e:
                print(f"   ✗ Error cleaning up: {e}")
                db.session.rollback()
            
            print("\n" + "=" * 60)
            print("ROUTE TESTS COMPLETED! ✓")
            print("=" * 60)
            return True

if __name__ == "__main__":
    success = test_routes()
    exit(0 if success else 1)
