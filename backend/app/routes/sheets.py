from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, GoogleSheetsConfig, Project, Phase, Task
from app.services.google_sheets_service import GoogleSheetsService
from datetime import datetime

sheets_bp = Blueprint('sheets', __name__, url_prefix='/api/sheets')

@sheets_bp.route('/configs', methods=['GET'])
@jwt_required()
def get_configs():
    """Get all Google Sheets configurations for current user"""
    current_user_id = int(get_jwt_identity())
    
    configs = GoogleSheetsConfig.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({
        'configs': [c.to_dict() for c in configs]
    }), 200


@sheets_bp.route('/configs', methods=['POST'])
@jwt_required()
def create_config():
    """Create a new Google Sheets configuration"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('name') or not data.get('spreadsheet_url'):
        return jsonify({'error': 'name and spreadsheet_url are required'}), 400
    
    config = GoogleSheetsConfig(
        user_id=current_user_id,
        name=data['name'],
        service_account_email=data.get('service_account_email'),
        spreadsheet_url=data['spreadsheet_url'],
        sync_frequency=data.get('sync_frequency', 'hourly')
    )
    
    # Extract spreadsheet ID
    url = data['spreadsheet_url']
    if '/d/' in url:
        config.spreadsheet_id = url.split('/d/')[1].split('/')[0]
    
    db.session.add(config)
    db.session.commit()
    
    return jsonify({
        'message': 'Configuration created',
        'config': config.to_dict()
    }), 201


@sheets_bp.route('/configs/<int:config_id>', methods=['GET'])
@jwt_required()
def get_config(config_id):
    """Get a specific Google Sheets configuration"""
    current_user_id = int(get_jwt_identity())
    
    config = GoogleSheetsConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    return jsonify({
        'config': config.to_dict()
    }), 200


@sheets_bp.route('/configs/<int:config_id>', methods=['PUT'])
@jwt_required()
def update_config(config_id):
    """Update a Google Sheets configuration"""
    current_user_id = int(get_jwt_identity())
    
    config = GoogleSheetsConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        config.name = data['name']
    if data.get('service_account_email'):
        config.service_account_email = data['service_account_email']
    if data.get('spreadsheet_url'):
        config.spreadsheet_url = data['spreadsheet_url']
        if '/d/' in data['spreadsheet_url']:
            config.spreadsheet_id = data['spreadsheet_url'].split('/d/')[1].split('/')[0]
    if data.get('sync_frequency'):
        config.sync_frequency = data['sync_frequency']
    if 'is_active' in data:
        config.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Configuration updated',
        'config': config.to_dict()
    }), 200


@sheets_bp.route('/configs/<int:config_id>', methods=['DELETE'])
@jwt_required()
def delete_config(config_id):
    """Delete a Google Sheets configuration"""
    current_user_id = int(get_jwt_identity())
    
    config = GoogleSheetsConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    db.session.delete(config)
    db.session.commit()
    
    return jsonify({'message': 'Configuration deleted'}), 200


@sheets_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_spreadsheet():
    """Verify connection to a Google Spreadsheet"""
    data = request.get_json()
    
    if not data.get('spreadsheet_url'):
        return jsonify({'error': 'spreadsheet_url is required'}), 400
    
    # Get credentials from config or request
    credentials = {
        'GOOGLE_APPLICATION_CREDENTIALS': data.get('credentials_file') or current_app.config.get('GOOGLE_APPLICATION_CREDENTIALS'),
        'GOOGLE_SERVICE_ACCOUNT_EMAIL': data.get('service_account_email') or current_app.config.get('GOOGLE_SERVICE_ACCOUNT_EMAIL')
    }
    
    service = GoogleSheetsService(credentials)
    result = service.verify_connection(data['spreadsheet_url'])
    
    if result.get('valid'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@sheets_bp.route('/sync/<int:config_id>', methods=['POST'])
@jwt_required()
def sync_spreadsheet(config_id):
    """Sync data from a Google Spreadsheet to local database"""
    current_user_id = int(get_jwt_identity())
    
    config = GoogleSheetsConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
    
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    # Get credentials
    credentials = {
        'GOOGLE_APPLICATION_CREDENTIALS': current_app.config.get('GOOGLE_APPLICATION_CREDENTIALS'),
        'GOOGLE_SERVICE_ACCOUNT_EMAIL': config.service_account_email
    }
    
    service = GoogleSheetsService(credentials)
    
    # If no credentials configured, try to use from config
    if not credentials['GOOGLE_APPLICATION_CREDENTIALS'] and not credentials['GOOGLE_SERVICE_ACCOUNT_EMAIL']:
        # Return error asking for credentials setup
        return jsonify({
            'error': 'Google Sheets credentials not configured. Please set GOOGLE_APPLICATION_CREDENTIALS in environment.'
        }), 400
    
    # Sync data
    result = service.sync_gantt_data(config.spreadsheet_url)
    
    if 'error' in result:
        return jsonify(result), 400
    
    # Create or update projects and phases
    synced_projects = []
    for project_data in result.get('projects', []):
        # Check if project exists
        project = Project.query.filter_by(
            user_id=current_user_id,
            name=project_data['name'],
            source='sheets'
        ).first()
        
        if not project:
            project = Project(
                user_id=current_user_id,
                name=project_data['name'],
                source='sheets',
                description=f'Synced from Google Sheets on {datetime.utcnow().strftime("%Y-%m-%d")}'
            )
            db.session.add(project)
        
        # Sync phases
        for phase_data in project_data.get('phases', []):
            # Check if phase exists by name
            phase = Phase.query.filter_by(
                project_id=project.id,
                name=phase_data['name']
            ).first()
            
            if not phase:
                phase = Phase(
                    project_id=project.id,
                    name=phase_data['name']
                )
                db.session.add(phase)
            
            phase.description = phase_data.get('description', '')
            phase.color = phase_data.get('color', '#002b59')
            phase.start_date = phase_data.get('start_date')
            phase.end_date = phase_data.get('end_date')
            phase.status = phase_data.get('status', 'pending')
            phase.progress = phase_data.get('progress', 0)
            phase.source_id = f"sheets-{phase_data['name']}"
        
        # Sync tasks
        for task_data in project_data.get('tasks', []):
            # Find phase by name if provided
            phase_id = None
            if task_data.get('phase_name'):
                phase = Phase.query.filter_by(
                    project_id=project.id,
                    name=task_data['phase_name']
                ).first()
                if phase:
                    phase_id = phase.id
            
            task = Task(
                project_id=project.id,
                phase_id=phase_id,
                title=task_data['title'],
                description=task_data.get('description', ''),
                status=task_data.get('status', 'todo'),
                priority=task_data.get('priority', 'medium'),
                assignee=task_data.get('assignee'),
                due_date=task_data.get('due_date'),
                deliverable_url=task_data.get('deliverable_url'),
                source='sheets'
            )
            db.session.add(task)
        
        synced_projects.append(project.to_dict(include_phases=True))
    
    # Update last sync time
    config.last_sync = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': f'Synced {len(synced_projects)} projects',
        'projects': synced_projects,
        'synced_at': result.get('synced_at')
    }), 200
