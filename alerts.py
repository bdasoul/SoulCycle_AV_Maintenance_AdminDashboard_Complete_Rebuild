from flask import Blueprint, request, jsonify
from src.models.maintenance import db, Alert, Studio, Equipment, MaintenanceSchedule, Priority
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get alerts with optional filtering"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        equipment_id = request.args.get('equipment_id', type=int)
        alert_type = request.args.get('alert_type')
        priority = request.args.get('priority')
        is_read = request.args.get('is_read', type=bool)
        is_resolved = request.args.get('is_resolved', type=bool)
        limit = request.args.get('limit', default=50, type=int)
        
        query = Alert.query
        
        if studio_id:
            query = query.filter(Alert.studio_id == studio_id)
        if equipment_id:
            query = query.filter(Alert.equipment_id == equipment_id)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if priority:
            try:
                priority_enum = Priority(priority)
                query = query.filter(Alert.priority == priority_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {priority}'}), 400
        if is_read is not None:
            query = query.filter(Alert.is_read == is_read)
        if is_resolved is not None:
            query = query.filter(Alert.is_resolved == is_resolved)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        
        # Include related data
        result = []
        for alert in alerts:
            alert_data = alert.to_dict()
            alert_data['studio_name'] = alert.studio.name if alert.studio else None
            alert_data['equipment_name'] = alert.equipment.name if alert.equipment else None
            result.append(alert_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        required_fields = ['alert_type', 'title', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate priority
        priority = Priority.MEDIUM
        if data.get('priority'):
            try:
                priority = Priority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {data["priority"]}'}), 400
        
        # Validate related objects if provided
        if data.get('studio_id'):
            studio = Studio.query.get(data['studio_id'])
            if not studio:
                return jsonify({'success': False, 'error': 'Studio not found'}), 404
        
        if data.get('equipment_id'):
            equipment = Equipment.query.get(data['equipment_id'])
            if not equipment:
                return jsonify({'success': False, 'error': 'Equipment not found'}), 404
        
        if data.get('schedule_id'):
            schedule = MaintenanceSchedule.query.get(data['schedule_id'])
            if not schedule:
                return jsonify({'success': False, 'error': 'Maintenance schedule not found'}), 404
        
        alert = Alert(
            studio_id=data.get('studio_id'),
            equipment_id=data.get('equipment_id'),
            schedule_id=data.get('schedule_id'),
            alert_type=data['alert_type'],
            priority=priority,
            title=data['title'],
            message=data['message']
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': alert.to_dict(),
            'message': 'Alert created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update an alert (mark as read/resolved)"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        data = request.get_json()
        
        if 'is_read' in data:
            alert.is_read = data['is_read']
            if alert.is_read and not alert.read_at:
                alert.read_at = datetime.utcnow()
        
        if 'is_resolved' in data:
            alert.is_resolved = data['is_resolved']
            if alert.is_resolved:
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = data.get('resolved_by')
            else:
                alert.resolved_at = None
                alert.resolved_by = None
        
        if 'priority' in data:
            try:
                alert.priority = Priority(data['priority'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid priority: {data["priority"]}'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': alert.to_dict(),
            'message': 'Alert updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/bulk-read', methods=['POST'])
def mark_alerts_read():
    """Mark multiple alerts as read"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        
        if not alert_ids:
            return jsonify({'success': False, 'error': 'No alert IDs provided'}), 400
        
        alerts = Alert.query.filter(Alert.id.in_(alert_ids)).all()
        
        for alert in alerts:
            alert.is_read = True
            if not alert.read_at:
                alert.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(alerts)} alerts marked as read'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/bulk-resolve', methods=['POST'])
def resolve_alerts():
    """Mark multiple alerts as resolved"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        resolved_by = data.get('resolved_by')
        
        if not alert_ids:
            return jsonify({'success': False, 'error': 'No alert IDs provided'}), 400
        
        alerts = Alert.query.filter(Alert.id.in_(alert_ids)).all()
        
        for alert in alerts:
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(alerts)} alerts resolved'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/generate-maintenance', methods=['POST'])
def generate_maintenance_alerts():
    """Generate alerts for upcoming and overdue maintenance"""
    try:
        # Get maintenance schedules that need alerts
        today = date.today()
        upcoming_cutoff = today + timedelta(days=7)  # Alert for maintenance due in next 7 days
        
        # Find overdue maintenance
        overdue_schedules = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date < today,
                MaintenanceSchedule.status.in_(['scheduled', 'in_progress'])
            )
        ).all()
        
        # Find upcoming maintenance
        upcoming_schedules = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date >= today,
                MaintenanceSchedule.scheduled_date <= upcoming_cutoff,
                MaintenanceSchedule.status == 'scheduled'
            )
        ).all()
        
        alerts_created = 0
        
        # Create overdue alerts
        for schedule in overdue_schedules:
            # Check if alert already exists
            existing_alert = Alert.query.filter(
                and_(
                    Alert.schedule_id == schedule.id,
                    Alert.alert_type == 'maintenance_overdue',
                    Alert.is_resolved == False
                )
            ).first()
            
            if not existing_alert:
                days_overdue = (today - schedule.scheduled_date).days
                alert = Alert(
                    studio_id=schedule.studio_id,
                    equipment_id=schedule.equipment_id,
                    schedule_id=schedule.id,
                    alert_type='maintenance_overdue',
                    priority=Priority.HIGH if days_overdue > 7 else Priority.MEDIUM,
                    title=f'Overdue Maintenance: {schedule.equipment.name}',
                    message=f'Maintenance for {schedule.equipment.name} at {schedule.studio.name} is {days_overdue} days overdue. Task: {schedule.task.name}'
                )
                db.session.add(alert)
                alerts_created += 1
        
        # Create upcoming alerts
        for schedule in upcoming_schedules:
            # Check if alert already exists
            existing_alert = Alert.query.filter(
                and_(
                    Alert.schedule_id == schedule.id,
                    Alert.alert_type == 'maintenance_due',
                    Alert.is_resolved == False
                )
            ).first()
            
            if not existing_alert:
                days_until = (schedule.scheduled_date - today).days
                alert = Alert(
                    studio_id=schedule.studio_id,
                    equipment_id=schedule.equipment_id,
                    schedule_id=schedule.id,
                    alert_type='maintenance_due',
                    priority=Priority.MEDIUM,
                    title=f'Upcoming Maintenance: {schedule.equipment.name}',
                    message=f'Maintenance for {schedule.equipment.name} at {schedule.studio.name} is due in {days_until} days. Task: {schedule.task.name}'
                )
                db.session.add(alert)
                alerts_created += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{alerts_created} maintenance alerts generated',
            'data': {
                'alerts_created': alerts_created,
                'overdue_count': len(overdue_schedules),
                'upcoming_count': len(upcoming_schedules)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        
        query = Alert.query
        if studio_id:
            query = query.filter(Alert.studio_id == studio_id)
        
        # Total counts
        total_alerts = query.count()
        unread_alerts = query.filter(Alert.is_read == False).count()
        unresolved_alerts = query.filter(Alert.is_resolved == False).count()
        
        # Alerts by priority
        from sqlalchemy import func
        priority_stats = db.session.query(
            Alert.priority,
            func.count(Alert.id).label('count')
        ).filter(Alert.is_resolved == False)
        
        if studio_id:
            priority_stats = priority_stats.filter(Alert.studio_id == studio_id)
        
        priority_stats = priority_stats.group_by(Alert.priority).all()
        priority_data = {priority.value: count for priority, count in priority_stats}
        
        # Alerts by type
        type_stats = db.session.query(
            Alert.alert_type,
            func.count(Alert.id).label('count')
        ).filter(Alert.is_resolved == False)
        
        if studio_id:
            type_stats = type_stats.filter(Alert.studio_id == studio_id)
        
        type_stats = type_stats.group_by(Alert.alert_type).all()
        type_data = {alert_type: count for alert_type, count in type_stats}
        
        # Recent alerts (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_alerts = query.filter(Alert.created_at >= week_ago).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_alerts': total_alerts,
                'unread_alerts': unread_alerts,
                'unresolved_alerts': unresolved_alerts,
                'recent_alerts': recent_alerts,
                'by_priority': priority_data,
                'by_type': type_data
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@alerts_bp.route('/alerts/types', methods=['GET'])
def get_alert_types():
    """Get available alert types"""
    try:
        alert_types = [
            {'value': 'maintenance_due', 'name': 'Maintenance Due'},
            {'value': 'maintenance_overdue', 'name': 'Maintenance Overdue'},
            {'value': 'equipment_failure', 'name': 'Equipment Failure'},
            {'value': 'warranty_expiring', 'name': 'Warranty Expiring'},
            {'value': 'inspection_required', 'name': 'Inspection Required'},
            {'value': 'parts_needed', 'name': 'Parts Needed'},
            {'value': 'technician_required', 'name': 'Technician Required'},
            {'value': 'system_notification', 'name': 'System Notification'}
        ]
        
        return jsonify({
            'success': True,
            'data': alert_types
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

