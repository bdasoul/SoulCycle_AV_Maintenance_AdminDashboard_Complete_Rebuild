from flask import Blueprint, request, jsonify
from src.models.maintenance import db, Studio, Equipment
from datetime import datetime

studios_bp = Blueprint('studios', __name__)

@studios_bp.route('/studios', methods=['GET'])
def get_studios():
    """Get all studios with optional filtering"""
    try:
        # Get query parameters
        is_active = request.args.get('is_active', type=bool)
        city = request.args.get('city')
        state = request.args.get('state')
        
        # Build query
        query = Studio.query
        
        if is_active is not None:
            query = query.filter(Studio.is_active == is_active)
        if city:
            query = query.filter(Studio.city.ilike(f'%{city}%'))
        if state:
            query = query.filter(Studio.state.ilike(f'%{state}%'))
        
        studios = query.all()
        
        return jsonify({
            'success': True,
            'data': [studio.to_dict() for studio in studios],
            'count': len(studios)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios/<int:studio_id>', methods=['GET'])
def get_studio(studio_id):
    """Get a specific studio by ID"""
    try:
        studio = Studio.query.get_or_404(studio_id)
        
        # Include equipment count
        equipment_count = Equipment.query.filter_by(studio_id=studio_id, is_active=True).count()
        
        studio_data = studio.to_dict()
        studio_data['equipment_count'] = equipment_count
        
        return jsonify({
            'success': True,
            'data': studio_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios', methods=['POST'])
def create_studio():
    """Create a new studio"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create new studio
        studio = Studio(
            name=data['name'],
            location=data['location'],
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            email=data.get('email'),
            manager_name=data.get('manager_name'),
            manager_email=data.get('manager_email'),
            capacity=data.get('capacity'),
            classes_per_day=data.get('classes_per_day', 10),
            operating_hours=data.get('operating_hours'),
            timezone=data.get('timezone', 'America/New_York'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(studio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': studio.to_dict(),
            'message': 'Studio created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios/<int:studio_id>', methods=['PUT'])
def update_studio(studio_id):
    """Update an existing studio"""
    try:
        studio = Studio.query.get_or_404(studio_id)
        data = request.get_json()
        
        # Update fields if provided
        updateable_fields = [
            'name', 'location', 'address', 'city', 'state', 'zip_code',
            'phone', 'email', 'manager_name', 'manager_email', 'capacity',
            'classes_per_day', 'operating_hours', 'timezone', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(studio, field, data[field])
        
        studio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': studio.to_dict(),
            'message': 'Studio updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios/<int:studio_id>', methods=['DELETE'])
def delete_studio(studio_id):
    """Delete a studio (soft delete by setting is_active to False)"""
    try:
        studio = Studio.query.get_or_404(studio_id)
        
        # Soft delete - set is_active to False
        studio.is_active = False
        studio.updated_at = datetime.utcnow()
        
        # Also deactivate all equipment in this studio
        Equipment.query.filter_by(studio_id=studio_id).update({'is_active': False})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Studio deactivated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios/<int:studio_id>/equipment', methods=['GET'])
def get_studio_equipment(studio_id):
    """Get all equipment for a specific studio"""
    try:
        studio = Studio.query.get_or_404(studio_id)
        
        # Get query parameters
        category = request.args.get('category')
        is_active = request.args.get('is_active', type=bool)
        is_critical = request.args.get('is_critical', type=bool)
        
        # Build query
        query = Equipment.query.filter_by(studio_id=studio_id)
        
        if category:
            query = query.filter(Equipment.category == category)
        if is_active is not None:
            query = query.filter(Equipment.is_active == is_active)
        if is_critical is not None:
            query = query.filter(Equipment.is_critical == is_critical)
        
        equipment = query.all()
        
        return jsonify({
            'success': True,
            'data': [eq.to_dict() for eq in equipment],
            'count': len(equipment),
            'studio': studio.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@studios_bp.route('/studios/<int:studio_id>/stats', methods=['GET'])
def get_studio_stats(studio_id):
    """Get statistics for a specific studio"""
    try:
        studio = Studio.query.get_or_404(studio_id)
        
        # Equipment statistics
        total_equipment = Equipment.query.filter_by(studio_id=studio_id, is_active=True).count()
        critical_equipment = Equipment.query.filter_by(studio_id=studio_id, is_active=True, is_critical=True).count()
        
        # Equipment by category
        from sqlalchemy import func
        equipment_by_category = db.session.query(
            Equipment.category,
            func.count(Equipment.id).label('count')
        ).filter_by(studio_id=studio_id, is_active=True).group_by(Equipment.category).all()
        
        category_stats = {cat.value: count for cat, count in equipment_by_category}
        
        # Maintenance statistics (would need to implement when maintenance schedules are available)
        # For now, return basic stats
        
        return jsonify({
            'success': True,
            'data': {
                'studio': studio.to_dict(),
                'equipment_stats': {
                    'total_equipment': total_equipment,
                    'critical_equipment': critical_equipment,
                    'by_category': category_stats
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

