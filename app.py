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
        return render_template('errors/500.html'), 500

    # Auto create tables and check for default admin
    with app.app_context():
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
            db.session.commit()

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

