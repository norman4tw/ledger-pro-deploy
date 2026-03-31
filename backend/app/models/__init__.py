from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    google_sheets_configs = db.relationship('GoogleSheetsConfig', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    monday_configs = db.relationship('MondayConfig', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'company': self.company,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')  # active, completed, archived
    source = db.Column(db.String(50), default='manual')  # manual, monday, sheets
    source_id = db.Column(db.String(255))  # Original ID from source
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    phases = db.relationship('Phase', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_phases=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'source': self.source,
            'source_id': self.source_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_phases:
            data['phases'] = [p.to_dict() for p in self.phases.order_by(Phase.start_date)]
        return data


class Phase(db.Model):
    __tablename__ = 'phases'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(20), default='#002b59')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed
    progress = db.Column(db.Integer, default=0)  # 0-100
    source_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'progress': self.progress,
            'source_id': self.source_id
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    phase_id = db.Column(db.Integer, db.ForeignKey('phases.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='todo')  # todo, in_progress, review, done
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    assignee = db.Column(db.String(255))
    due_date = db.Column(db.Date)
    deliverable_url = db.Column(db.String(500))
    source = db.Column(db.String(50))  # monday, sheets, jira
    source_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'phase_id': self.phase_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'deliverable_url': self.deliverable_url,
            'source': self.source,
            'source_id': self.source_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class GoogleSheetsConfig(db.Model):
    __tablename__ = 'google_sheets_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    service_account_email = db.Column(db.String(255))
    spreadsheet_url = db.Column(db.String(500))
    spreadsheet_id = db.Column(db.String(255))
    sync_frequency = db.Column(db.String(50), default='hourly')  # real-time, hourly, daily, manual
    last_sync = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'service_account_email': self.service_account_email,
            'spreadsheet_url': self.spreadsheet_url,
            'spreadsheet_id': self.spreadsheet_id,
            'sync_frequency': self.sync_frequency,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'is_active': self.is_active
        }


class MondayConfig(db.Model):
    __tablename__ = 'monday_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255))
    board_ids = db.Column(db.Text)  # JSON array of board IDs
    sync_frequency = db.Column(db.String(50), default='hourly')
    last_sync = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'board_ids': self.board_ids,
            'sync_frequency': self.sync_frequency,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'is_active': self.is_active
        }
