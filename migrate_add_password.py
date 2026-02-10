"""
Migration script to add password_hash column to members table.
Run this script once to update existing databases.
"""
from app import app, db
from models import Member
from werkzeug.security import generate_password_hash

def migrate():
    """Add password_hash column to members table."""
    with app.app_context():
        # Check if column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('members')]
        
        if 'password_hash' in columns:
            print("✓ password_hash column already exists")
            return
        
        print("Adding password_hash column to members table...")
        
        # Add the column with ALTER TABLE
        with db.engine.connect() as conn:
            # For SQLite
            if 'sqlite' in str(db.engine.url):
                # SQLite doesn't support ALTER TABLE ADD COLUMN with NOT NULL directly
                # So we add it as nullable first, then update all rows, then make it NOT NULL
                conn.execute(db.text("ALTER TABLE members ADD COLUMN password_hash VARCHAR(255)"))
                conn.commit()
                
                # Set a default password for existing users (they'll need to reset it)
                default_password_hash = generate_password_hash('ChangeMe123!')
                conn.execute(
                    db.text("UPDATE members SET password_hash = :hash WHERE password_hash IS NULL"),
                    {"hash": default_password_hash}
                )
                conn.commit()
                
                print("✓ Column added successfully")
                print("⚠️  WARNING: Existing users have been assigned a temporary password: 'ChangeMe123!'")
                print("   They should change their password after logging in.")
            else:
                # For MySQL/PostgreSQL
                conn.execute(db.text("ALTER TABLE members ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''"))
                conn.commit()
                
                # Set a default password for existing users
                default_password_hash = generate_password_hash('ChangeMe123!')
                conn.execute(
                    db.text("UPDATE members SET password_hash = :hash WHERE password_hash = ''"),
                    {"hash": default_password_hash}
                )
                conn.commit()
                
                print("✓ Column added successfully")
                print("⚠️  WARNING: Existing users have been assigned a temporary password: 'ChangeMe123!'")
                print("   They should change their password after logging in.")

if __name__ == "__main__":
    migrate()
