"""
Database configuration using SQLAlchemy factory pattern.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize database with Flask app using factory pattern.
    
    Args:
        app: Flask application instance
    """
    # Configure database URI
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///maintenance.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        db.create_all()


class BaseModel(db.Model):
    """
    Base model class with common fields and methods.
    """
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the current instance to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the current instance from database."""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    @classmethod
    def get_by_id(cls, id):
        """Get instance by ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """Get all instances."""
        return cls.query.all()

