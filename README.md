# ✨ GlowWheels - Doorstep Mobile Car Wash Platform

A full-stack, responsive mobile car wash web platform built with **Python (Flask)**, **Tailwind CSS**, and **SQLite / PostgreSQL**.

Designed with **3 dedicated panels** (Customer, Worker, Admin), an automated **WhatsApp notification system**, real-time **9 AM – 6 PM time slot scheduling with filled-slot disabling**, **WhatsApp-style GPS pin sharing**, **inventory alerts**, **equipment damage reports**, and **zero-lag deployment configuration**.

---

## 🌟 Key Features

### 🚗 1. Customer Panel
- **Wash Packages Showcase**: View packages (Quick Shine, Deep Interior, Full Glow Signature, Ceramic Ultra Spa) with pricing, duration, and feature checklists.
- **Dynamic 9 AM – 6 PM Slot Scheduler**:
  - Operating slots: `09:00 AM - 10:00 AM` to `05:00 PM - 06:00 PM`.
  - **Real-time Colorless Disabling**: Whenever a slot is booked on a date, it immediately appears **colorless, strikethrough, and disabled** with a "Booked" badge.
- **WhatsApp-Style GPS Location Sharing**:
  - One-tap `"📍 Use My Current Location"` button uses HTML5 browser GPS.
  - Interactive Leaflet map with draggable pin to pinpoint the exact parking spot.
  - Automatic reverse geocoding and landmark/parking notes (e.g. Basement B2, near Pillar 14).
- **Automated WhatsApp Alert**:
  - On booking, pre-formats and dispatches a WhatsApp alert to the Admin with the customer name, phone, car model, time slot, and clickable Google Maps link.
- **Live Booking Tracker**: Customers can track their wash status (`Pending`, `Confirmed`, `In Progress`, `Finished`, or `Rescheduled`).

### 🛡️ 2. Admin Panel (Fixed Access)
- **Fixed Credentials**: Preconfigured login (`admin` / `admin123`).
- **Master Command Dashboard**:
  - Real-time KPIs: Total Works, Pending Works, Confirmed Works, In Progress, Finished Works.
  - Revenue analytics: Total income with breakdown by **Google Pay / UPI**, **Cash**, and **Card**.
  - **Product Finished Alerts**: Visual red banner alerting when supplies (shampoo, wax, tire shine) are empty or below threshold.
  - **Machine Damage Alerts**: Real-time warning of damaged pressure washers, vacuums, or generators reported by workers.
- **Booking Management & WhatsApp Engine**:
  - View each booking's package, date/time, vehicle, and live Google Maps location.
  - **Confirm Booking**: Marks status as confirmed and triggers WhatsApp confirmation message to customer.
  - **Extend / Reschedule Booking**: Modal to reschedule to a new day or 9 AM–6 PM slot, triggering a WhatsApp alert informing the customer of the updated schedule.
  - **Assign Worker**: Assign any registered worker to the booking.
- **Supplies & Inventory Control**: Track stock counts, 1-click "Mark Finished" or "Restock".
- **Staff & HR Oversight**: Review equipment damage reports, approve/reject worker leave applications, and view overtime hours logged.

### 🔧 3. Worker Panel
- **Self-Registration & Login**: Workers can register their own accounts (`/worker/register`).
- **Available Works Board**: Real-time list of pending jobs waiting to be claimed. Workers can click **"Commit to Work"** to claim a job.
- **Active Job Workflow**:
  - Status updates: `"Start Wash"` -> `"Finish & Record Payment"`.
- **Finish Work Modal**:
  - Record collected fees: **Google Pay**, **Cash**, **PhonePe**, or **Card**.
  - Mark any **finished/depleted products** (notifies admin immediately).
  - Report any **damaged equipment/machines** (machine name, issue description, severity).
- **Worker History & HR Tools**:
  - View completed jobs history and total serviced earnings.
  - Submit leave requests (start date, end date, reason).
  - Log overtime hours worked.

---

## 🔑 Default Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Fixed admin access (configurable in `.env`) |
| **Sample Worker** | `worker1` | `worker123` | Can also register new workers at `/worker/register` |
| **Customer** | *(Self-register)* | *(Your password)* | Register at `/register` |

---

## 🚀 Running Locally

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Default Packages, Products & Admin
```bash
python seed_data.py
```

### 4. Start the Application
```bash
python app.py
```
Open your browser and visit: **`http://127.0.0.1:5000`**

---

## 🌐 Free Cloud Deployment (Zero Lag)

### Option A: Vercel (Serverless Free Tier)
This repository includes `vercel.json` and `api/index.py` configured for Vercel:
1. Push this project to GitHub.
2. Go to [Vercel](https://vercel.com) and click **"Add New Project"**.
3. Import your GitHub repository.
4. Set Environment Variables under **Project Settings -> Environment Variables**:
   - `SECRET_KEY`: any random string
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: `admin123`
   - `ADMIN_PHONE`: `919876543210` (Your admin WhatsApp number)
   - `DATABASE_URL`: Your PostgreSQL connection string from [Supabase](https://supabase.com) or [Neon](https://neon.tech) (both offer 100% free PostgreSQL databases).
5. Click **Deploy**. Vercel will automatically build and deploy the project.

### Option B: Render.com (Recommended for Persistent Zero-Lag 24/7 Hosting)
1. Push this project to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New Web Service**.
3. Connect your repository.
4. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python seed_data.py`
   - **Start Command**: `gunicorn app:app`
5. Add Environment Variables (`SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_PHONE`).
6. Click **Create Web Service**. Render provides zero-lag hosting with instant responses.

---

## 📱 WhatsApp Integration Details
The system generates universal `wa.me` links containing pre-formatted messages and clickable Google Maps GPS coordinates:
- **Admin Alert**: Sent when a customer books (`https://wa.me/<admin_phone>?text=...`).
- **Confirmation Alert**: Sent when Admin confirms a booking (`https://wa.me/<customer_phone>?text=...`).
- **Reschedule / Extension Alert**: Sent when Admin updates the date or time slot.

