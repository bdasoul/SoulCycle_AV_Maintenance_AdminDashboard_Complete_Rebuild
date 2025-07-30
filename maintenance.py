from flask import Blueprint, request, jsonify
from src.models.maintenance import (
    db, MaintenanceTask, MaintenanceSchedule, MaintenanceHistory, Equipment, Studio,
    EquipmentCategory, MaintenanceType, TaskStatus, Priority
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

maintenance_bp = Blueprint('maintenance', __name__)

# Maintenance Tasks Routes
@maintenance_bp.route('/maintenance/tasks', methods=['GET'])
def get_maintenance_tasks():
    """Get all maintenance tasks with optional filtering"""
    try:
        category = request.args.get('category')
        maintenance_type = request.args.get('maintenance_type')
        is_active = request.args.get('is_active', type=bool)
        
        query = MaintenanceTask.query
        
        if category:
            try:
                cat_enum = EquipmentCategory(category)
                query = query.filter(MaintenanceTask.category == cat_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid category: {category}'}), 400
        
        if maintenance_type:
            try:
                type_enum = MaintenanceType(maintenance_type)
                query = query.filter(MaintenanceTask.maintenance_type == type_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid maintenance type: {maintenance_type}'}), 400
        
        if is_active is not None:
            query = query.filter(MaintenanceTask.is_active == is_active)
        
        tasks = query.all()
        
        return jsonify({
            'success': True,
            'data': [task.to_dict() for task in tasks],
            'count': len(tasks)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/tasks', methods=['POST'])
def create_maintenance_task():
    """Create a new maintenance task"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'category', 'maintenance_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate enums
        try:
            category = EquipmentCategory(data['category'])
            maintenance_type = MaintenanceType(data['maintenance_type'])
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Invalid enum value: {str(e)}'}), 400
        
        task = MaintenanceTask(
            name=data['name'],
            description=data.get('description'),
            category=category,
            maintenance_type=maintenance_type,
            estimated_duration_minutes=data.get('estimated_duration_minutes', 30),
            safety_requirements=data.get('safety_requirements'),
            frequency_days=data.get('frequency_days'),
            is_active=data.get('is_active', True)
        )
        
        # Set JSON fields
        if data.get('required_tools'):
            task.set_required_tools(data['required_tools'])
        if data.get('required_skills'):
            task.set_required_skills(data['required_skills'])
        if data.get('procedure_steps'):
            task.set_procedure_steps(data['procedure_steps'])
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': task.to_dict(),
            'message': 'Maintenance task created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Maintenance Schedules Routes
@maintenance_bp.route('/maintenance/schedules', methods=['GET'])
def get_maintenance_schedules():
    """Get maintenance schedules with filtering"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        equipment_id = request.args.get('equipment_id', type=int)
        status = request.args.get('status')
        priority = request.args.get('priority')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        assigned_technician = request.args.get('assigned_technician')
        
        query = MaintenanceSchedule.query
        
        if studio_id:
            query = query.filter(MaintenanceSchedule.studio_id == studio_id)
        if equipment_id:
            query = query.filter(MaintenanceSchedule.equipment_id == equipment_id)
        if status:
            try:
                status_enum = TaskStatus(status)
                query = query.filter(MaintenanceSchedule.status == status_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid status: {status}'}), 400
        if priority:
            try:
                priority_enum = Priority(priority)
                query = query.filter(MaintenanceSchedule.priority == priority_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {priority}'}), 400
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(MaintenanceSchedule.scheduled_date >= start)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(MaintenanceSchedule.scheduled_date <= end)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        if assigned_technician:
            query = query.filter(MaintenanceSchedule.assigned_technician.ilike(f'%{assigned_technician}%'))
        
        schedules = query.order_by(MaintenanceSchedule.scheduled_date).all()
        
        # Include related data
        result = []
        for schedule in schedules:
            schedule_data = schedule.to_dict()
            schedule_data['studio_name'] = schedule.studio.name if schedule.studio else None
            schedule_data['equipment_name'] = schedule.equipment.name if schedule.equipment else None
            schedule_data['task_name'] = schedule.task.name if schedule.task else None
            schedule_data['is_overdue'] = schedule.is_overdue()
            result.append(schedule_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/schedules', methods=['POST'])
def create_maintenance_schedule():
    """Create a new maintenance schedule"""
    try:
        data = request.get_json()
        
        required_fields = ['studio_id', 'equipment_id', 'task_id', 'scheduled_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate related objects exist
        studio = Studio.query.get(data['studio_id'])
        equipment = Equipment.query.get(data['equipment_id'])
        task = MaintenanceTask.query.get(data['task_id'])
        
        if not studio:
            return jsonify({'success': False, 'error': 'Studio not found'}), 404
        if not equipment:
            return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        if not task:
            return jsonify({'success': False, 'error': 'Maintenance task not found'}), 404
        
        # Parse dates and times
        try:
            scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid scheduled_date format. Use YYYY-MM-DD'}), 400
        
        scheduled_time = None
        if data.get('scheduled_time'):
            try:
                scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid scheduled_time format. Use HH:MM'}), 400
        
        # Validate priority and status
        priority = Priority.MEDIUM
        if data.get('priority'):
            try:
                priority = Priority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {data["priority"]}'}), 400
        
        status = TaskStatus.SCHEDULED
        if data.get('status'):
            try:
                status = TaskStatus(data['status'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid status: {data["status"]}'}), 400
        
        schedule = MaintenanceSchedule(
            studio_id=data['studio_id'],
            equipment_id=data['equipment_id'],
            task_id=data['task_id'],
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            priority=priority,
            status=status,
            assigned_technician=data.get('assigned_technician'),
            estimated_duration_minutes=data.get('estimated_duration_minutes', task.estimated_duration_minutes),
            notes=data.get('notes'),
            is_recurring=data.get('is_recurring', True)
        )
        
        # Set parts if provided
        if data.get('parts_used'):
            schedule.set_parts_used(data['parts_used'])
        
        # Calculate next occurrence for recurring tasks
        if schedule.is_recurring and task.frequency_days:
            schedule.next_occurrence = scheduled_date + timedelta(days=task.frequency_days)
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': schedule.to_dict(),
            'message': 'Maintenance schedule created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/schedules/<int:schedule_id>', methods=['PUT'])
def update_maintenance_schedule(schedule_id):
    """Update a maintenance schedule"""
    try:
        schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
        data = request.get_json()
        
        # Update basic fields
        if 'assigned_technician' in data:
            schedule.assigned_technician = data['assigned_technician']
        if 'notes' in data:
            schedule.notes = data['notes']
        if 'cost' in data:
            schedule.cost = data['cost']
        if 'actual_duration_minutes' in data:
            schedule.actual_duration_minutes = data['actual_duration_minutes']
        
        # Update status
        if 'status' in data:
            try:
                new_status = TaskStatus(data['status'])
                schedule.status = new_status
                
                # If marking as completed, set completion details
                if new_status == TaskStatus.COMPLETED:
                    schedule.completed_date = datetime.utcnow()
                    schedule.completed_by = data.get('completed_by', schedule.assigned_technician)
                    
                    # Update equipment last maintenance date
                    equipment = schedule.equipment
                    equipment.last_maintenance = schedule.scheduled_date
                    equipment.next_maintenance = equipment.calculate_next_maintenance()
                    
                    # Create next recurring schedule if applicable
                    if schedule.is_recurring and schedule.next_occurrence:
                        next_schedule = MaintenanceSchedule(
                            studio_id=schedule.studio_id,
                            equipment_id=schedule.equipment_id,
                            task_id=schedule.task_id,
                            scheduled_date=schedule.next_occurrence,
                            priority=schedule.priority,
                            status=TaskStatus.SCHEDULED,
                            estimated_duration_minutes=schedule.estimated_duration_minutes,
                            is_recurring=True
                        )
                        
                        # Calculate next occurrence
                        task = schedule.task
                        if task.frequency_days:
                            next_schedule.next_occurrence = schedule.next_occurrence + timedelta(days=task.frequency_days)
                        
                        db.session.add(next_schedule)
                
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid status: {data["status"]}'}), 400
        
        # Update priority
        if 'priority' in data:
            try:
                schedule.priority = Priority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {data["priority"]}'}), 400
        
        # Update parts used
        if 'parts_used' in data:
            schedule.set_parts_used(data['parts_used'])
        
        # Update dates
        if 'scheduled_date' in data:
            try:
                schedule.scheduled_date = datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid scheduled_date format. Use YYYY-MM-DD'}), 400
        
        if 'scheduled_time' in data:
            try:
                schedule.scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid scheduled_time format. Use HH:MM'}), 400
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': schedule.to_dict(),
            'message': 'Maintenance schedule updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/schedules/overdue', methods=['GET'])
def get_overdue_maintenance():
    """Get overdue maintenance schedules"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        
        query = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date < date.today(),
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        )
        
        if studio_id:
            query = query.filter(MaintenanceSchedule.studio_id == studio_id)
        
        overdue_schedules = query.order_by(MaintenanceSchedule.scheduled_date).all()
        
        result = []
        for schedule in overdue_schedules:
            schedule_data = schedule.to_dict()
            schedule_data['studio_name'] = schedule.studio.name if schedule.studio else None
            schedule_data['equipment_name'] = schedule.equipment.name if schedule.equipment else None
            schedule_data['task_name'] = schedule.task.name if schedule.task else None
            schedule_data['days_overdue'] = (date.today() - schedule.scheduled_date).days
            result.append(schedule_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/history', methods=['GET'])
def get_maintenance_history():
    """Get maintenance history with filtering"""
    try:
        equipment_id = request.args.get('equipment_id', type=int)
        studio_id = request.args.get('studio_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        maintenance_type = request.args.get('maintenance_type')
        technician = request.args.get('technician')
        limit = request.args.get('limit', default=50, type=int)
        
        query = MaintenanceHistory.query
        
        if equipment_id:
            query = query.filter(MaintenanceHistory.equipment_id == equipment_id)
        
        if studio_id:
            # Join with equipment to filter by studio
            query = query.join(Equipment).filter(Equipment.studio_id == studio_id)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(MaintenanceHistory.maintenance_date >= start)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(MaintenanceHistory.maintenance_date <= end)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        if maintenance_type:
            try:
                type_enum = MaintenanceType(maintenance_type)
                query = query.filter(MaintenanceHistory.maintenance_type == type_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid maintenance type: {maintenance_type}'}), 400
        
        if technician:
            query = query.filter(MaintenanceHistory.technician.ilike(f'%{technician}%'))
        
        history = query.order_by(MaintenanceHistory.maintenance_date.desc()).limit(limit).all()
        
        result = []
        for record in history:
            record_data = record.to_dict()
            record_data['equipment_name'] = record.equipment.name if record.equipment else None
            record_data['studio_name'] = record.equipment.studio.name if record.equipment and record.equipment.studio else None
            result.append(record_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@maintenance_bp.route('/maintenance/stats', methods=['GET'])
def get_maintenance_stats():
    """Get maintenance statistics"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        days_back = request.args.get('days_back', default=30, type=int)
        
        start_date = date.today() - timedelta(days=days_back)
        
        # Base queries
        schedule_query = MaintenanceSchedule.query
        history_query = MaintenanceHistory.query
        
        if studio_id:
            schedule_query = schedule_query.filter(MaintenanceSchedule.studio_id == studio_id)
            history_query = history_query.join(Equipment).filter(Equipment.studio_id == studio_id)
        
        # Scheduled maintenance stats
        total_scheduled = schedule_query.count()
        completed = schedule_query.filter(MaintenanceSchedule.status == TaskStatus.COMPLETED).count()
        overdue = schedule_query.filter(
            and_(
                MaintenanceSchedule.scheduled_date < date.today(),
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        ).count()
        
        upcoming = schedule_query.filter(
            and_(
                MaintenanceSchedule.scheduled_date >= date.today(),
                MaintenanceSchedule.scheduled_date <= date.today() + timedelta(days=7),
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        ).count()
        
        # Recent maintenance history
        recent_maintenance = history_query.filter(
            MaintenanceHistory.maintenance_date >= start_date
        ).count()
        
        # Maintenance by type
        type_stats = db.session.query(
            MaintenanceHistory.maintenance_type,
            func.count(MaintenanceHistory.id).label('count')
        ).filter(MaintenanceHistory.maintenance_date >= start_date)
        
        if studio_id:
            type_stats = type_stats.join(Equipment).filter(Equipment.studio_id == studio_id)
        
        type_stats = type_stats.group_by(MaintenanceHistory.maintenance_type).all()
        type_data = {mtype.value: count for mtype, count in type_stats}
        
        # Average completion time
        avg_duration = db.session.query(
            func.avg(MaintenanceSchedule.actual_duration_minutes)
        ).filter(
            and_(
                MaintenanceSchedule.status == TaskStatus.COMPLETED,
                MaintenanceSchedule.actual_duration_minutes.isnot(None)
            )
        )
        
        if studio_id:
            avg_duration = avg_duration.filter(MaintenanceSchedule.studio_id == studio_id)
        
        avg_duration = avg_duration.scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'scheduled_maintenance': {
                    'total': total_scheduled,
                    'completed': completed,
                    'overdue': overdue,
                    'upcoming_week': upcoming,
                    'completion_rate': round((completed / total_scheduled * 100) if total_scheduled > 0 else 0, 2)
                },
                'recent_maintenance': {
                    'count': recent_maintenance,
                    'by_type': type_data,
                    'avg_duration_minutes': round(avg_duration, 2)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

