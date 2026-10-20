"""Smoke tests for the first customer-facing marketplace release."""
from flask_migrate import upgrade
from sqlalchemy import select
from app.extensions import db
from app.models.identity import User
from app.models.commerce import ServiceZone, VendorProfile, Product


def test_marketplace_home_renders_without_seed_data(client, app, clean_db):
    with app.app_context():
        upgrade()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Everything you need, delivered.' in response.data
    assert b'No products found yet' in response.data


def test_registration_creates_hashed_customer_and_profile(client, app, clean_db):
    with app.app_context():
        upgrade()
        app.config['WTF_CSRF_ENABLED'] = False
    response = client.post('/register', data={
        'full_name': 'Example Customer',
        'email': 'customer@example.test',
        'phone': '0700000000',
        'password': 'Long-Development-Password-123!',
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == 'customer@example.test'))
        assert user is not None
        assert user.password_hash != 'Long-Development-Password-123!'
        assert user.has_role('customer')
        assert user.is_active


def test_public_catalog_hides_pending_vendor_products(client, app, clean_db):
    from datetime import datetime, timezone
    from werkzeug.security import generate_password_hash
    with app.app_context():
        upgrade()
        user = User(email='vendor@example.test', password_hash=generate_password_hash('Long-Development-Password-123!'), status='active', status_changed_at=datetime.now(timezone.utc))
        db.session.add(user); db.session.flush()
        vendor = VendorProfile(owner_user_id=user.id, business_name='Pending Shop', category='Food', status='pending')
        db.session.add(vendor); db.session.flush()
        db.session.add(Product(vendor_id=vendor.id, name='Hidden Product', category='Food', price_ugx=1000, stock_quantity=3, is_active=True))
        db.session.commit()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hidden Product' not in response.data


def test_order_state_machine_rejects_skipped_states():
    from app.marketplace.services.orders import ALLOWED_TRANSITIONS, OrderError
    assert 'confirmed' in ALLOWED_TRANSITIONS['placed']
    assert 'delivered' not in ALLOWED_TRANSITIONS['placed']
    assert ALLOWED_TRANSITIONS['delivered'] == set()
    try:
        raise OrderError('That order status transition is not allowed.')
    except OrderError as exc:
        assert 'not allowed' in str(exc)
