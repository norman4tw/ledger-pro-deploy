from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Project, Phase, Task
from datetime import datetime

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')

@projects_bp.route('', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects for current user"""
    current_user_id = int(int(get_jwt_identity()))
    
    projects = Project.query.filter_by(user_id=current_user_id).order_by(Project.created_at.desc()).all()
    
    return jsonify({
        'projects': [p.to_dict() for p in projects]
    }), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Project name is required'}), 400
    
    project = Project(
        user_id=current_user_id,
        name=data['name'],
        description=data.get('description'),
        status=data.get('status', 'active'),
        source=data.get('source', 'manual'),
        source_id=data.get('source_id')
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'message': 'Project created',
        'project': project.to_dict()
    }), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get a specific project with phases"""
    current_user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify({
        'project': project.to_dict(include_phases=True)
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project"""
    current_user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if data.get('status'):
        project.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Project updated',
        'project': project.to_dict()
    }), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project"""
    current_user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'message': 'Project deleted'}), 200


# Phase routes
@projects_bp.route('/<int:project_id>/phases', methods=['GET'])
@jwt_required()
def get_phases(project_id):
    """Get all phases for a project"""
    current_user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    phases = Phase.query.filter_by(project_id=project_id).order_by(Phase.start_date).all()
    
    return jsonify({
        'phases': [p.to_dict() for p in phases]
    }), 200


@projects_bp.route('/<int:project_id>/phases', methods=['POST'])
@jwt_required()
def create_phase(project_id):
    """Create a new phase"""
    current_user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    
    if not data.get('name') or not data.get('start_date') or not data.get('end_date'):
        return jsonify({'error': 'Name, start_date, and end_date are required'}), 400
    
    phase = Phase(
        project_id=project_id,
        name=data['name'],
        description=data.get('description'),
        color=data.get('color', '#002b59'),
        start_date=datetime.fromisoformat(data['start_date']).date() if isinstance(data['start_date'], str) else data['start_date'],
        end_date=datetime.fromisoformat(data['end_date']).date() if isinstance(data['end_date'], str) else data['end_date'],
        status=data.get('status', 'pending'),
        progress=data.get('progress', 0),
        source_id=data.get('source_id')
    )
    
    db.session.add(phase)
    db.session.commit()
    
    return jsonify({
        'message': 'Phase created',
        'phase': phase.to_dict()
    }), 201


@projects_bp.route('/phases/<int:phase_id>', methods=['PUT'])
@jwt_required()
def update_phase(phase_id):
    """Update a phase"""
    current_user_id = int(get_jwt_identity())
    
    phase = Phase.query.join(Project).filter(
        Phase.id == phase_id,
        Project.user_id == current_user_id
    ).first()
    
    if not phase:
        return jsonify({'error': 'Phase not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        phase.name = data['name']
    if 'description' in data:
        phase.description = data['description']
    if data.get('color'):
        phase.color = data['color']
    if data.get('start_date'):
        phase.start_date = datetime.fromisoformat(data['start_date']).date() if isinstance(data['start_date'], str) else data['start_date']
    if data.get('end_date'):
        phase.end_date = datetime.fromisoformat(data['end_date']).date() if isinstance(data['end_date'], str) else data['end_date']
    if data.get('status'):
        phase.status = data['status']
    if 'progress' in data:
        phase.progress = data['progress']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Phase updated',
        'phase': phase.to_dict()
    }), 200


@projects_bp.route('/phases/<int:phase_id>', methods=['DELETE'])
@jwt_required()
def delete_phase(phase_id):
    """Delete a phase"""
    current_user_id = int(get_jwt_identity())
    
    phase = Phase.query.join(Project).filter(
        Phase.id == phase_id,
        Project.user_id == current_user_id
    ).first()
    
    if not phase:
        return jsonify({'error': 'Phase not found'}), 404
    
    db.session.delete(phase)
    db.session.commit()
    
    return jsonify({'message': 'Phase deleted'}), 200
