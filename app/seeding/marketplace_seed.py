"""Fictional, idempotent development-only data for local acceptance testing."""
from datetime import datetime, timezone
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from app.models.identity import User, Role, UserRole
from app.models.commerce import CustomerProfile, ServiceZone, VendorProfile, Product, RiderApplication
from app.seeding import SeedStats

DEMO_PASSWORD = 'LocalDemoOnly-ChangeMe-123!'

def run(session):
    created = skipped = 0
    zone = session.scalar(select(ServiceZone).where(ServiceZone.name == 'Central Kampala'))
    if zone is None:
        zone = ServiceZone(name='Central Kampala', city='Kampala', is_active=True); session.add(zone); session.flush(); created += 1
    accounts = [
        ('customer.demo@example.test','Demo Customer','customer'),
        ('vendor.demo@example.test','Demo Vendor Owner','vendor_owner'),
        ('admin.demo@example.test','Demo Operations Admin','operations_manager'),
        ('rider.demo@example.test','Demo Rider','rider'),
    ]
    users = {}
    for email, name, role_code in accounts:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email,password_hash=generate_password_hash(DEMO_PASSWORD),status='active',status_changed_at=datetime.now(timezone.utc)); session.add(user); session.flush(); created += 1
        else: skipped += 1
        users[role_code] = user
        role = session.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            role = Role(code=role_code,name=role_code.replace('_',' ').title()); session.add(role); session.flush(); created += 1
        if session.get(UserRole,(user.id,role.id)) is None:
            session.add(UserRole(user_id=user.id,role_id=role.id)); created += 1
        else: skipped += 1
        if role_code == 'customer' and session.scalar(select(CustomerProfile).where(CustomerProfile.user_id == user.id)) is None:
            session.add(CustomerProfile(user_id=user.id,full_name=name)); created += 1
        if role_code == 'rider' and session.scalar(select(RiderApplication).where(RiderApplication.user_id == user.id)) is None:
            session.add(RiderApplication(user_id=user.id,phone='+256700000004',vehicle_type='Motorcycle',status='pending')); created += 1
    vendor_user = users['vendor_owner']
    vendor = session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id == vendor_user.id))
    if vendor is None:
        vendor = VendorProfile(owner_user_id=vendor_user.id,business_name='Kampala Fresh Market',category='Groceries',description='Fictional demo grocery shop for local testing.',phone='+256700000001',zone_id=zone.id,status='approved',is_featured=True); session.add(vendor); session.flush(); created += 1
    else: skipped += 1
    samples = [
        ('Fresh Bananas','Groceries','A bunch of fresh bananas.',4500,30),
        ('Farm Eggs (Tray)','Groceries','Locally sourced eggs.',15000,20),
        ('Ground Coffee 250g','Food','Freshly packed coffee for your morning cup.',12000,15),
        ('Reusable Shopping Bag','Home & living','A reusable everyday shopping bag.',5000,40),
    ]
    for name, category, description, price, stock in samples:
        if session.scalar(select(Product).where(Product.vendor_id==vendor.id,Product.name==name)) is None:
            session.add(Product(vendor_id=vendor.id,name=name,category=category,description=description,price_ugx=price,stock_quantity=stock,is_active=True)); created += 1
        else: skipped += 1
    return SeedStats(created=created,skipped=skipped)
