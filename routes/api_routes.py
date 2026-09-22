from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Booking
from config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')

STANDARD_SLOTS = [
    "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM",
    "11:00 AM - 12:00 PM",
    "12:00 PM - 01:00 PM",
    "01:00 PM - 02:00 PM",
    "02:00 PM - 03:00 PM",
    "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM",
    "05:00 PM - 06:00 PM"
]

@api_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter is required (YYYY-MM-DD)'}), 400

    # Retrieve all active bookings for this date
    # Statuses that block the slot: pending, confirmed, committed, in_progress
    active_bookings = Booking.query.filter(
        Booking.booking_date == date_str,
        Booking.status.in_(['pending', 'confirmed', 'committed', 'in_progress'])
    ).all()

    booked_slots = set()
    for b in active_bookings:
        booked_slots.add(b.time_slot.strip())

    slots_data = []
    for slot in STANDARD_SLOTS:
        is_booked = slot in booked_slots
        slots_data.append({
            'slot': slot,
            'available': not is_booked,
            'status_label': 'Booked (Unavailable)' if is_booked else 'Available'
        })

    return jsonify({
        'date': date_str,
        'slots': slots_data,
        'total_slots': len(STANDARD_SLOTS),
        'available_count': sum(1 for s in slots_data if s['available']),
        'booked_count': len(booked_slots)
    })

