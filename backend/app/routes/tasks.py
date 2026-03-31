from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Project, Phase, Task
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks for current user, optionally filtered by project"""
    current_user_id = int(get_jwt_identity())
    
    query = Task.query.join(Project).filter(Project.user_id == current_user_id)
    
    # Optional filters
    project_id = request.args.get('project_id', type=int)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    status = request.args.get('status')
    if status:
        query = query.filter(Task.status == status)
    
    priority = request.args.get('priority')
    if priority:
        query = query.filter(Task.priority == priority)
    
    source = request.args.get('source')
    if source:
        query = query.filter(Task.source == source)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify({
        'tasks': [t.to_dict() for t in tasks]
    }), 200


@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('project_id') or not data.get('title'):
        return jsonify({'error': 'project_id and title are required'}), 400
    
    # Verify project ownership
    project = Project.query.filter_by(id=data['project_id'], user_id=current_user_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Verify phase if provided
    phase_id = data.get('phase_id')
    if phase_id:
        phase = Phase.query.filter_by(id=phase_id, project_id=data['project_id']).first()
        if not phase:
            return jsonify({'error': 'Phase not found'}), 404
    
    task = Task(
        project_id=data['project_id'],
        phase_id=phase_id,
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'todo'),
        priority=data.get('priority', 'medium'),
        assignee=data.get('assignee'),
        due_date=datetime.fromisoformat(data['due_date']).date() if data.get('due_date') else None,
        deliverable_url=data.get('deliverable_url'),
        source=data.get('source', 'manual'),
        source_id=data.get('source_id')
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'message': 'Task created',
        'task': task.to_dict()
    }), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get a specific task"""
    current_user_id = int(get_jwt_identity())
    
    task = Task.query.join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user_id
    ).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update a task"""
    current_user_id = int(get_jwt_identity())
    
    task = Task.query.join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user_id
    ).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    if data.get('title'):
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if data.get('status'):
        task.status = data['status']
    if data.get('priority'):
        task.priority = data['priority']
    if 'assignee' in data:
        task.assignee = data['assignee']
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date']).date() if data['due_date'] else None
    if 'deliverable_url' in data:
        task.deliverable_url = data['deliverable_url']
    if 'phase_id' in data:
        task.phase_id = data['phase_id']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task updated',
        'task': task.to_dict()
    }), 200


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    current_user_id = int(get_jwt_identity())
    
    task = Task.query.join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user_id
    ).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'Task deleted'}), 200


@tasks_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_create_tasks():
    """Bulk create tasks (for importing from external sources)"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('tasks') or not isinstance(data['tasks'], list):
        return jsonify({'error': 'tasks array is required'}), 400
    
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({'error': 'project_id is required'}), 400
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    created_tasks = []
    for task_data in data['tasks']:
        if not task_data.get('title'):
            continue
        
        task = Task(
            project_id=project_id,
            phase_id=task_data.get('phase_id'),
            title=task_data['title'],
            description=task_data.get('description'),
            status=task_data.get('status', 'todo'),
            priority=task_data.get('priority', 'medium'),
            assignee=task_data.get('assignee'),
            due_date=datetime.fromisoformat(task_data['due_date']).date() if task_data.get('due_date') else None,
            deliverable_url=task_data.get('deliverable_url'),
            source=task_data.get('source', 'imported'),
            source_id=task_data.get('source_id')
        )
        db.session.add(task)
        created_tasks.append(task)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(created_tasks)} tasks created',
        'tasks': [t.to_dict() for t in created_tasks]
    }), 201
