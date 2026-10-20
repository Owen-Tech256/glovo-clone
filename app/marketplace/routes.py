from datetime import datetime, timezone
from functools import wraps
from flask import abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_limiter.util import get_remote_address
from sqlalchemy import or_, select, func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db, limiter, login_manager
from app.models.identity import User, Role, UserRole, AuthToken, AuditLog
from app.models.commerce import (CartItem, CustomerProfile, Delivery, Order, OrderItem, Payment, Product, Promotion, ServiceZone, SupportTicket, VendorProfile, RiderApplication)
from . import bp
from .services.orders import create_order, OrderError, transition_order

@login_manager.user_loader
def _load_user(user_id):
    try: return db.session.get(User, int(user_id))
    except (TypeError, ValueError): return None

@bp.before_app_request
def enforce_active_session():
    if current_user.is_authenticated:
        if not current_user.is_active or session.get('_session_version') != current_user.session_version:
            logout_user()
            session.pop('_session_version', None)


def role_required(*roles):
    def decorate(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_active: abort(403)
            if not current_user.has_role(*roles): abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorate

def _audit(action, entity_type, entity_id, after=None):
    db.session.add(AuditLog(actor_user_id=current_user.id if current_user.is_authenticated else None, actor_label=None if current_user.is_authenticated else 'anonymous', action=action, entity_type=entity_type, entity_id=str(entity_id), after_data=after or {}, event_metadata={'request_id': getattr(g, 'request_id', None)}))

def _role(code):
    role = db.session.scalar(select(Role).where(Role.code == code))
    if role is None:
        role = Role(code=code, name=code.replace('_',' ').title()); db.session.add(role); db.session.flush()
    return role

def _assign_role(user, code):
    role = _role(code)
    if db.session.get(UserRole, (user.id, role.id)) is None: db.session.add(UserRole(user_id=user.id, role_id=role.id))

@bp.get('/')
def home():
    q = request.args.get('q','').strip()[:100]
    stmt = select(Product).join(VendorProfile).where(Product.is_active.is_(True), VendorProfile.status == 'approved')
    if q: stmt = stmt.where(or_(Product.name.ilike(f'%{q}%'), Product.description.ilike(f'%{q}%'), Product.category.ilike(f'%{q}%'), VendorProfile.business_name.ilike(f'%{q}%')))
    products = db.session.scalars(stmt.order_by(VendorProfile.is_featured.desc(), Product.created_at.desc()).limit(24)).all()
    vendors = db.session.scalars(select(VendorProfile).where(VendorProfile.status=='approved').order_by(VendorProfile.is_featured.desc(), VendorProfile.business_name).limit(8)).all()
    zones = db.session.scalars(select(ServiceZone).where(ServiceZone.is_active.is_(True)).order_by(ServiceZone.city, ServiceZone.name)).all()
    return render_template('marketplace/home.html', products=products, vendors=vendors, zones=zones, q=q)

@bp.route('/register', methods=['GET','POST'])
@limiter.limit('5 per hour')
def register():
    if current_user.is_authenticated: return redirect(url_for('marketplace.home'))
    if request.method == 'POST':
        name=request.form.get('full_name','').strip()[:120]; email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip()[:30]; password=request.form.get('password','')
        if not name or len(name)<2 or '@' not in email or len(password)<12:
            flash('Enter your name, a valid email, and a password of at least 12 characters.', 'danger')
        else:
            user=User(email=email,password_hash=generate_password_hash(password),status='active',status_changed_at=datetime.now(timezone.utc))
            try:
                db.session.add(user); db.session.flush(); _assign_role(user,'customer'); db.session.add(CustomerProfile(user_id=user.id,full_name=name,phone=phone or None)); _audit('identity.customer_registered','user',user.public_id,{'email':email}); db.session.commit(); login_user(user); session['_session_version']=user.session_version; flash('Your account is ready. Welcome.', 'success'); return redirect(url_for('marketplace.home'))
            except IntegrityError:
                db.session.rollback(); flash('An account with those details may already exist.', 'danger')
    return render_template('marketplace/register.html')

@bp.route('/login', methods=['GET','POST'])
@limiter.limit('10 per hour')
def login():
    if current_user.is_authenticated: return redirect(url_for('marketplace.home'))
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=db.session.scalar(select(User).where(User.email==email))
        if user and user.is_active and check_password_hash(user.password_hash,password):
            login_user(user, remember=False, fresh=True); session['_session_version']=user.session_version; user.last_login_at=datetime.now(timezone.utc); _audit('identity.login_succeeded','user',user.public_id); db.session.commit()
            nxt=request.args.get('next','')
            if nxt.startswith('/') and not nxt.startswith('//'): return redirect(nxt)
            return redirect(url_for('marketplace.home'))
        flash('Email or password was not recognised.', 'danger')
    return render_template('marketplace/login.html')

@bp.post('/logout')
@login_required
def logout():
    _audit('identity.logout','user',current_user.public_id); db.session.commit(); logout_user(); session.pop('_session_version', None); flash('You have signed out.', 'info'); return redirect(url_for('marketplace.home'))

@bp.get('/product/<uuid:public_id>')
def product_detail(public_id):
    product=db.session.scalar(select(Product).join(VendorProfile).where(Product.public_id==public_id, Product.is_active.is_(True), VendorProfile.status=='approved'))
    if not product: abort(404)
    return render_template('marketplace/product.html', product=product)

@bp.post('/cart/add/<uuid:public_id>')
@login_required
def cart_add(public_id):
    product=db.session.scalar(select(Product).join(VendorProfile).where(Product.public_id==public_id,Product.is_active.is_(True),VendorProfile.status=='approved'))
    if not product: abort(404)
    try: quantity=max(1,min(99,int(request.form.get('quantity','1'))))
    except ValueError: quantity=1
    item=db.session.scalar(select(CartItem).where(CartItem.user_id==current_user.id,CartItem.product_id==product.id))
    if item: item.quantity += quantity
    else: db.session.add(CartItem(user_id=current_user.id,product_id=product.id,quantity=quantity))
    db.session.commit(); flash('Added to your cart.', 'success'); return redirect(request.referrer if request.referrer and request.referrer.startswith('/') else url_for('marketplace.cart'))

@bp.get('/cart')
@login_required
def cart():
    items=db.session.scalars(select(CartItem).where(CartItem.user_id==current_user.id).order_by(CartItem.created_at)).all()
    total=sum(i.product.price_ugx*i.quantity for i in items)
    return render_template('marketplace/cart.html',items=items,total=total)

@bp.post('/cart/update/<int:item_id>')
@login_required
def cart_update(item_id):
    item=db.session.scalar(select(CartItem).where(CartItem.id==item_id,CartItem.user_id==current_user.id))
    if not item: abort(404)
    try: quantity=int(request.form.get('quantity','1'))
    except ValueError: quantity=1
    if quantity <= 0: db.session.delete(item)
    else: item.quantity=min(quantity,99)
    db.session.commit(); return redirect(url_for('marketplace.cart'))

@bp.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    items=db.session.scalars(select(CartItem).where(CartItem.user_id==current_user.id)).all()
    if not items: flash('Your cart is empty.', 'info'); return redirect(url_for('marketplace.home'))
    total=sum(i.product.price_ugx*i.quantity for i in items)+3000
    if request.method=='POST':
        name=request.form.get('delivery_name','').strip()[:120]; phone=request.form.get('delivery_phone','').strip()[:30]; address=request.form.get('delivery_address','').strip()[:300]
        if not name or not phone or len(address)<5: flash('Complete the delivery details.', 'danger')
        else:
            try:
                order=create_order(current_user,name,phone,address); _audit('order.placed','order',order.public_id,{'total_ugx':order.total_ugx}); db.session.commit()
                flash('Order placed. Payment remains pending until a real payment or cash-on-delivery workflow is completed.', 'success'); return redirect(url_for('marketplace.order_detail',public_id=order.public_id))
            except OrderError as e: db.session.rollback(); flash(str(e),'danger')
    return render_template('marketplace/checkout.html',items=items,total=total)

@bp.get('/orders')
@login_required
def orders():
    rows=db.session.scalars(select(Order).where(Order.user_id==current_user.id).order_by(Order.created_at.desc())).all()
    return render_template('marketplace/orders.html',orders=rows)

@bp.get('/orders/<uuid:public_id>')
@login_required
def order_detail(public_id):
    order=db.session.scalar(select(Order).where(Order.public_id==public_id,Order.user_id==current_user.id))
    if not order: abort(404)
    return render_template('marketplace/order_detail.html',order=order)

@bp.route('/vendor/apply', methods=['GET','POST'])
@login_required
def vendor_apply():
    existing=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    if request.method=='POST':
        name=request.form.get('business_name','').strip()[:160]; category=request.form.get('category','').strip()[:60]; description=request.form.get('description','').strip()[:2000]; phone=request.form.get('phone','').strip()[:30]
        if not name or not category: flash('Business name and category are required.','danger')
        elif existing: flash('You already have a vendor application.','info')
        else:
            vendor=VendorProfile(owner_user_id=current_user.id,business_name=name,category=category,description=description,phone=phone or None,status='pending'); db.session.add(vendor); _assign_role(current_user,'vendor_owner'); _audit('vendor.application_submitted','vendor_profile',vendor.public_id,{'status':'pending'}); db.session.commit(); flash('Application submitted for administrator review.','success'); return redirect(url_for('marketplace.vendor_dashboard'))
    return render_template('marketplace/vendor_apply.html',vendor=existing)

@bp.get('/vendor')
@role_required('vendor_owner','vendor_staff')
def vendor_dashboard():
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    if not vendor: return render_template('marketplace/vendor_dashboard.html',vendor=None,products=[],orders=[])
    products=db.session.scalars(select(Product).where(Product.vendor_id==vendor.id).order_by(Product.created_at.desc())).all()
    order_rows=db.session.scalars(select(Order).join(OrderItem).where(OrderItem.vendor_id==vendor.id).distinct().order_by(Order.created_at.desc()).limit(50)).all()
    return render_template('marketplace/vendor_dashboard.html',vendor=vendor,products=products,orders=order_rows)

@bp.route('/vendor/products/new', methods=['GET','POST'])
@role_required('vendor_owner','vendor_staff')
def vendor_product_new():
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    if not vendor or vendor.status!='approved': abort(403)
    if request.method=='POST':
        try: price=int(request.form.get('price_ugx','-1')); stock=int(request.form.get('stock_quantity','0'))
        except ValueError: price=-1; stock=-1
        name=request.form.get('name','').strip()[:180]; category=request.form.get('category','').strip()[:60]
        if not name or not category or price<0 or stock<0: flash('Enter valid product details, price and stock.','danger')
        else:
            product=Product(vendor_id=vendor.id,name=name,category=category,description=request.form.get('description','').strip()[:2000],price_ugx=price,stock_quantity=stock,image_url=None,is_active=True); db.session.add(product); _audit('catalog.product_created','product',product.public_id,{'name':name}); db.session.commit(); flash('Product saved.','success'); return redirect(url_for('marketplace.vendor_dashboard'))
    return render_template('marketplace/product_form.html')

@bp.route('/vendor/orders/<uuid:public_id>/status', methods=['POST'])
@role_required('vendor_owner','vendor_staff')
def vendor_order_status(public_id):
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    order=db.session.scalar(select(Order).join(OrderItem).where(Order.public_id==public_id,OrderItem.vendor_id==vendor.id).distinct()) if vendor else None
    if not order or not vendor or vendor.status!='approved': abort(404)
    target=request.form.get('status','')
    if target not in {'confirmed','preparing','ready','cancelled'}: abort(400)
    try: transition_order(order,target); _audit('order.status_changed','order',order.public_id,{'status':target}); db.session.commit(); flash('Order status updated.','success')
    except OrderError as e: db.session.rollback(); flash(str(e),'danger')
    return redirect(url_for('marketplace.vendor_dashboard'))

@bp.route('/rider', methods=['GET','POST'])
@login_required
def rider_dashboard():
    if request.method=='POST':
        phone=request.form.get('phone','').strip()[:30]; vehicle=request.form.get('vehicle','').strip()[:80]
        if not phone or not vehicle: flash('Phone and vehicle type are required.','danger')
        else:
            existing=db.session.scalar(select(RiderApplication).where(RiderApplication.user_id==current_user.id))
            if existing: flash('You already have a rider application.','info')
            else:
                application=RiderApplication(user_id=current_user.id,phone=phone,vehicle_type=vehicle,status='pending'); db.session.add(application); _assign_role(current_user,'rider'); _audit('rider.application_submitted','rider_application',application.public_id,{'status':'pending'}); db.session.commit(); flash('Rider application recorded. Administrator approval is required before dispatch.','success')
    deliveries=db.session.scalars(select(Delivery).where(Delivery.rider_user_id==current_user.id).order_by(Delivery.created_at.desc())).all() if current_user.has_role('rider') else []
    return render_template('marketplace/rider_dashboard.html',deliveries=deliveries,applied=current_user.has_role('rider'))

@bp.post('/rider/deliveries/<uuid:public_id>/status')
@role_required('rider')
def rider_delivery_status(public_id):
    delivery=db.session.scalar(select(Delivery).join(RiderApplication, RiderApplication.user_id==Delivery.rider_user_id).where(Delivery.public_id==public_id,Delivery.rider_user_id==current_user.id,RiderApplication.status=='approved'))
    if not delivery: abort(404)
    target=request.form.get('status','')
    allowed={'assigned':{'picked_up'},'picked_up':{'in_transit'},'in_transit':{'delivered'}}
    if target not in allowed.get(delivery.status,set()): abort(400)
    delivery.status=target
    order=db.session.get(Order,delivery.order_id)
    if target=='picked_up': order.status='picked_up'
    elif target=='delivered': order.status='delivered'
    elif target=='in_transit': order.status='picked_up'
    db.session.commit(); flash('Delivery status updated.','success'); return redirect(url_for('marketplace.rider_dashboard'))

@bp.get('/admin')
@role_required('super_admin','operations_manager','support_agent','finance_operator')
def admin_dashboard():
    counts={'users':db.session.scalar(select(func.count()).select_from(User)) or 0,'vendors_pending':db.session.scalar(select(func.count()).select_from(VendorProfile).where(VendorProfile.status=='pending')) or 0,'orders':db.session.scalar(select(func.count()).select_from(Order)) or 0,'tickets':db.session.scalar(select(func.count()).select_from(SupportTicket).where(SupportTicket.status=='open')) or 0}
    vendors=db.session.scalars(select(VendorProfile).where(VendorProfile.status=='pending').order_by(VendorProfile.created_at)).all() if current_user.has_role('super_admin','operations_manager') else []
    tickets=db.session.scalars(select(SupportTicket).where(SupportTicket.status.in_(['open','in_progress'])).order_by(SupportTicket.created_at.desc()).limit(30)).all() if current_user.has_role('super_admin','operations_manager','support_agent') else []
    riders=db.session.scalars(select(RiderApplication).where(RiderApplication.status=='pending').order_by(RiderApplication.created_at)).all() if current_user.has_role('super_admin','operations_manager') else []
    unassigned=db.session.scalars(select(Delivery).join(Order, Order.id==Delivery.order_id).where(Delivery.status=='unassigned',Order.status=='ready').order_by(Delivery.created_at)).all() if current_user.has_role('super_admin','operations_manager') else []
    approved_riders=db.session.scalars(select(RiderApplication).where(RiderApplication.status=='approved').order_by(RiderApplication.created_at)).all() if unassigned else []
    return render_template('marketplace/admin.html',counts=counts,vendors=vendors,tickets=tickets,riders=riders,unassigned=unassigned,approved_riders=approved_riders)

@bp.post('/admin/vendors/<uuid:public_id>/review')
@role_required('super_admin','operations_manager')
def admin_vendor_review(public_id):
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.public_id==public_id))
    if not vendor: abort(404)
    status=request.form.get('status','')
    if status not in {'approved','rejected','suspended'}: abort(400)
    vendor.status=status; _audit('vendor.application_reviewed','vendor_profile',vendor.public_id,{'status':status}); db.session.commit(); flash('Vendor status updated.','success'); return redirect(url_for('marketplace.admin_dashboard'))

@bp.route('/support/new', methods=['GET','POST'])
@login_required
def support_new():
    if request.method=='POST':
        subject=request.form.get('subject','').strip()[:160]; message=request.form.get('message','').strip()[:5000]
        if not subject or not message: flash('Subject and message are required.','danger')
        else:
            ticket=SupportTicket(user_id=current_user.id,subject=subject,message=message); db.session.add(ticket); _audit('support.ticket_created','support_ticket',ticket.public_id); db.session.commit(); flash('Support request submitted.','success'); return redirect(url_for('marketplace.home'))
    return render_template('marketplace/support_new.html')

@bp.get('/api/catalog')
def api_catalog():
    q=request.args.get('q','').strip()[:100]
    stmt=select(Product).join(VendorProfile).where(Product.is_active.is_(True),VendorProfile.status=='approved')
    if q: stmt=stmt.where(or_(Product.name.ilike(f'%{q}%'),Product.category.ilike(f'%{q}%')))
    products=db.session.scalars(stmt.order_by(Product.name).limit(50)).all()
    response=jsonify({'items':[{'id':str(p.public_id),'name':p.name,'category':p.category,'price_ugx':p.price_ugx,'vendor':p.vendor.business_name,'stock_available':p.stock_quantity>0} for p in products]})
    response.headers['Cache-Control']='no-store'; return response

@bp.post('/admin/riders/<uuid:public_id>/review')
@role_required('super_admin','operations_manager')
def admin_rider_review(public_id):
    application=db.session.scalar(select(RiderApplication).where(RiderApplication.public_id==public_id))
    if not application: abort(404)
    status=request.form.get('status','')
    if status not in {'approved','rejected'}: abort(400)
    application.status=status
    _audit('rider.application_reviewed','rider_application',application.public_id,{'status':status})
    db.session.commit(); flash('Rider application updated.','success'); return redirect(url_for('marketplace.admin_dashboard'))

@bp.post('/admin/deliveries/<uuid:public_id>/assign')
@role_required('super_admin','operations_manager')
def admin_assign_delivery(public_id):
    delivery=db.session.scalar(select(Delivery).where(Delivery.public_id==public_id).with_for_update())
    if not delivery: abort(404)
    try: rider_id=int(request.form.get('rider_user_id',''))
    except ValueError: abort(400)
    approved_rider=db.session.scalar(select(RiderApplication).where(RiderApplication.user_id==rider_id,RiderApplication.status=='approved'))
    if not approved_rider: flash('Choose an approved rider.','danger'); return redirect(url_for('marketplace.admin_dashboard'))
    order=db.session.get(Order,delivery.order_id)
    if delivery.status!='unassigned' or order.status!='ready': flash('Only ready, unassigned deliveries can be dispatched.','danger'); return redirect(url_for('marketplace.admin_dashboard'))
    delivery.rider_user_id=rider_id; delivery.status='assigned'
    order.status='assigned'
    _audit('delivery.assigned','delivery',delivery.public_id,{'rider_user_id':rider_id})
    db.session.commit(); flash('Delivery assigned.','success'); return redirect(url_for('marketplace.admin_dashboard'))

@bp.get('/finance')
@role_required('super_admin','finance_operator')
def finance_dashboard():
    from app.models.commerce import Payment
    payments=db.session.scalars(select(Payment).order_by(Payment.created_at.desc()).limit(100)).all()
    totals={'pending':db.session.scalar(select(func.coalesce(func.sum(Payment.amount_ugx),0)).where(Payment.status=='pending')) or 0,'succeeded':db.session.scalar(select(func.coalesce(func.sum(Payment.amount_ugx),0)).where(Payment.status=='succeeded')) or 0,'refunded':db.session.scalar(select(func.coalesce(func.sum(Payment.amount_ugx),0)).where(Payment.status=='refunded')) or 0}
    return render_template('marketplace/finance.html',payments=payments,totals=totals)

@bp.get('/vendor/promotions')
@role_required('vendor_owner','vendor_staff')
def vendor_promotions():
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    if not vendor: abort(403)
    promotions=db.session.scalars(select(Promotion).where(Promotion.vendor_id==vendor.id).order_by(Promotion.created_at.desc())).all()
    return render_template('marketplace/promotions.html',vendor=vendor,promotions=promotions)

@bp.route('/vendor/promotions/new', methods=['GET','POST'])
@role_required('vendor_owner','vendor_staff')
def vendor_promotion_new():
    vendor=db.session.scalar(select(VendorProfile).where(VendorProfile.owner_user_id==current_user.id))
    if not vendor or vendor.status!='approved': abort(403)
    if request.method=='POST':
        title=request.form.get('title','').strip()[:140]; description=request.form.get('description','').strip()[:2000]
        try: budget=int(request.form.get('budget_ugx','0'))
        except ValueError: budget=-1
        if not title or budget<0: flash('Enter a title and valid budget.','danger')
        else:
            promo=Promotion(vendor_id=vendor.id,title=title,description=description,budget_ugx=budget,is_active=False); db.session.add(promo); _audit('promotion.created','promotion',promo.public_id,{'budget_ugx':budget}); db.session.commit(); flash('Promotion draft saved. It is not live until approved and scheduled.','success'); return redirect(url_for('marketplace.vendor_promotions'))
    return render_template('marketplace/promotion_form.html')

@bp.post('/admin/support/<uuid:public_id>/status')
@role_required('super_admin','operations_manager','support_agent')
def admin_support_status(public_id):
    ticket=db.session.scalar(select(SupportTicket).where(SupportTicket.public_id==public_id))
    if not ticket: abort(404)
    status=request.form.get('status','')
    if status not in {'open','in_progress','resolved','closed'}: abort(400)
    before=ticket.status; ticket.status=status; _audit('support.ticket_status_changed','support_ticket',ticket.public_id,{'before':before,'status':status}); db.session.commit(); flash('Support ticket updated.','success'); return redirect(url_for('marketplace.admin_dashboard'))
