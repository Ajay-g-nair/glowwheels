from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import Booking, Product, MachineDamageReport, LeaveRequest, OvertimeLog, User, Package
from services.whatsapp_service import WhatsAppService
from routes.auth_routes import admin_required
from routes.api_routes import STANDARD_SLOTS
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Metrics
    total_works = Booking.query.count()
    pending_works = Booking.query.filter_by(status='pending').count()
    confirmed_works = Booking.query.filter_by(status='confirmed').count()
    in_progress_works = Booking.query.filter(Booking.status.in_(['committed', 'in_progress'])).count()
    finished_works = Booking.query.filter_by(status='finished').count()
    
    # Financial metrics
    paid_bookings = Booking.query.filter_by(payment_status='paid').all()
    total_income = sum(b.payment_amount or 0 for b in paid_bookings)
    gpay_income = sum(b.payment_amount or 0 for b in paid_bookings if b.payment_mode in ['Google Pay', 'UPI', 'PhonePe'])
    cash_income = sum(b.payment_amount or 0 for b in paid_bookings if b.payment_mode == 'Cash')

    # Inventory and Machine alerts
    finished_products = Product.query.filter((Product.is_finished == True) | (Product.stock_quantity <= Product.low_threshold)).all()
    unresolved_damages = MachineDamageReport.query.filter_by(is_repaired=False).order_by(MachineDamageReport.reported_at.desc()).all()
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()

    # Filter bookings by query parameter
    status_filter = request.args.get('status', 'all')
    if status_filter != 'all':
        bookings = Booking.query.filter_by(status=status_filter).order_by(Booking.created_at.desc()).all()
    else:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()

    workers = User.query.filter_by(role='worker').all()
    packages = Package.query.order_by(Package.price.asc()).all()

    return render_template(
        'admin/dashboard.html',
        total_works=total_works,
        pending_works=pending_works,
        confirmed_works=confirmed_works,
        in_progress_works=in_progress_works,
        finished_works=finished_works,
        total_income=total_income,
        gpay_income=gpay_income,
        cash_income=cash_income,
        finished_products=finished_products,
        unresolved_damages=unresolved_damages,
        pending_leaves=pending_leaves,
        bookings=bookings,
        status_filter=status_filter,
        workers=workers,
        packages=packages,
        standard_slots=STANDARD_SLOTS,
        config=Config
    )

@admin_bp.route('/services')
@admin_required
def services():
    packages = Package.query.order_by(Package.price.asc()).all()
    return render_template('admin/services.html', packages=packages, config=Config)

@admin_bp.route('/services/add', methods=['POST'])
@admin_required
def add_service():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', type=float)
    duration_mins = request.form.get('duration_mins', type=int, default=45)
    badge = request.form.get('badge', '').strip()
    icon = request.form.get('icon', 'sparkles').strip()
    description = request.form.get('description', '').strip()
    features = request.form.get('features', '').strip()

    if not name or not price:
        flash('Service name and price are required.', 'danger')
        return redirect(url_for('admin.dashboard'))

    pkg = Package(
        name=name,
        price=price,
        duration_mins=duration_mins,
        badge=badge or None,
        icon=icon,
        description=description,
        features=features
    )
    db.session.add(pkg)
    db.session.commit()
    flash(f'New service "{name}" (₹{price:,.0f}) added successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/services/<int:package_id>/edit', methods=['POST'])
@admin_required
def edit_service(package_id):
    pkg = Package.query.get_or_404(package_id)
    name = request.form.get('name', '').strip()
    price = request.form.get('price', type=float)
    duration_mins = request.form.get('duration_mins', type=int)
    badge = request.form.get('badge', '').strip()
    icon = request.form.get('icon', '').strip()
    description = request.form.get('description', '').strip()
    features = request.form.get('features', '').strip()

    if name:
        pkg.name = name
    if price is not None:
        pkg.price = price
    if duration_mins is not None:
        pkg.duration_mins = duration_mins
    pkg.badge = badge or None
    if icon:
        pkg.icon = icon
    if description:
        pkg.description = description
    if features:
        pkg.features = features

    db.session.commit()
    flash(f'Service "{pkg.name}" details updated successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/services/<int:package_id>/delete', methods=['POST'])
@admin_required
def delete_service(package_id):
    pkg = Package.query.get_or_404(package_id)
    bookings_count = Booking.query.filter_by(package_id=pkg.id).count()
    if bookings_count > 0:
        flash(f'Cannot delete "{pkg.name}" because {bookings_count} active/past bookings use it.', 'warning')
        return redirect(url_for('admin.dashboard'))

    db.session.delete(pkg)
    db.session.commit()
    flash(f'Service "{pkg.name}" deleted.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/bookings/<int:booking_id>')
@admin_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    workers = User.query.filter_by(role='worker').all()
    
    # Pre-generate WhatsApp messages for immediate dispatch
    wa_confirm = WhatsAppService.get_booking_confirmed_message(booking)
    wa_reschedule = WhatsAppService.get_booking_extended_message(booking)

    return render_template(
        'admin/booking_detail.html',
        booking=booking,
        workers=workers,
        standard_slots=STANDARD_SLOTS,
        wa_confirm=wa_confirm,
        wa_reschedule=wa_reschedule,
        config=Config
    )

@admin_bp.route('/bookings/<int:booking_id>/confirm', methods=['POST'])
@admin_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'confirmed'
    db.session.commit()

    wa_data = WhatsAppService.get_booking_confirmed_message(booking)
    flash(f'Booking #{booking.booking_number} confirmed! WhatsApp notification link generated.', 'success')
    return redirect(url_for('admin.booking_detail', booking_id=booking.id, trigger_wa=wa_data['url']))

@admin_bp.route('/bookings/<int:booking_id>/extend', methods=['POST'])
@admin_required
def extend_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_date = request.form.get('new_date', '').strip()
    new_slot = request.form.get('new_time_slot', '').strip()
    notes = request.form.get('extension_notes', '').strip()

    if not new_date or not new_slot:
        flash('Please select both a new date and time slot.', 'danger')
        return redirect(url_for('admin.booking_detail', booking_id=booking.id))

    booking.booking_date = new_date
    booking.time_slot = new_slot
    booking.extension_notes = notes
    booking.rescheduled_at = datetime.utcnow()
    db.session.commit()

    wa_data = WhatsAppService.get_booking_extended_message(booking, new_date, new_slot, notes)
    flash(f'Booking schedule updated to {new_date} at {new_slot}. WhatsApp alert prepared.', 'success')
    return redirect(url_for('admin.booking_detail', booking_id=booking.id, trigger_wa=wa_data['url']))

@admin_bp.route('/bookings/<int:booking_id>/assign', methods=['POST'])
@admin_required
def assign_worker(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    worker_id = request.form.get('worker_id', type=int)

    if worker_id:
        worker = User.query.filter_by(id=worker_id, role='worker').first_or_404()
        booking.worker_id = worker.id
        if booking.status == 'pending':
            booking.status = 'confirmed'
        db.session.commit()
        flash(f'Assigned worker {worker.full_name or worker.username} to booking #{booking.booking_number}.', 'success')
    else:
        booking.worker_id = None
        db.session.commit()
        flash('Worker unassigned.', 'info')

    return redirect(url_for('admin.booking_detail', booking_id=booking.id))

@admin_bp.route('/inventory', methods=['GET', 'POST'])
@admin_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', 'Chemicals').strip()
        stock_quantity = request.form.get('stock_quantity', type=int, default=10)
        unit = request.form.get('unit', 'bottles').strip()
        low_threshold = request.form.get('low_threshold', type=int, default=2)

        if name:
            prod = Product(
                name=name,
                category=category,
                stock_quantity=stock_quantity,
                unit=unit,
                low_threshold=low_threshold,
                is_finished=(stock_quantity == 0)
            )
            db.session.add(prod)
            db.session.commit()
            flash(f'Product "{name}" added to inventory.', 'success')
            return redirect(url_for('admin.inventory'))

    products = Product.query.order_by(Product.is_finished.desc(), Product.stock_quantity.asc()).all()
    finished_count = Product.query.filter_by(is_finished=True).count()
    low_count = Product.query.filter(Product.stock_quantity <= Product.low_threshold, Product.is_finished == False).count()

    return render_template(
        'admin/inventory.html',
        products=products,
        finished_count=finished_count,
        low_count=low_count
    )

@admin_bp.route('/inventory/<int:product_id>/restock', methods=['POST'])
@admin_required
def restock_product(product_id):
    product = Product.query.get_or_404(product_id)
    add_qty = request.form.get('add_quantity', type=int, default=10)
    product.stock_quantity += add_qty
    if product.stock_quantity > 0:
        product.is_finished = False
    product.last_restocked = datetime.utcnow()
    db.session.commit()
    flash(f'Restocked {product.name} (+{add_qty} {product.unit}). Stock is now {product.stock_quantity}.', 'success')
    return redirect(url_for('admin.inventory'))

@admin_bp.route('/inventory/<int:product_id>/toggle-finished', methods=['POST'])
@admin_required
def toggle_finished_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_finished = not product.is_finished
    if product.is_finished:
        product.stock_quantity = 0
    db.session.commit()
    status_label = "FINISHED / DEPLETED" if product.is_finished else "AVAILABLE"
    flash(f'Product "{product.name}" marked as {status_label}.', 'info')
    return redirect(url_for('admin.inventory'))

@admin_bp.route('/workers')
@admin_required
def workers():
    all_workers = User.query.filter_by(role='worker').all()
    damage_reports = MachineDamageReport.query.order_by(MachineDamageReport.reported_at.desc()).all()
    leave_requests = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).all()
    overtime_logs = OvertimeLog.query.order_by(OvertimeLog.logged_at.desc()).all()

    return render_template(
        'admin/workers.html',
        workers=all_workers,
        damage_reports=damage_reports,
        leave_requests=leave_requests,
        overtime_logs=overtime_logs
    )

@admin_bp.route('/damage-reports/<int:report_id>/repair', methods=['POST'])
@admin_required
def resolve_damage_report(report_id):
    report = MachineDamageReport.query.get_or_404(report_id)
    report.is_repaired = not report.is_repaired
    db.session.commit()
    status = "Repaired / Resolved" if report.is_repaired else "Marked as Damaged"
    flash(f'Machine issue for "{report.machine_name}" marked as {status}.', 'success')
    return redirect(request.referrer or url_for('admin.workers'))

@admin_bp.route('/leaves/<int:leave_id>/<action>', methods=['POST'])
@admin_required
def review_leave(leave_id, action):
    leave = LeaveRequest.query.get_or_404(leave_id)
    if action in ['approve', 'reject']:
        leave.status = 'approved' if action == 'approve' else 'rejected'
        db.session.commit()
        flash(f'Leave request for {leave.worker.full_name or leave.worker.username} has been {leave.status}.', 'info')
    return redirect(url_for('admin.workers'))

@admin_bp.route('/finance')
@admin_required
def finance():
    paid_bookings = Booking.query.filter_by(payment_status='paid').order_by(Booking.finished_at.desc()).all()
    
    total_revenue = sum(b.payment_amount or 0 for b in paid_bookings)
    gpay_total = sum(b.payment_amount or 0 for b in paid_bookings if b.payment_mode in ['Google Pay', 'UPI', 'PhonePe'])
    cash_total = sum(b.payment_amount or 0 for b in paid_bookings if b.payment_mode == 'Cash')
    card_total = sum(b.payment_amount or 0 for b in paid_bookings if b.payment_mode == 'Card')

    return render_template(
        'admin/finance.html',
        paid_bookings=paid_bookings,
        total_revenue=total_revenue,
        gpay_total=gpay_total,
        cash_total=cash_total,
        card_total=card_total
    )
