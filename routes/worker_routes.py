from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import Booking, Product, MachineDamageReport, LeaveRequest, OvertimeLog, User, Package
from routes.auth_routes import worker_required

worker_bp = Blueprint('worker', __name__, url_prefix='/worker')

@worker_bp.route('/dashboard', methods=['GET', 'POST'])
@worker_required
def dashboard():
    worker_id = session['user_id']

    # Fallback if damage report is submitted to /dashboard
    if request.method == 'POST':
        machine_name = request.form.get('machine_name', '').strip()
        damage_desc = request.form.get('damage_description', '').strip()
        severity = request.form.get('severity', 'moderate')
        if machine_name and damage_desc:
            report = MachineDamageReport(
                worker_id=worker_id,
                machine_name=machine_name,
                issue_description=damage_desc,
                severity=severity
            )
            db.session.add(report)
            db.session.commit()
            flash(f'Machine issue for "{machine_name}" reported successfully to Admin!', 'success')
            return redirect(url_for('worker.dashboard'))

    worker = User.query.get(worker_id)

    # Jobs that need a worker
    available_jobs = Booking.query.filter(
        Booking.worker_id == None,
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.booking_date.asc()).all()

    # Active jobs assigned to this worker
    active_jobs = Booking.query.filter(
        Booking.worker_id == worker_id,
        Booking.status.in_(['committed', 'in_progress'])
    ).order_by(Booking.booking_date.asc()).all()

    # Completed jobs count
    completed_jobs = Booking.query.filter_by(worker_id=worker_id, status='finished').all()
    finished_count = len(completed_jobs)
    total_serviced_amount = sum(b.payment_amount or 0 for b in completed_jobs)

    # All packages/services for quick look-up
    packages = Package.query.order_by(Package.price.asc()).all()

    # Active inventory products list for the finish modal
    inventory_products = Product.query.filter_by(is_finished=False).all()
    all_products = Product.query.order_by(Product.name.asc()).all()

    return render_template(
        'worker/dashboard.html',
        worker=worker,
        available_jobs=available_jobs,
        active_jobs=active_jobs,
        finished_count=finished_count,
        total_serviced_amount=total_serviced_amount,
        inventory_products=inventory_products,
        all_products=all_products,
        packages=packages
    )

@worker_bp.route('/report-damage', methods=['POST'])
@worker_required
def report_damage():
    worker_id = session['user_id']
    machine_name = request.form.get('machine_name', '').strip()
    damage_desc = request.form.get('damage_description', '').strip()
    severity = request.form.get('severity', 'moderate')
    booking_id = request.form.get('booking_id', type=int)

    if not machine_name or not damage_desc:
        flash('Machine name and damage description are required.', 'danger')
        return redirect(url_for('worker.dashboard'))

    report = MachineDamageReport(
        worker_id=worker_id,
        booking_id=booking_id,
        machine_name=machine_name,
        issue_description=damage_desc,
        severity=severity
    )
    db.session.add(report)
    db.session.commit()

    flash(f'Machine issue for "{machine_name}" reported! Admin alerted for repair.', 'success')
    return redirect(url_for('worker.dashboard'))

@worker_bp.route('/report-product-finished', methods=['POST'])
@worker_required
def report_product_finished():
    product_id = request.form.get('product_id', type=int)
    if product_id:
        prod = Product.query.get(product_id)
        if prod:
            prod.is_finished = True
            prod.stock_quantity = 0
            db.session.commit()
            flash(f'Product "{prod.name}" flagged as Finished/Depleted! Admin notified to restock.', 'warning')
            return redirect(url_for('worker.dashboard'))
    flash('Please select a valid product.', 'danger')
    return redirect(url_for('worker.dashboard'))

@worker_bp.route('/commit/<int:booking_id>', methods=['POST'])
@worker_required
def commit_work(booking_id):
    worker_id = session['user_id']
    booking = Booking.query.get_or_404(booking_id)

    if booking.worker_id and booking.worker_id != worker_id:
        flash('This job was already committed by another worker.', 'warning')
        return redirect(url_for('worker.dashboard'))

    booking.worker_id = worker_id
    booking.status = 'committed'
    db.session.commit()

    flash(f'Success! You have committed to booking #{booking.booking_number}.', 'success')
    return redirect(url_for('worker.dashboard'))

@worker_bp.route('/start/<int:booking_id>', methods=['POST'])
@worker_required
def start_work(booking_id):
    worker_id = session['user_id']
    booking = Booking.query.get_or_404(booking_id)

    if booking.worker_id != worker_id:
        flash('You can only start jobs you committed to.', 'danger')
        return redirect(url_for('worker.dashboard'))

    booking.status = 'in_progress'
    db.session.commit()
    flash(f'Car wash started for #{booking.booking_number}!', 'info')
    return redirect(url_for('worker.dashboard'))

@worker_bp.route('/finish/<int:booking_id>', methods=['POST'])
@worker_required
def finish_work(booking_id):
    worker_id = session['user_id']
    booking = Booking.query.get_or_404(booking_id)

    if booking.worker_id != worker_id:
        flash('Unauthorized action for this booking.', 'danger')
        return redirect(url_for('worker.dashboard'))

    # Payment details
    payment_mode = request.form.get('payment_mode', 'Cash').strip()
    payment_amount = request.form.get('payment_amount', type=float, default=booking.payment_amount or booking.package.price)

    booking.status = 'finished'
    booking.payment_mode = payment_mode
    booking.payment_amount = payment_amount
    booking.payment_status = 'paid'
    booking.finished_at = datetime.utcnow()

    # Record finished/depleted products
    finished_product_ids = request.form.getlist('finished_products')
    for pid in finished_product_ids:
        try:
            prod = Product.query.get(int(pid))
            if prod:
                prod.is_finished = True
                prod.stock_quantity = 0
        except ValueError:
            pass

    # Record damaged machine / equipment if reported
    has_damage = request.form.get('has_damage') == 'on'
    if has_damage:
        machine_name = request.form.get('machine_name', '').strip()
        damage_desc = request.form.get('damage_description', '').strip()
        severity = request.form.get('severity', 'moderate')

        if machine_name and damage_desc:
            report = MachineDamageReport(
                worker_id=worker_id,
                booking_id=booking.id,
                machine_name=machine_name,
                issue_description=damage_desc,
                severity=severity
            )
            db.session.add(report)

    db.session.commit()

    flash(f'Great work! Booking #{booking.booking_number} marked as Finished and Payment recorded ({payment_mode}: ₹{payment_amount:,.0f}).', 'success')
    return redirect(url_for('worker.dashboard'))

@worker_bp.route('/history')
@worker_required
def history():
    worker_id = session['user_id']
    history_jobs = Booking.query.filter_by(worker_id=worker_id, status='finished').order_by(Booking.finished_at.desc()).all()
    total_earned = sum(b.payment_amount or 0 for b in history_jobs)
    return render_template('worker/history.html', history_jobs=history_jobs, total_earned=total_earned)

@worker_bp.route('/leave', methods=['GET', 'POST'])
@worker_required
def leave():
    worker_id = session['user_id']
    if request.method == 'POST':
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        reason = request.form.get('reason', '').strip()

        if not start_date or not end_date or not reason:
            flash('All fields are required to apply for leave.', 'danger')
            return redirect(url_for('worker.leave'))

        lr = LeaveRequest(
            worker_id=worker_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        db.session.add(lr)
        db.session.commit()
        flash('Leave application submitted to Admin for approval.', 'success')
        return redirect(url_for('worker.leave'))

    leaves = LeaveRequest.query.filter_by(worker_id=worker_id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('worker/leave.html', leaves=leaves)

@worker_bp.route('/overtime', methods=['GET', 'POST'])
@worker_required
def overtime():
    worker_id = session['user_id']
    if request.method == 'POST':
        work_date = request.form.get('work_date', '').strip()
        hours = request.form.get('hours', type=float)
        reason = request.form.get('reason', '').strip()

        if not work_date or not hours or not reason:
            flash('Date, hours and reason are required.', 'danger')
            return redirect(url_for('worker.overtime'))

        ot = OvertimeLog(
            worker_id=worker_id,
            work_date=work_date,
            hours=hours,
            reason=reason
        )
        db.session.add(ot)
        db.session.commit()
        flash(f'Logged {hours} hours overtime for {work_date}.', 'success')
        return redirect(url_for('worker.overtime'))

    logs = OvertimeLog.query.filter_by(worker_id=worker_id).order_by(OvertimeLog.logged_at.desc()).all()
    total_ot_hours = sum(l.hours for l in logs)
    return render_template('worker/overtime.html', logs=logs, total_ot_hours=total_ot_hours)
