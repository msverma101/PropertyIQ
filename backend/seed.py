import os
import asyncio
from sqlmodel import SQLModel, create_engine, Session
from models import Owner, Property, Flat, Tenant, Vendor, PropertyOwnerLink, CONTEXT_STORE_DIR, init_flat_details

# SQLite Database path
DB_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "database.db")
)
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, echo=True)

async def seed_data():
    print(f"Dropping and recreating tables in database: {DB_FILE}")
    # Drop all tables first to ensure clean state
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        print("Seeding database with updated hackathon phone numbers & real emails...")

        # 1. Create Owners
        # Owner 1 (Hans Schmidt - Primary) maps to adityaladwa11@gmail.com
        owner1 = Owner(id="owner_001", name="Hans Schmidt", phone="+491777003294", email="adityaladwa11@gmail.com")
        owner2 = Owner(id="owner_002", name="Markus Weber", phone="+491709999992", email="m.weber@weber-properties.de")
        # Owner 3 (Sabine Weber - Co-owner of prop_001) maps to adityaladawa09@gmail.com
        owner3 = Owner(id="owner_003", name="Sabine Weber", phone="+491709999993", email="adityaladawa09@gmail.com")
        session.add_all([owner1, owner2, owner3])

        # 2. Create Tenants
        # Max Müller (Tenant) maps to aditya_ladawa@moderncoe.edu.in
        tenant1 = Tenant(id="tenant_001", name="Max Müller", phone="+4917636766245", email="aditya_ladawa@moderncoe.edu.in")
        tenant2 = Tenant(id="tenant_002", name="Jonas Becker", phone="+491707654321", email="jonas.becker@web.de")
        tenant3 = Tenant(id="tenant_003", name="Anna Krause", phone="+491711112222", email="anna.krause@gmx.de")
        tenant4 = Tenant(id="tenant_004", name="Sarah Fischer", phone="+491713334444", email="sarah.fischer@outlook.com")
        tenant5 = Tenant(id="tenant_005", name="Felix Wagner", phone="+491715556666", email="felix.wagner@hotmail.com")
        session.add_all([tenant1, tenant2, tenant3, tenant4, tenant5])

        # 3. Create Properties
        prop1 = Property(id="prop_001", name="Musterstraße 12", address="Musterstraße 12, 10115 Berlin", zipcode="10115")
        prop2 = Property(id="prop_002", name="Hauptstraße 45", address="Hauptstraße 45, 10117 Berlin", zipcode="10117")
        prop3 = Property(id="prop_003", name="Schönhauser Allee 89", address="Schönhauser Allee 89, 10439 Berlin", zipcode="10439")
        session.add_all([prop1, prop2, prop3])

        # 4. Create Property Owner Links
        link1 = PropertyOwnerLink(owner_id="owner_001", property_id="prop_001")
        link2 = PropertyOwnerLink(owner_id="owner_003", property_id="prop_001") # co-owner
        link3 = PropertyOwnerLink(owner_id="owner_001", property_id="prop_002")
        link4 = PropertyOwnerLink(owner_id="owner_002", property_id="prop_003")
        session.add_all([link1, link2, link3, link4])

        # 5. Create Flats (and set is_rented based on tenant presence)
        flat1 = Flat(id="flat_001", flat_no="Apt 3B", property_id="prop_001", tenant_id="tenant_001", is_rented=True)
        flat2 = Flat(id="flat_002", flat_no="Apt 2A", property_id="prop_001", tenant_id="tenant_002", is_rented=True)
        flat3 = Flat(id="flat_003", flat_no="Apt 1", property_id="prop_002", tenant_id="tenant_003", is_rented=True)
        flat4 = Flat(id="flat_004", flat_no="Apt 2", property_id="prop_002", tenant_id="tenant_004", is_rented=True)
        flat5 = Flat(id="flat_005", flat_no="Apt 4", property_id="prop_003", tenant_id="tenant_005", is_rented=True)
        flat6 = Flat(id="flat_006", flat_no="Apt 5", property_id="prop_003", tenant_id=None, is_rented=False) # Vacant
        session.add_all([flat1, flat2, flat3, flat4, flat5, flat6])

        # 6. Create Vendors
        # RohrBlitz Berlin (Plumbing) maps to adityaladawa11@gmail.com
        vendor1 = Vendor(id="vendor_001", name="Berlin HVAC GmbH", phone="+491721111111", email="info@berlin-hvac.de", category="hvac", zipcode_coverage="10115,10117")
        vendor2 = Vendor(id="vendor_002", name="WärmeFix24", phone="+491722222222", email="service@waermefix24.de", category="hvac", zipcode_coverage="10115,10117,10439")
        vendor3 = Vendor(id="vendor_003", name="RohrBlitz Berlin", phone="+4915252003916", email="adityaladawa11@gmail.com", category="plumbing", zipcode_coverage="10115,10117,10439")
        vendor4 = Vendor(id="vendor_004", name="SchlüsselDienst24", phone="+491724444444", email="locksmith@schluesseldienst24.de", category="locksmith", zipcode_coverage="10115,10117,10439")
        vendor5 = Vendor(id="vendor_005", name="ElektroSchmidt", phone="+491725555555", email="support@elektroschmidt.de", category="electrical", zipcode_coverage="10115,10117,10439")
        session.add_all([vendor1, vendor2, vendor3, vendor4, vendor5])

        session.commit()
        print("Database seeded in SQLite successfully!")

    # 7. Initialize filesystem context folders
    print("Initializing property-centric context store folders...")
    
    # Init Context for Flat 1 (Max Müller)
    await init_flat_details(
        property_name="Musterstraße 12",
        flat_no="Apt 3B",
        owners_data=[
            {"id": "owner_001", "name": "Hans Schmidt", "phone": "+491777003294", "email": "adityaladwa11@gmail.com"},
            {"id": "owner_003", "name": "Sabine Weber", "phone": "+491709999993", "email": "adityaladawa09@gmail.com"}
        ],
        tenant_data={"id": "tenant_001", "name": "Max Müller", "phone": "+4917636766245", "email": "aditya_ladawa@moderncoe.edu.in"}
    )
    
    # Init Context for Flat 2 (Jonas Becker)
    await init_flat_details(
        property_name="Musterstraße 12",
        flat_no="Apt 2A",
        owners_data=[
            {"id": "owner_001", "name": "Hans Schmidt", "phone": "+491777003294", "email": "adityaladwa11@gmail.com"},
            {"id": "owner_003", "name": "Sabine Weber", "phone": "+491709999993", "email": "adityaladawa09@gmail.com"}
        ],
        tenant_data={"id": "tenant_002", "name": "Jonas Becker", "phone": "+491707654321", "email": "jonas.becker@web.de"}
    )

    # Init Context for Flat 3 (Anna Krause)
    await init_flat_details(
        property_name="Hauptstraße 45",
        flat_no="Apt 1",
        owners_data=[
            {"id": "owner_001", "name": "Hans Schmidt", "phone": "+491777003294", "email": "adityaladwa11@gmail.com"}
        ],
        tenant_data={"id": "tenant_003", "name": "Anna Krause", "phone": "+491711112222", "email": "anna.krause@gmx.de"}
    )
    
    # Init Context for Flat 4 (Sarah Fischer)
    await init_flat_details(
        property_name="Hauptstraße 45",
        flat_no="Apt 2",
        owners_data=[
            {"id": "owner_001", "name": "Hans Schmidt", "phone": "+491777003294", "email": "adityaladwa11@gmail.com"}
        ],
        tenant_data={"id": "tenant_004", "name": "Sarah Fischer", "phone": "+491713334444", "email": "sarah.fischer@outlook.com"}
    )

    # Init Context for Flat 5 (Felix Wagner)
    await init_flat_details(
        property_name="Schönhauser Allee 89",
        flat_no="Apt 4",
        owners_data=[
            {"id": "owner_002", "name": "Markus Weber", "phone": "+491709999992", "email": "m.weber@weber-properties.de"}
        ],
        tenant_data={"id": "tenant_005", "name": "Felix Wagner", "phone": "+491715556666", "email": "felix.wagner@hotmail.com"}
    )

    print("Context store folder hierarchies initialized successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
