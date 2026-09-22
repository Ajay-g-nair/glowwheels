import urllib.parse
from config import Config

class WhatsAppService:
    @staticmethod
    def clean_phone(phone: str) -> str:
        """Strip spaces, dashes, plus signs for WhatsApp link format."""
        if not phone:
            return ""
        digits = "".join([c for c in phone if c.isdigit()])
        # Default to 91 (India) prefix if 10 digits provided
        if len(digits) == 10:
            digits = "91" + digits
        return digits

    @staticmethod
    def create_whatsapp_url(phone: str, text: str) -> str:
        """Generates a direct universal wa.me link for WhatsApp Web or Mobile."""
        cleaned_phone = WhatsAppService.clean_phone(phone)
        encoded_text = urllib.parse.quote(text)
        if cleaned_phone:
            return f"https://wa.me/{cleaned_phone}?text={encoded_text}"
        return f"https://wa.me/?text={encoded_text}"

    @classmethod
    def get_new_booking_admin_message(cls, booking) -> dict:
        """Message sent to Admin when a new booking is made by a customer."""
        maps_link = booking.get_maps_url() or "Location shared manually"
        msg = (
            f"🚗 *NEW WORK BOOKED - {Config.BRAND_NAME}* 🚗\n\n"
            f"📋 *Booking Ref:* #{booking.booking_number}\n"
            f"✨ *Package:* {booking.package.name} (₹{booking.package.price:,.0f})\n"
            f"📅 *Date:* {booking.booking_date}\n"
            f"⏰ *Time Slot:* {booking.time_slot}\n"
            f"👤 *Customer:* {booking.customer_name}\n"
            f"📞 *Customer Phone:* {booking.customer_phone}\n"
            f"🚘 *Vehicle:* {booking.car_model} ({booking.car_number or 'N/A'})\n"
            f"📍 *GPS Location:* {maps_link}\n"
            f"🏠 *Address/Notes:* {booking.address or booking.landmark or 'Doorstep'}\n\n"
            f"👉 Open Admin Dashboard to Confirm & Assign Workers!"
        )
        url = cls.create_whatsapp_url(Config.ADMIN_PHONE, msg)
        return {"text": msg, "url": url, "recipient": Config.ADMIN_PHONE}

    @classmethod
    def get_booking_confirmed_message(cls, booking) -> dict:
        """Message sent to Customer when Admin confirms their booking."""
        msg = (
            f"✅ *BOOKING CONFIRMED - {Config.BRAND_NAME}* ✅\n\n"
            f"Hello *{booking.customer_name}*!\n"
            f"Your doorstep car wash booking #{booking.booking_number} is officially *CONFIRMED*! 🎉\n\n"
            f"✨ *Package:* {booking.package.name}\n"
            f"📅 *Scheduled Date:* {booking.booking_date}\n"
            f"⏰ *Time Slot:* {booking.time_slot}\n"
            f"🚘 *Vehicle:* {booking.car_model}\n\n"
            f"Our fully equipped mobile wash van and detailing specialists will arrive at your location on time.\n"
            f"Thank you for choosing {Config.BRAND_NAME}!"
        )
        url = cls.create_whatsapp_url(booking.customer_phone, msg)
        return {"text": msg, "url": url, "recipient": booking.customer_phone}

    @classmethod
    def get_booking_extended_message(cls, booking, new_date=None, new_slot=None, notes=None) -> dict:
        """Message sent to Customer when booking is extended or rescheduled."""
        date_str = new_date or booking.booking_date
        slot_str = new_slot or booking.time_slot
        notes_str = f"\n📝 *Update Notes:* {notes}" if notes else ""

        msg = (
            f"⏳ *BOOKING SCHEDULE UPDATE - {Config.BRAND_NAME}* ⏳\n\n"
            f"Hello *{booking.customer_name}*,\n"
            f"Your booking #{booking.booking_number} has been updated/extended to a new slot:\n\n"
            f"✨ *Package:* {booking.package.name}\n"
            f"📅 *New Date:* {date_str}\n"
            f"⏰ *New Time Slot:* {slot_str}{notes_str}\n\n"
            f"We appreciate your understanding and look forward to making your vehicle shine like new!\n"
            f"For questions, reply to this message directly."
        )
        url = cls.create_whatsapp_url(booking.customer_phone, msg)
        return {"text": msg, "url": url, "recipient": booking.customer_phone}

