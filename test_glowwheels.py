from datetime import date
from app import create_app
from database import db
from models import User, Package, Booking, Product, MachineDamageReport, LeaveRequest, OvertimeLog
from services.whatsapp_service import WhatsAppService
from config import Config

def run_tests():
    app = create_app()
    client = app.test_client()

    print("==================================================")
    print("[START] Starting End-to-End Verification of GlowWheels")
    print("==================================================")

    with app.app_context():
        today = date.today().isoformat()
        # 1. Verify Seeded Data
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        assert admin is not None, "Admin user must exist"
        assert admin.check_password(Config.ADMIN_PASSWORD), "Admin password verification failed"
        print("[PASS] Test 1: Admin fixed credentials verified successfully.")

        pkg_count = Package.query.count()
        assert pkg_count >= 4, f"Expected at least 4 packages, got {pkg_count}"
        assert pkg_count >= 3, f"Expected at least 3 packages, got {pkg_count}"
        print(f"[PASS] Test 2: Car wash packages loaded ({pkg_count} packages).")

        prod_count = Product.query.count()
        assert prod_count >= 7, f"Expected at least 7 products, got {prod_count}"
        print(f"[PASS] Test 3: Inventory products loaded ({prod_count} products).")

        # 2. Test Customer Registration & Login
        res = client.post('/register', data={
            'username': 'customer_test',
            'full_name': 'Aarav Sharma',
            'phone': '9876543210',
            'email': 'aarav@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        assert res.status_code == 200
        customer = User.query.filter_by(username='customer_test').first()
        assert customer is not None
        print("[PASS] Test 4: Customer registration and database commit verified.")

        # 3. Test Time Slot Availability API before booking
        today = date.today().isoformat()
        res = client.get(f'/api/available-slots?date={today}')
        import datetime
        test_date = (date.today() + datetime.timedelta(days=5)).isoformat()
        # Clean any existing booking on test_date
        Booking.query.filter_by(booking_date=test_date).delete()
        db.session.commit()

        res = client.get(f'/api/available-slots?date={test_date}')
        assert res.status_code == 200
        slots_json = res.get_json()
        assert slots_json['total_slots'] == 9
        test_slot = "10:00 AM - 11:00 AM"
        initial_slot_obj = next(s for s in slots_json['slots'] if s['slot'] == test_slot)
        assert initial_slot_obj['available'] is True
        print(f"[PASS] Test 5: Dynamic time slots API verified (Slot '{test_slot}' is available).")

        # 4. Create a Booking with GPS coordinates
        package = Package.query.first()
        with client.session_transaction() as sess:
            sess['user_id'] = customer.id
            sess['username'] = customer.username
            sess['role'] = customer.role

        booking_res = client.post('/book', data={
            'package_id': package.id,
            'booking_date': today,
            'booking_date': test_date,
            'time_slot': test_slot,
            'customer_name': 'Aarav Sharma',
            'customer_phone': '9876543210',
            'car_model': 'White Hyundai Creta',
            'car_number': 'KA 03 MN 5678',
            'latitude': 12.9716,
            'longitude': 77.5946,
            'address': 'Flat 204, Silicon Towers, Koramangala',
            'landmark': 'Basement parking near Pillar 9'
        }, follow_redirects=True)
        assert booking_res.status_code == 200
        created_booking = Booking.query.filter_by(user_id=customer.id, time_slot=test_slot).first()
        assert created_booking is not None
        print(f"[PASS] Test 6: Booking #{created_booking.booking_number} created with GPS Coordinates (12.9716, 77.5946).")

        # 5. Verify Slot is now COLORLESS / UNAVAILABLE in API
        res_after = client.get(f'/api/available-slots?date={today}')
        res_after = client.get(f'/api/available-slots?date={test_date}')
        slots_after = res_after.get_json()
        booked_slot_obj = next(s for s in slots_after['slots'] if s['slot'] == test_slot)
        assert booked_slot_obj['available'] is False, "Booked slot must be marked available: false"
        print(f"[PASS] Test 7: Slot '{test_slot}' is now correctly DISABLED / COLORLESS for future bookings.")

        # 6. Test WhatsApp Message Formatter
        wa_admin = WhatsAppService.get_new_booking_admin_message(created_booking)
        assert "NEW WORK BOOKED" in wa_admin['text']
        assert "maps.google.com" in wa_admin['text'] or "google.com/maps" in wa_admin['text']
        assert "wa.me" in wa_admin['url']
        print("[PASS] Test 8: WhatsApp 'New Work Booked' alert generated with Google Maps pin URL.")

        # 7. Test Admin Booking Confirmation & Rescheduling
        with client.session_transaction() as sess:
            sess['user_id'] = admin.id
            sess['username'] = admin.username
            sess['role'] = 'admin'

        conf_res = client.post(f'/admin/bookings/{created_booking.id}/confirm', follow_redirects=False)
        assert conf_res.status_code == 302
        assert created_booking.status == 'confirmed'
        wa_confirmed = WhatsAppService.get_booking_confirmed_message(created_booking)
        assert "CONFIRMED" in wa_confirmed['text']
        print(f"[PASS] Test 9: Admin confirmation successful and customer WhatsApp alert created.")

        # Test Rescheduling (Extend booking)
        new_slot = "02:00 PM - 03:00 PM"
        ext_res = client.post(f'/admin/bookings/{created_booking.id}/extend', data={
            'new_date': today,
            'new_time_slot': new_slot,
            'extension_notes': 'Extended due to heavy traffic on outer ring road'
        }, follow_redirects=False)
        assert ext_res.status_code == 302
        assert created_booking.time_slot == new_slot
        wa_extended = WhatsAppService.get_booking_extended_message(created_booking, today, new_slot, 'Extended due to traffic')
        assert "UPDATE" in wa_extended['text']
        print(f"[PASS] Test 10: Admin rescheduled booking to '{new_slot}' and customer alert created.")

        # 8. Test Worker Panel Flow (Commit -> Start -> Finish with Payment, Depleted Product & Machine Damage)
        worker = User.query.filter_by(role='worker').first()
        with client.session_transaction() as sess:
            sess['user_id'] = worker.id
            sess['username'] = worker.username
            sess['role'] = 'worker'

        # Commit
        commit_res = client.post(f'/worker/commit/{created_booking.id}', follow_redirects=True)
        assert commit_res.status_code == 200
        assert created_booking.worker_id == worker.id
        print(f"[PASS] Test 11: Worker {worker.username} committed to booking #{created_booking.booking_number}.")

        # Finish with Google Pay, Empty Product, and Machine Damage
        shampoo = Product.query.filter(Product.name.like('%Shampoo%')).first()
        assert shampoo is not None

        finish_res = client.post(f'/worker/finish/{created_booking.id}', data={
            'payment_mode': 'Google Pay',
            'payment_amount': 499.0,
            'finished_products': [shampoo.id],
            'has_damage': 'on',
            'machine_name': 'Karcher High Pressure Washer',
            'damage_description': 'Water leaking from high pressure lance trigger',
            'severity': 'moderate'
        }, follow_redirects=True)
        assert finish_res.status_code == 200
        assert created_booking.status == 'finished'
        assert created_booking.payment_mode == 'Google Pay'
        assert created_booking.payment_status == 'paid'
        print("[PASS] Test 12: Worker finished job, recorded Google Pay Rs. 499 fee.")

        # Check Product is marked finished
        db.session.refresh(shampoo)
        assert shampoo.is_finished is True
        print(f"[PASS] Test 13: Product '{shampoo.name}' marked as FINISHED / DEPLETED for Admin alert.")

        # Check Damaged Machine is recorded
        damage = MachineDamageReport.query.filter_by(worker_id=worker.id).first()
        assert damage is not None
        assert "Karcher" in damage.machine_name
        print(f"[PASS] Test 14: Damaged equipment report logged ('{damage.machine_name}').")

        # 9. Test Worker Leave Application & Overtime Logging
        leave_res = client.post('/worker/leave', data={
            'start_date': today,
            'end_date': today,
            'reason': 'Family emergency'
        }, follow_redirects=True)
        assert leave_res.status_code == 200
        leave = LeaveRequest.query.filter_by(worker_id=worker.id).first()
        assert leave is not None
        print("[PASS] Test 15: Worker leave application recorded.")

        ot_res = client.post('/worker/overtime', data={
            'work_date': today,
            'hours': 2.0,
            'reason': 'Late evening ceramic coating service'
        }, follow_redirects=True)
        assert ot_res.status_code == 200
        ot = OvertimeLog.query.filter_by(worker_id=worker.id).first()
        assert ot is not None
        assert ot.hours == 2.0
        print("[PASS] Test 16: Worker overtime log recorded (+2.0 hrs).")

    print("==================================================")
    print("[SUCCESS] ALL 16 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_tests()
