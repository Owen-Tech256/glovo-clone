"""Core marketplace persistence models for the first usable commerce release."""
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, PrimaryKeyMixin, PublicIdMixin, TimestampMixin

class CustomerProfile(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'customer_profiles'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

class ServiceZone(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'service_zones'
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))

class VendorProfile(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'vendor_profiles'
    __table_args__ = (CheckConstraint("status IN ('pending','approved','rejected','suspended')", name='status_allowed'),)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    business_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    phone: Mapped[str | None] = mapped_column(String(30))
    zone_id: Mapped[int | None] = mapped_column(ForeignKey('service_zones.id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    products = relationship('Product', back_populates='vendor', cascade='save-update, merge')

class Product(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'products'
    __table_args__ = (CheckConstraint('price_ugx >= 0', name='price_nonnegative'), CheckConstraint('stock_quantity >= 0', name='stock_nonnegative'), Index('ix_products_visible_category', 'is_active', 'category'))
    vendor_id: Mapped[int] = mapped_column(ForeignKey('vendor_profiles.id', ondelete='RESTRICT'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    price_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    image_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    vendor = relationship('VendorProfile', back_populates='products')

class CartItem(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'cart_items'
    __table_args__ = (UniqueConstraint('user_id','product_id', name='uq_cart_items_user_product'), CheckConstraint('quantity > 0', name='quantity_positive'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    product = relationship('Product')

class Order(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'orders'
    __table_args__ = (CheckConstraint("status IN ('placed','confirmed','preparing','ready','assigned','picked_up','delivered','cancelled')", name='status_allowed'), CheckConstraint('subtotal_ugx >= 0 AND delivery_fee_ugx >= 0 AND total_ugx >= 0', name='amounts_nonnegative'), Index('ix_orders_user_created', 'user_id','created_at'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'placed'"))
    delivery_name: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(300), nullable=False)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey('service_zones.id', ondelete='RESTRICT'))
    subtotal_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_fee_ugx: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    total_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(PrimaryKeyMixin, Base):
    __tablename__ = 'order_items'
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    vendor_id: Mapped[int] = mapped_column(ForeignKey('vendor_profiles.id', ondelete='RESTRICT'), nullable=False)
    product_name: Mapped[str] = mapped_column(String(180), nullable=False)
    unit_price_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    order = relationship('Order', back_populates='items')

class Delivery(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'deliveries'
    __table_args__ = (CheckConstraint("status IN ('unassigned','assigned','picked_up','in_transit','delivered','failed')", name='status_allowed'),)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='RESTRICT'), unique=True, nullable=False)
    rider_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'unassigned'"))
    delivery_notes: Mapped[str | None] = mapped_column(Text)

class Payment(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'payments'
    __table_args__ = (CheckConstraint("status IN ('pending','succeeded','failed','refunded')", name='status_allowed'), CheckConstraint('amount_ugx >= 0', name='amount_nonnegative'), UniqueConstraint('provider_reference', name='uq_payments_provider_reference'))
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'cash_on_delivery'"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    amount_ugx: Mapped[int] = mapped_column(Integer, nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(120))

class SupportTicket(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'support_tickets'
    __table_args__ = (CheckConstraint("status IN ('open','in_progress','resolved','closed')", name='status_allowed'),)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.id', ondelete='RESTRICT'))
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'open'"))

class Promotion(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = 'promotions'
    __table_args__ = (CheckConstraint('budget_ugx >= 0', name='budget_nonnegative'),)
    vendor_id: Mapped[int] = mapped_column(ForeignKey('vendor_profiles.id', ondelete='RESTRICT'), nullable=False)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    budget_ugx: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))


class RiderApplication(PrimaryKeyMixin, PublicIdMixin, TimestampMixin, Base):
    __tablename__ = "rider_applications"
    __table_args__ = (CheckConstraint("status IN ('pending','approved','rejected')", name='status_allowed'),)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
