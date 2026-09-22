import os
from flask import Flask, render_template, session
from config import Config
from database import db
from models import User, Package, Product, Booking, MachineDamageReport, LeaveRequest, OvertimeLog

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.worker_routes import worker_bp
    from routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(worker_bp)
    app.register_blueprint(api_bp)

    # Global context processor
    @app.context_processor
    def inject_globals():
        current_user = None
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
        return {
            'config': Config,
            'current_user': current_user,
            'session_role': session.get('role'),
            'session_username': session.get('username')
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        import traceback
        from flask import request
        app.logger.error(f"Server Error: {e}\n{traceback.format_exc()}")
        if request.args.get('debug') == '1':
            return f"<h3>500 Internal Server Error</h3><pre>{traceback.format_exc()}</pre>", 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        import traceback
        from werkzeug.exceptions import HTTPException
        from flask import request
        if isinstance(e, HTTPException):
            return e
        app.logger.error(f"Unhandled Exception: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        if request.args.get('debug') == '1':
            return f"<h3>Unhandled Exception: {type(e).__name__}: {e}</h3><pre>{traceback.format_exc()}</pre>", 500
        return render_template('errors/500.html'), 500

    # Auto create tables and check for default admin & initial packages
    with app.app_context():
        try:
            db.create_all()
            # Ensure default fixed admin user exists
            admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
            if not admin:
                admin = User(
                    username=Config.ADMIN_USERNAME,
                    full_name="GlowWheels Admin",
                    role="admin"
                )
                admin.set_password(Config.ADMIN_PASSWORD)
                db.session.add(admin)

            # Ensure default packages exist if table is empty
            if Package.query.count() == 0:
                default_packages = [
                    Package(
                        name="Basic Wash",
                        price=299.0,
                        duration_mins=30,
                        badge="Essential",
                        icon="droplet",
                        description="Quick exterior spruce up for everyday driving.",
                        features="Exterior wash; Foam cleaning; Wheel cleaning; Drying; Tyre dressing"
                    ),
                    Package(
                        name="Premium Wash",
                        price=499.0,
                        duration_mins=50,
                        badge="Most Popular",
                        icon="sparkles",
                        description="Comprehensive interior and exterior detailing for complete cleanliness.",
                        features="Exterior wash; Interior vacuum; Dashboard cleaning; Tyre cleaning; Mat cleaning; Glass cleaning"
                    ),
                    Package(
                        name="Complete Detailing",
                        price=999.0,
                        duration_mins=90,
                        badge="Luxury Care",
                        icon="shield-halved",
                        description="Showroom gloss restoration with paint wax and deep interior sanitization.",
                        features="Everything in Premium; Interior deep cleaning; Stain removal; Polishing and waxing; Headlight cleaning; Long lasting protection"
                    )
                ]
                db.session.bulk_save_objects(default_packages)

            # Ensure default products exist if empty
            if Product.query.count() == 0:
                default_products = [
                    Product(name="High Foam Car Shampoo", category="Chemicals", stock_quantity=14, unit="bottles", low_threshold=3),
                    Product(name="Tire Shine and Rim Polish", category="Chemicals", stock_quantity=8, unit="bottles", low_threshold=2),
                    Product(name="Microfiber Detailing Towels", category="Accessories", stock_quantity=24, unit="pieces", low_threshold=6),
                    Product(name="Carnauba Liquid Body Wax", category="Polish", stock_quantity=5, unit="bottles", low_threshold=2),
                    Product(name="Interior Dashboard Dressing", category="Chemicals", stock_quantity=6, unit="bottles", low_threshold=2),
                    Product(name="Wet and Dry Vacuum Bags", category="Equipment", stock_quantity=10, unit="packs", low_threshold=3),
                    Product(name="Ceramic Hydrophobic Sealant", category="Coatings", stock_quantity=4, unit="bottles", low_threshold=2)
                ]
                db.session.bulk_save_objects(default_products)

            # Ensure sample worker exists if none
            if not User.query.filter_by(role='worker').first():
                sample_worker = User(
                    username="worker1",
                    full_name="Ramesh (Field Specialist)",
                    phone="9876500001",
                    role="worker"
                )
                sample_worker.set_password("worker123")
                db.session.add(sample_worker)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Database initialization notice: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("==================================================")
    print("  GlowWheels Mobile Car Wash Platform Running")
    print(f"  Local URL: http://127.0.0.1:{port}")
    print(f"  Admin Login: {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")
    print("==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)

