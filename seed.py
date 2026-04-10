"""
seed.py - Runs on container startup to set up the database.
Creates all tables and inserts sample data for locally onboarded vendors
(these are vendors that exist in SNM but NOT in AgNet).
Only seeds if the database is empty to prevent duplicates on restart.
"""

import uuid
from datetime import datetime, UTC
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

import app as app_module
from app import Vendor, Category, Product, Shipment, ShipmentLot

engine = create_engine(
    "sqlite:///supplynetwork.db",
    connect_args={"check_same_thread": False}
)

# This creates all the database tables
app_module.app.build_app()
print("Tables created.")

with Session(engine) as session:

    # Check if we already have vendors — if so, skip seeding
    existing = session.execute(select(func.count()).select_from(Vendor)).scalar()
    if existing > 0:
        print(f"Database already has {existing} vendors, skipping seed.")
        exit(0)

    # --- Vendors ---
    # Locally onboarded vendors, not in AgNet.
    # Matching AgNet's NAME-HARVEST-TYPE format so Inventory can't tell the difference.
    vendors = [
        Vendor(
            vendor_id="MAPLEWOOD-HARVEST-FARM",
            name="Maplewood Harvest Farm",
            type="Farm",
            reg_state="Active",
            order_count=0,
            last_order=datetime.now(UTC)
        ),
        Vendor(
            vendor_id="CLEARWATER-HARVEST-DAIRY",
            name="Clearwater Harvest Dairy",
            type="Dairy",
            reg_state="Active",
            order_count=0,
            last_order=datetime.now(UTC)
        ),
        Vendor(
            vendor_id="IRONWOOD-HARVEST-BUTCHERY",
            name="Ironwood Harvest Butchery",
            type="Butcher",
            reg_state="New",
            order_count=0,
            last_order=datetime.now(UTC)
        ),
    ]
    session.add_all(vendors)
    session.flush()

    # --- Categories ---
    # 3-level hierarchy matching CIS spec.
    # Top-level categories use empty string for parent_category_id (not null).
    categories = [
        Category(category_id="CAT-PRODUCE", parent_category_id="",
                 category_name="Produce", level=1),
        Category(category_id="CAT-DAIRY", parent_category_id="",
                 category_name="Dairy", level=1),
        Category(category_id="CAT-MEAT", parent_category_id="",
                 category_name="Meat", level=1),
        Category(category_id="CAT-VEGETABLES", parent_category_id="CAT-PRODUCE",
                 category_name="Vegetables", level=2),
        Category(category_id="CAT-LEAFYGREENS", parent_category_id="CAT-PRODUCE",
                 category_name="LeafyGreens", level=2),
        Category(category_id="CAT-MILK", parent_category_id="CAT-DAIRY",
                 category_name="Milk", level=2),
        Category(category_id="CAT-BEEF", parent_category_id="CAT-MEAT",
                 category_name="Beef", level=2),
        Category(category_id="CAT-KALE", parent_category_id="CAT-LEAFYGREENS",
                 category_name="Kale", level=3),
        Category(category_id="CAT-SQUASH", parent_category_id="CAT-VEGETABLES",
                 category_name="Squash", level=3),
        Category(category_id="CAT-WHOLEMILK", parent_category_id="CAT-MILK",
                 category_name="WholeMilk", level=3),
        Category(category_id="CAT-GROUNDBEEF", parent_category_id="CAT-BEEF",
                 category_name="GroundBeef", level=3),
    ]
    session.add_all(categories)
    session.flush()

    # --- Products ---
    # Matching AgNet's PROD-XXXX format.
    # Each product belongs to a level-3 category and a local vendor.
    products = [
        Product(
            product_id="PROD-KALE",
            vendor_id="MAPLEWOOD-HARVEST-FARM",
            category_id="CAT-KALE",
            product_name="Kale",
            unit="kg"
        ),
        Product(
            product_id="PROD-SQUASH",
            vendor_id="MAPLEWOOD-HARVEST-FARM",
            category_id="CAT-SQUASH",
            product_name="Squash",
            unit="kg"
        ),
        Product(
            product_id="PROD-MILK-WHOLE-L",
            vendor_id="CLEARWATER-HARVEST-DAIRY",
            category_id="CAT-WHOLEMILK",
            product_name="Whole Milk",
            unit="l"
        ),
        Product(
            product_id="PROD-BEEF-GROUND-L",
            vendor_id="IRONWOOD-HARVEST-BUTCHERY",
            category_id="CAT-GROUNDBEEF",
            product_name="Ground Beef",
            unit="kg"
        ),
    ]
    session.add_all(products)
    session.flush()

    # --- Shipments ---
    # A shipment is a delivery from a local vendor to our warehouse.
    # ID format matches CIS spec: SHIP-VENDORCODE-YYYYMMDD-XXX
    shipments = [
        Shipment(
            shipment_id="SHIP-MAPLE-20260301-001",
            vendor_id="MAPLEWOOD-HARVEST-FARM",
            shipment_date=datetime(2026, 3, 1, tzinfo=UTC)
        ),
        Shipment(
            shipment_id="SHIP-CLEAR-20260305-001",
            vendor_id="CLEARWATER-HARVEST-DAIRY",
            shipment_date=datetime(2026, 3, 5, tzinfo=UTC)
        ),
    ]
    session.add_all(shipments)
    session.flush()

    # --- Shipment Lots ---
    # Each lot tracks how much of a product arrived in a shipment.
    # This gets forwarded to CIS when registering a shipment.
    lots = [
        ShipmentLot(
            lot_id=uuid.uuid4(),
            shipment_id="SHIP-MAPLE-20260301-001",
            product_id="PROD-KALE",
            quantity_on_hand=150.0,
            unit="kg",
            last_restocked_date=datetime.now(UTC)
        ),
        ShipmentLot(
            lot_id=uuid.uuid4(),
            shipment_id="SHIP-MAPLE-20260301-001",
            product_id="PROD-SQUASH",
            quantity_on_hand=200.0,
            unit="kg",
            last_restocked_date=datetime.now(UTC)
        ),
        ShipmentLot(
            lot_id=uuid.uuid4(),
            shipment_id="SHIP-CLEAR-20260305-001",
            product_id="PROD-MILK-WHOLE-L",
            quantity_on_hand=100.0,
            unit="l",
            last_restocked_date=datetime.now(UTC)
        ),
    ]
    session.add_all(lots)

    session.commit()
    print("Seed data inserted successfully!")
    print(f"  {len(vendors)} vendors")
    print(f"  {len(categories)} categories")
    print(f"  {len(products)} products")
    print(f"  {len(shipments)} shipments")
    print(f"  {len(lots)} shipment lots")
