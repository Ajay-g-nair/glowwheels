import random
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import Package, Booking, User
from services.whatsapp_service import WhatsAppService
from routes.auth_routes import login_required
from routes.api_routes import STANDARD_SLOTS
from config import Config

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    packages = Package.query.filter_by(is_active=True).all()
    return render_template('index.html', packages=packages, config=Config)

@user_bp.route('/packages')
@user_bp.route('/services')
def packages_catalog():
    packages = Package.query.filter_by(is_active=True).all()
    return render_template('user/packages.html', packages=packages)

@user_bp.route('/book', methods=['GET', 'POST'])
def book():
    if 'user_id' not in session:
        flash('Please login or register to book your mobile car wash.', 'info')
        return redirect(url_for('auth.login', next=url_for('user.book', package_id=request.args.get('package_id'))))

    current_user = User.query.get(session['user_id'])
    packages = Package.query.filter_by(is_active=True).all()
    selected_package_id = request.args.get('package_id', type=int)

    # Today's date string YYYY-MM-DD
    today_str = date.today().isoformat()

    if request.method == 'POST':
        package_id = request.form.get('package_id', type=int)
        booking_date = request.form.get('booking_date', '').strip()
        time_slot = request.form.get('time_slot', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        car_model = request.form.get('car_model', '').strip()
        car_number = request.form.get('car_number', '').strip()
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        address = request.form.get('address', '').strip()
        landmark = request.form.get('landmark', '').strip()

        # Validation
        if not package_id or not booking_date or not time_slot or not customer_phone or not car_model:
            flash('Please fill in all mandatory booking fields.', 'danger')
            return redirect(url_for('user.book', package_id=package_id))

        # Check if the chosen time slot is already booked
        existing_conflict = Booking.query.filter(
            Booking.booking_date == booking_date,
            Booking.time_slot == time_slot,
            Booking.status.in_(['pending', 'confirmed', 'committed', 'in_progress'])
        ).first()

        if existing_conflict:
            flash(f'Slot {time_slot} on {booking_date} has already been reserved! Please pick another slot.', 'warning')
            return redirect(url_for('user.book', package_id=package_id))

        # Create unique booking reference number
        ref_date = datetime.now().strftime('%Y%m%d')
        ref_rand = random.randint(1000, 9999)
        booking_number = f"GW-{ref_date}-{ref_rand}"

        package = Package.query.get_or_404(package_id)

        new_booking = Booking(
            booking_number=booking_number,
            user_id=current_user.id,
            package_id=package.id,
            booking_date=booking_date,
            time_slot=time_slot,
            customer_name=customer_name or current_user.full_name or current_user.username,
            customer_phone=customer_phone,
            car_model=car_model,
            car_number=car_number,
            latitude=latitude,
            longitude=longitude,
            address=address,
            landmark=landmark,
            status='pending',
            payment_amount=package.price,
            payment_status='pending'
        )

        db.session.add(new_booking)
        db.session.commit()

        flash('Booking placed successfully! Your slot has been reserved.', 'success')
        return redirect(url_for('user.booking_success', booking_id=new_booking.id))

    return render_template(
        'user/book.html',
        packages=packages,
        selected_package_id=selected_package_id,
        current_user=current_user,
        standard_slots=STANDARD_SLOTS,
        today_str=today_str,
        config=Config
    )

@user_bp.route('/booking-success/<int:booking_id>')
@login_required
def booking_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Generate the Admin WhatsApp message with Google Maps location and booking details
    whatsapp_data = WhatsAppService.get_new_booking_admin_message(booking)
    return render_template('user/booking_success.html', booking=booking, whatsapp=whatsapp_data, config=Config)

@user_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.created_at.desc()).all()
    return render_template('user/my_bookings.html', bookings=bookings)

