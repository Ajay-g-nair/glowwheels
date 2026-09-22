from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') # 'user', 'worker', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='customer', foreign_keys='Booking.user_id', lazy=True)
    assigned_works = db.relationship('Booking', backref='worker', foreign_keys='Booking.worker_id', lazy=True)
    leave_requests = db.relationship('LeaveRequest', backref='worker', lazy=True)
    overtime_logs = db.relationship('OvertimeLog', backref='worker', lazy=True)
    damage_reports = db.relationship('MachineDamageReport', backref='worker', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name or self.username,
            'phone': self.phone,
            'role': self.role
        }


class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_mins = db.Column(db.Integer, default=60)
    description = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text, nullable=True) # Semicolon-separated features list
    badge = db.Column(db.String(50), nullable=True)
    icon = db.Column(db.String(50), default='car')
    is_active = db.Column(db.Boolean, default=True)

    bookings = db.relationship('Booking', backref='package', lazy=True)

    def get_features_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.split(';') if f.strip()]


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    
    booking_date = db.Column(db.String(20), nullable=False) # 'YYYY-MM-DD'
    time_slot = db.Column(db.String(30), nullable=False)    # e.g., '10:00 AM'
    
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(25), nullable=False)
    car_model = db.Column(db.String(100), nullable=False)
    car_number = db.Column(db.String(40), nullable=True)
    
    # WhatsApp-style GPS Location
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.Text, nullable=True)
    landmark = db.Column(db.String(150), nullable=True)
    
    # Status lifecycle: 'pending' -> 'confirmed' -> 'committed' -> 'in_progress' -> 'finished' (or 'rescheduled' / 'cancelled')
    status = db.Column(db.String(25), default='pending')
    
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Financials & Payment Collection (Done by worker / admin)
    payment_mode = db.Column(db.String(30), nullable=True) # 'Google Pay', 'Cash', 'PhonePe', 'UPI', 'Card'
    payment_amount = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='pending') # 'pending', 'paid'
    
    # Reschedule & Extension tracking
    extension_notes = db.Column(db.Text, nullable=True)
    rescheduled_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    def get_maps_url(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return ""


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='Chemicals')
    stock_quantity = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(20), default='bottles')
    low_threshold = db.Column(db.Integer, default=2)
    is_finished = db.Column(db.Boolean, default=False)
    last_restocked = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_threshold and not self.is_finished


class MachineDamageReport(db.Model):
    __tablename__ = 'machine_damage_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    machine_name = db.Column(db.String(100), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='moderate') # 'minor', 'moderate', 'severe'
    is_repaired = db.Column(db.Boolean, default=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OvertimeLog(db.Model):
    __tablename__ = 'overtime_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    work_date = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

