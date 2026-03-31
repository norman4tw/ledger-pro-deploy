from .auth import auth_bp
from .projects import projects_bp
from .tasks import tasks_bp
from .sheets import sheets_bp

def register_blueprints(app):
    """Register all blueprints with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(sheets_bp)
