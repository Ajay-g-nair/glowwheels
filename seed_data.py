from app import create_app
from database import db
from models import Package, Product, User
from config import Config

def seed():
    app = create_app()
    with app.app_context():
        # 1. Check or create Admin
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=Config.ADMIN_USERNAME,
                full_name="GlowWheels Admin",
                role="admin"
            )
            admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(admin)
            print(f"Created Admin account: {Config.ADMIN_USERNAME}")

        # 2. Reset / Seed Packages matching mockup design
        Package.query.delete()
        packages = [
            Package(
                name="Basic Wash",
                price=299.0,
                duration_mins=30,
                badge="Essential",
                icon="droplet",
                description="Quick exterior spruce up for everyday driving.",
                features="Exterior wash; Foam cleaning; Wheel cleaning; Drying; Tyre dressing"
            ),
            Package(
                name="Premium Wash",
                price=499.0,
                duration_mins=50,
                badge="Most Popular",
                icon="sparkles",
                description="Comprehensive interior and exterior detailing for complete cleanliness.",
                features="Exterior wash; Interior vacuum; Dashboard cleaning; Tyre cleaning; Mat cleaning; Glass cleaning"
            ),
            Package(
                name="Complete Detailing",
                price=999.0,
                duration_mins=90,
                badge="Luxury Care",
                icon="shield-halved",
                description="Showroom gloss restoration with paint wax and deep interior sanitization.",
                features="Everything in Premium; Interior deep cleaning; Stain removal; Polishing and waxing; Headlight cleaning; Long lasting protection"
            )
        ]
        db.session.bulk_save_objects(packages)
        print(f"Seeded {len(packages)} car wash packages matching design mockup.")

        # 3. Seed Inventory Products if none exist
        if Product.query.count() == 0:
            products = [
                Product(name="High Foam Car Shampoo", category="Chemicals", stock_quantity=14, unit="bottles", low_threshold=3),
                Product(name="Tire Shine and Rim Polish", category="Chemicals", stock_quantity=8, unit="bottles", low_threshold=2),
                Product(name="Microfiber Detailing Towels", category="Accessories", stock_quantity=24, unit="pieces", low_threshold=6),
                Product(name="Carnauba Liquid Body Wax", category="Polish", stock_quantity=5, unit="bottles", low_threshold=2),
                Product(name="Interior Dashboard Dressing", category="Chemicals", stock_quantity=6, unit="bottles", low_threshold=2),
                Product(name="Wet and Dry Vacuum Bags", category="Equipment", stock_quantity=10, unit="packs", low_threshold=3),
                Product(name="Ceramic Hydrophobic Sealant", category="Coatings", stock_quantity=4, unit="bottles", low_threshold=2)
            ]
            db.session.bulk_save_objects(products)
            print(f"Seeded {len(products)} inventory products.")

        # 4. Create sample worker account if none exist
        sample_worker = User.query.filter_by(role='worker').first()
        if not sample_worker:
            worker = User(
                username="worker1",
                full_name="Ramesh (Field Specialist)",
                phone="9876500001",
                role="worker"
            )
            worker.set_password("worker123")
            db.session.add(worker)
            print("Created sample worker account: worker1 / worker123")

        # 5. Create sample user account if none exist
        sample_user = User.query.filter_by(role='user').first()
        if not sample_user:
            user = User(
                username="user1",
                full_name="Arjun Sharma",
                phone="9876500002",
                role="user"
            )
            user.set_password("password")
            db.session.add(user)
            print("Created sample user account: user1 / password")

        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
