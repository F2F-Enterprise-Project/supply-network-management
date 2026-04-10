"""
seed.py - Runs on container startup to set up the database.
Creates all tables and inserts sample data for locally onboarded vendors
(these are vendors that exist in SNM but NOT in AgNet).
Only seeds if the database is empty to prevent duplicates on restart.

Category structure is 2 levels only:
  Level 1: Produce, Dairy, Meat
  Level 2: the category a product belongs to
The 3rd element in AgNet's hierarchy array is the product name, not a category.
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

app_module.app.build_app()
print("Tables created.")

with Session(engine) as session:

    existing = session.execute(select(func.count()).select_from(Vendor)).scalar()
    if existing > 0:
        print(f"Database already has {existing} vendors, skipping seed.")
        exit(0)

    # -------------------------------------------------------------------------
    # Vendors — local only, not in AgNet
    # -------------------------------------------------------------------------
    vendors = [
        Vendor(vendor_id="MAPLEWOOD-HARVEST-FARM",    name="Maplewood Harvest Farm",    type="Farm",    reg_state="Active", order_count=0, last_order=datetime.now(UTC)),
        Vendor(vendor_id="CLEARWATER-HARVEST-DAIRY",  name="Clearwater Harvest Dairy",  type="Dairy",   reg_state="Active", order_count=0, last_order=datetime.now(UTC)),
        Vendor(vendor_id="IRONWOOD-HARVEST-BUTCHERY", name="Ironwood Harvest Butchery", type="Butcher", reg_state="New",    order_count=0, last_order=datetime.now(UTC)),
    ]
    session.add_all(vendors)
    session.flush()

    # -------------------------------------------------------------------------
    # Categories — 2 levels only, names match AgNet exactly
    # -------------------------------------------------------------------------
    categories = [
        # Level 1
        Category(category_id="CAT-PRODUCE", parent_category_id="", category_name="Produce", level=1),
        Category(category_id="CAT-DAIRY",   parent_category_id="", category_name="Dairy",   level=1),
        Category(category_id="CAT-MEAT",    parent_category_id="", category_name="Meat",    level=1),

        # Level 2 — Produce
        Category(category_id="CAT-ROOTVEGETABLES", parent_category_id="CAT-PRODUCE", category_name="RootVegetables", level=2),
        Category(category_id="CAT-VEGETABLES",     parent_category_id="CAT-PRODUCE", category_name="Vegetables",     level=2),
        Category(category_id="CAT-LEAFYGREENS",    parent_category_id="CAT-PRODUCE", category_name="LeafyGreens",    level=2),
        Category(category_id="CAT-FRUIT",          parent_category_id="CAT-PRODUCE", category_name="Fruit",          level=2),

        # Level 2 — Dairy
        Category(category_id="CAT-MILK",   parent_category_id="CAT-DAIRY", category_name="Milk",   level=2),
        Category(category_id="CAT-CREAM",  parent_category_id="CAT-DAIRY", category_name="Cream",  level=2),
        Category(category_id="CAT-BUTTER", parent_category_id="CAT-DAIRY", category_name="Butter", level=2),
        Category(category_id="CAT-CHEESE", parent_category_id="CAT-DAIRY", category_name="Cheese", level=2),
        Category(category_id="CAT-YOGURT", parent_category_id="CAT-DAIRY", category_name="Yogurt", level=2),

        # Level 2 — Meat
        Category(category_id="CAT-BEEF",    parent_category_id="CAT-MEAT", category_name="Beef",    level=2),
        Category(category_id="CAT-POULTRY", parent_category_id="CAT-MEAT", category_name="Poultry", level=2),
        Category(category_id="CAT-LAMB",    parent_category_id="CAT-MEAT", category_name="Lamb",    level=2),
        Category(category_id="CAT-PORK",    parent_category_id="CAT-MEAT", category_name="Pork",    level=2),
    ]
    session.add_all(categories)
    session.flush()

    # -------------------------------------------------------------------------
    # Products — all AgNet products plus Kale and Squash (local-only)
    # -------------------------------------------------------------------------
    products = [
        # Maplewood Harvest Farm — Produce
        Product(product_id="PROD-CARROTS",  vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-ROOTVEGETABLES", product_name="Carrots",  unit="kg"),
        Product(product_id="PROD-ONIONS",   vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-ROOTVEGETABLES", product_name="Onions",   unit="kg"),
        Product(product_id="PROD-POTATOES", vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-ROOTVEGETABLES", product_name="Potatoes", unit="kg"),
        Product(product_id="PROD-TOMATOES", vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-VEGETABLES",     product_name="Tomatoes", unit="kg"),
        Product(product_id="PROD-BROCCOLI", vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-VEGETABLES",     product_name="Broccoli", unit="kg"),
        Product(product_id="PROD-SQUASH",   vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-VEGETABLES",     product_name="Squash",   unit="kg"),
        Product(product_id="PROD-SPINACH",  vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-LEAFYGREENS",    product_name="Spinach",  unit="kg"),
        Product(product_id="PROD-KALE",     vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-LEAFYGREENS",    product_name="Kale",     unit="kg"),
        Product(product_id="PROD-PEARS",    vendor_id="MAPLEWOOD-HARVEST-FARM", category_id="CAT-FRUIT",          product_name="Pears",    unit="kg"),

        # Clearwater Harvest Dairy
        Product(product_id="PROD-MILK-WHOLE",      vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-MILK",   product_name="Whole Milk",      unit="l"),
        Product(product_id="PROD-MILK-2PCT",       vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-MILK",   product_name="2% Milk",         unit="l"),
        Product(product_id="PROD-CREAM-35",        vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-CREAM",  product_name="35% Cream",       unit="l"),
        Product(product_id="PROD-CREAM-10",        vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-CREAM",  product_name="10% Cream",       unit="l"),
        Product(product_id="PROD-BUTTER-UNSALTED", vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-BUTTER", product_name="Unsalted Butter", unit="kg"),
        Product(product_id="PROD-CHEESE-CHEDDAR",  vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-CHEESE", product_name="Cheddar Cheese",  unit="kg"),
        Product(product_id="PROD-CHEESE-MOZZA",    vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-CHEESE", product_name="Mozzarella Cheese", unit="kg"),
        Product(product_id="PROD-YOGURT-PLAIN",    vendor_id="CLEARWATER-HARVEST-DAIRY", category_id="CAT-YOGURT", product_name="Plain Yogurt",    unit="kg"),

        # Ironwood Harvest Butchery
        Product(product_id="PROD-BEEF-GROUND",    vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-BEEF",    product_name="Ground Beef",    unit="kg"),
        Product(product_id="PROD-BEEF-STEAK",     vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-BEEF",    product_name="Beef Steak",     unit="kg"),
        Product(product_id="PROD-CHICKEN-BREAST", vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-POULTRY", product_name="Chicken Breast", unit="kg"),
        Product(product_id="PROD-CHICKEN-THIGH",  vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-POULTRY", product_name="Chicken Thigh",  unit="kg"),
        Product(product_id="PROD-TURKEY-GROUND",  vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-POULTRY", product_name="Ground Turkey",  unit="kg"),
        Product(product_id="PROD-LAMB-LEG",       vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-LAMB",    product_name="Lamb Leg",       unit="kg"),
        Product(product_id="PROD-PORK-SAUSAGE",   vendor_id="IRONWOOD-HARVEST-BUTCHERY", category_id="CAT-PORK",    product_name="Pork Sausage",   unit="kg"),
    ]
    session.add_all(products)
    session.flush()

    # -------------------------------------------------------------------------
    # Shipments
    # -------------------------------------------------------------------------
    shipments = [
        Shipment(shipment_id="SHIP-MAPLE-20260301-001", vendor_id="MAPLEWOOD-HARVEST-FARM",    shipment_date=datetime(2026, 3, 1,  9,  0, 0, tzinfo=UTC)),
        Shipment(shipment_id="SHIP-CLEAR-20260305-001", vendor_id="CLEARWATER-HARVEST-DAIRY",  shipment_date=datetime(2026, 3, 5,  8, 30, 0, tzinfo=UTC)),
        Shipment(shipment_id="SHIP-IRON-20260310-001",  vendor_id="IRONWOOD-HARVEST-BUTCHERY", shipment_date=datetime(2026, 3, 10, 11,  0, 0, tzinfo=UTC)),
    ]
    session.add_all(shipments)
    session.flush()

    # -------------------------------------------------------------------------
    # Shipment Lots
    # -------------------------------------------------------------------------
    lots = [
        # Maplewood
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-CARROTS",  quantity_on_hand=120.250, unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-ONIONS",   quantity_on_hand=98.000,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-POTATOES", quantity_on_hand=150.000, unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-TOMATOES", quantity_on_hand=90.750,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-BROCCOLI", quantity_on_hand=60.000,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-SQUASH",   quantity_on_hand=80.500,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-SPINACH",  quantity_on_hand=75.500,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-KALE",     quantity_on_hand=55.000,  unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-MAPLE-20260301-001", product_id="PROD-PEARS",    quantity_on_hand=110.000, unit="kg", last_restocked_date=datetime(2026, 3, 1, 9, 0, 0, tzinfo=UTC)),

        # Clearwater
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-MILK-WHOLE",      quantity_on_hand=250.500, unit="l",  last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-MILK-2PCT",       quantity_on_hand=180.000, unit="l",  last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-CREAM-35",        quantity_on_hand=100.000, unit="l",  last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-CREAM-10",        quantity_on_hand=120.000, unit="l",  last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-BUTTER-UNSALTED", quantity_on_hand=75.500,  unit="kg", last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-CHEESE-CHEDDAR",  quantity_on_hand=60.000,  unit="kg", last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-CHEESE-MOZZA",    quantity_on_hand=45.000,  unit="kg", last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-CLEAR-20260305-001", product_id="PROD-YOGURT-PLAIN",    quantity_on_hand=90.000,  unit="kg", last_restocked_date=datetime(2026, 3, 5, 8, 30, 0, tzinfo=UTC)),

        # Ironwood
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-BEEF-GROUND",    quantity_on_hand=180.000, unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-BEEF-STEAK",     quantity_on_hand=95.250,  unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-CHICKEN-BREAST", quantity_on_hand=110.000, unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-CHICKEN-THIGH",  quantity_on_hand=85.000,  unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-TURKEY-GROUND",  quantity_on_hand=70.000,  unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-LAMB-LEG",       quantity_on_hand=50.000,  unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
        ShipmentLot(lot_id=uuid.uuid4(), shipment_id="SHIP-IRON-20260310-001", product_id="PROD-PORK-SAUSAGE",   quantity_on_hand=65.750,  unit="kg", last_restocked_date=datetime(2026, 3, 10, 11, 0, 0, tzinfo=UTC)),
    ]
    session.add_all(lots)

    session.commit()
    print("Seed data inserted successfully!")
    print(f"  {len(vendors)} vendors")
    print(f"  {len(categories)} categories")
    print(f"  {len(products)} products")
    print(f"  {len(shipments)} shipments")
    print(f"  {len(lots)} shipment lots")