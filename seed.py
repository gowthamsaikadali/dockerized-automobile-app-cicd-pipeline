import os

from app import create_app, db
from app.models import User, Vehicle

app = create_app(os.environ.get("FLASK_ENV", "default"))


with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@autoforge.com",
            is_admin=True,
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        print("Admin user created -> username: admin / password: Admin@123")

    if Vehicle.query.count() == 0:
        vehicles = [
            Vehicle(
                name="Toyota",
                model="Hilux",
                year=2024,
                category="truck",
                price=42000,
                stock=15,
                description="Rugged pickup truck built for tough terrain.",
            ),
            Vehicle(
                name="Ford",
                model="Mustang",
                year=2024,
                category="sports",
                price=58000,
                stock=8,
                description="Iconic American muscle car.",
            ),
            Vehicle(
                name="Tesla",
                model="Model 3",
                year=2024,
                category="electric",
                price=47000,
                stock=20,
                description="Long-range electric sedan.",
            ),
            Vehicle(
                name="Honda",
                model="CR-V",
                year=2024,
                category="suv",
                price=35000,
                stock=12,
                description="Reliable family SUV.",
            ),
            Vehicle(
                name="Toyota",
                model="Camry",
                year=2024,
                category="sedan",
                price=28000,
                stock=18,
                description="Comfortable everyday sedan.",
            ),
        ]
        db.session.add_all(vehicles)
        print(f"{len(vehicles)} sample vehicles added.")

    db.session.commit()
    print("Seed complete.")
