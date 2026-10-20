"""Transaction-safe order creation and state transitions."""
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.commerce import CartItem, Delivery, Order, OrderItem, Payment, Product

class OrderError(ValueError): pass

def create_order(user, delivery_name: str, delivery_phone: str, delivery_address: str, zone_id=None):
    items = db.session.scalars(select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id == user.id).with_for_update()).all()
    if not items:
        raise OrderError('Your cart is empty.')
    subtotal = 0
    snapshots = []
    for cart_item in items:
        product = db.session.scalar(select(Product).where(Product.id == cart_item.product_id).with_for_update())
        if not product or not product.is_active or product.vendor.status != 'approved':
            raise OrderError('A product in your cart is no longer available.')
        if product.stock_quantity < cart_item.quantity:
            raise OrderError(f'Not enough stock for {product.name}.')
        subtotal += product.price_ugx * cart_item.quantity
        snapshots.append((product, cart_item.quantity))
    if len({product.vendor_id for product, _quantity in snapshots}) > 1:
        raise OrderError('For now, place separate orders for products from different vendors.')
    delivery_fee = 3000 if subtotal else 0
    order = Order(user_id=user.id, delivery_name=delivery_name.strip(), delivery_phone=delivery_phone.strip(), delivery_address=delivery_address.strip(), zone_id=zone_id, subtotal_ugx=subtotal, delivery_fee_ugx=delivery_fee, total_ugx=subtotal+delivery_fee, status='placed', payment_status='pending')
    db.session.add(order)
    db.session.flush()
    for product, quantity in snapshots:
        product.stock_quantity -= quantity
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, vendor_id=product.vendor_id, product_name=product.name, unit_price_ugx=product.price_ugx, quantity=quantity, line_total_ugx=product.price_ugx*quantity))
    db.session.add(Delivery(order_id=order.id, status='unassigned'))
    db.session.add(Payment(order_id=order.id, method='cash_on_delivery', status='pending', amount_ugx=order.total_ugx))
    for item in items: db.session.delete(item)
    return order

ALLOWED_TRANSITIONS = {
    'placed': {'confirmed','cancelled'}, 'confirmed': {'preparing','cancelled'},
    'preparing': {'ready','cancelled'}, 'ready': {'assigned','cancelled'},
    'assigned': {'picked_up','cancelled'}, 'picked_up': {'delivered'},
    'delivered': set(), 'cancelled': set(),
}

def transition_order(order, new_status):
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise OrderError('That order status transition is not allowed.')
    if new_status == 'cancelled':
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            if product: product.stock_quantity += item.quantity
    order.status = new_status
    return order
