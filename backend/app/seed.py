"""
Seed script to populate initial data
Run with: python -m app.seed
"""
import sys
import os
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.service import Service, PricingMode
from app.models.computer import Computer
from app.models.inventory import InventoryItem
from app.core.security import get_password_hash


def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    
    try:
        print("Starting database seeding...")
        
        # Create admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@cybercafe.com",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                password_hash=get_password_hash("admin123"),
                is_active=True
            )
            db.add(admin)
            print("Created admin user (username: admin, password: admin123)")
        
        # Create sample manager
        manager = db.query(User).filter(User.username == "manager").first()
        if not manager:
            manager = User(
                username="manager",
                email="manager@cybercafe.com",
                full_name="Cafe Manager",
                role=UserRole.MANAGER,
                password_hash=get_password_hash("manager123"),
                is_active=True
            )
            db.add(manager)
            print("Created manager user (username: manager, password: manager123)")
        
        # Create sample attendant
        attendant = db.query(User).filter(User.username == "attendant").first()
        if not attendant:
            attendant = User(
                username="attendant",
                email="attendant@cybercafe.com",
                full_name="Front Desk Attendant",
                role=UserRole.ATTENDANT,
                password_hash=get_password_hash("attendant123"),
                is_active=True
            )
            db.add(attendant)
            print("Created attendant user (username: attendant, password: attendant123)")
        
        db.commit()
        
        # Create inventory items
        inventory_items = []
        
        a4_paper = db.query(InventoryItem).filter(InventoryItem.name == "A4 Paper").first()
        if not a4_paper:
            a4_paper = InventoryItem(
                name="A4 Paper",
                unit="reams",
                current_stock=Decimal("50"),
                min_stock_level=Decimal("10"),
                unit_cost=Decimal("400")
            )
            db.add(a4_paper)
            inventory_items.append(a4_paper)
        
        toner = db.query(InventoryItem).filter(InventoryItem.name == "Printer Toner").first()
        if not toner:
            toner = InventoryItem(
                name="Printer Toner",
                unit="cartridges",
                current_stock=Decimal("5"),
                min_stock_level=Decimal("2"),
                unit_cost=Decimal("3500")
            )
            db.add(toner)
            inventory_items.append(toner)
        
        lamination = db.query(InventoryItem).filter(InventoryItem.name == "Lamination Pouches").first()
        if not lamination:
            lamination = InventoryItem(
                name="Lamination Pouches",
                unit="pieces",
                current_stock=Decimal("100"),
                min_stock_level=Decimal("20"),
                unit_cost=Decimal("15")
            )
            db.add(lamination)
            inventory_items.append(lamination)
        
        if inventory_items:
            db.commit()
            print(f"Created {len(inventory_items)} inventory items")
        
        # Refresh to get IDs
        if a4_paper:
            db.refresh(a4_paper)
        
        # Create services
        services_data = [
            {
                "name": "Printing (Black & White)",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("5"),
                "description": "Black and white printing service",
                "requires_stock": True,
                "stock_item_id": a4_paper.id if a4_paper else None
            },
            {
                "name": "Printing (Color)",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("20"),
                "description": "Color printing service",
                "requires_stock": True,
                "stock_item_id": a4_paper.id if a4_paper else None
            },
            {
                "name": "Photocopy",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("3"),
                "description": "Photocopying service",
                "requires_stock": True,
                "stock_item_id": a4_paper.id if a4_paper else None
            },
            {
                "name": "Scanning",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("10"),
                "description": "Document scanning service",
                "requires_stock": False
            },
            {
                "name": "Lamination (A4)",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("50"),
                "description": "A4 size lamination",
                "requires_stock": True,
                "stock_item_id": lamination.id if lamination else None
            },
            {
                "name": "Typing Services",
                "pricing_mode": PricingMode.PER_PAGE,
                "base_price": Decimal("50"),
                "description": "Document typing service",
                "requires_stock": False
            },
            {
                "name": "Browsing",
                "pricing_mode": PricingMode.PER_MINUTE,
                "base_price": Decimal("1"),
                "description": "Internet browsing per minute",
                "requires_stock": False
            },
            {
                "name": "CV Package",
                "pricing_mode": PricingMode.BUNDLE,
                "base_price": Decimal("300"),
                "description": "Complete CV typing and printing package",
                "requires_stock": False
            },
            {
                "name": "KRA PIN Application",
                "pricing_mode": PricingMode.PER_JOB,
                "base_price": Decimal("100"),
                "description": "KRA PIN application assistance",
                "requires_stock": False
            },
            {
                "name": "HELB Application",
                "pricing_mode": PricingMode.PER_JOB,
                "base_price": Decimal("150"),
                "description": "HELB application assistance",
                "requires_stock": False
            }
        ]
        
        services_created = 0
        for service_data in services_data:
            existing = db.query(Service).filter(Service.name == service_data["name"]).first()
            if not existing:
                service = Service(**service_data)
                db.add(service)
                services_created += 1
        
        if services_created > 0:
            db.commit()
            print(f"Created {services_created} services")
        
        # Create computers
        computers_created = 0
        for i in range(1, 6):
            pc_name = f"PC{i}"
            existing = db.query(Computer).filter(Computer.name == pc_name).first()
            if not existing:
                computer = Computer(name=pc_name)
                db.add(computer)
                computers_created += 1
        
        if computers_created > 0:
            db.commit()
            print(f"Created {computers_created} computers")
        
        print("\nDatabase seeding completed successfully!")
        print("\nLogin credentials:")
        print("   Admin    - username: admin,     password: admin123")
        print("   Manager  - username: manager,   password: manager123")
        print("   Attendant- username: attendant, password: attendant123")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
