from flask import Blueprint, request, jsonify
from src.models.maintenance import db, Equipment, Studio, EquipmentCategory, MaintenanceSchedule, MaintenanceHistory
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/equipment', methods=['GET'])
def get_equipment():
    """Get all equipment with optional filtering"""
    try:
        # Get query parameters
        studio_id = request.args.get('studio_id', type=int)
        category = request.args.get('category')
        is_active = request.args.get('is_active', type=bool)
        is_critical = request.args.get('is_critical', type=bool)
        manufacturer = request.args.get('manufacturer')
        maintenance_due = request.args.get('maintenance_due', type=bool)
        
        # Build query
        query = Equipment.query
        
        if studio_id:
            query = query.filter(Equipment.studio_id == studio_id)
        if category:
            try:
                cat_enum = EquipmentCategory(category)
                query = query.filter(Equipment.category == cat_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid category: {category}'}), 400
        if is_active is not None:
            query = query.filter(Equipment.is_active == is_active)
        if is_critical is not None:
            query = query.filter(Equipment.is_critical == is_critical)
        if manufacturer:
            query = query.filter(Equipment.manufacturer.ilike(f'%{manufacturer}%'))
        if maintenance_due:
            today = date.today()
            query = query.filter(Equipment.next_maintenance <= today)
        
        equipment = query.all()
        
        # Include studio information
        result = []
        for eq in equipment:
            eq_data = eq.to_dict()
            eq_data['studio_name'] = eq.studio.name if eq.studio else None
            result.append(eq_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['GET'])
def get_equipment_detail(equipment_id):
    """Get detailed information about specific equipment"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        
        # Get maintenance history
        history = MaintenanceHistory.query.filter_by(equipment_id=equipment_id)\
            .order_by(MaintenanceHistory.maintenance_date.desc()).limit(10).all()
        
        # Get upcoming maintenance
        upcoming = MaintenanceSchedule.query.filter_by(equipment_id=equipment_id)\
            .filter(MaintenanceSchedule.scheduled_date >= date.today())\
            .order_by(MaintenanceSchedule.scheduled_date).limit(5).all()
        
        eq_data = equipment.to_dict()
        eq_data['studio_name'] = equipment.studio.name if equipment.studio else None
        eq_data['maintenance_history'] = [h.to_dict() for h in history]
        eq_data['upcoming_maintenance'] = [s.to_dict() for s in upcoming]
        
        return jsonify({
            'success': True,
            'data': eq_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment', methods=['POST'])
def create_equipment():
    """Create new equipment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['studio_id', 'name', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate studio exists
        studio = Studio.query.get(data['studio_id'])
        if not studio:
            return jsonify({'success': False, 'error': 'Studio not found'}), 404
        
        # Validate category
        try:
            category = EquipmentCategory(data['category'])
        except ValueError:
            return jsonify({'success': False, 'error': f'Invalid category: {data["category"]}'}), 400
        
        # Parse dates
        purchase_date = None
        installation_date = None
        warranty_expiry = None
        
        if data.get('purchase_date'):
            purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        if data.get('installation_date'):
            installation_date = datetime.strptime(data['installation_date'], '%Y-%m-%d').date()
        if data.get('warranty_expiry'):
            warranty_expiry = datetime.strptime(data['warranty_expiry'], '%Y-%m-%d').date()
        
        # Create equipment
        equipment = Equipment(
            studio_id=data['studio_id'],
            name=data['name'],
            category=category,
            manufacturer=data.get('manufacturer'),
            model=data.get('model'),
            serial_number=data.get('serial_number'),
            purchase_date=purchase_date,
            installation_date=installation_date,
            warranty_expiry=warranty_expiry,
            location_in_studio=data.get('location_in_studio'),
            operating_hours=data.get('operating_hours', 0),
            power_cycles=data.get('power_cycles', 0),
            maintenance_interval_days=data.get('maintenance_interval_days', 90),
            usage_based_maintenance=data.get('usage_based_maintenance', False),
            usage_threshold_hours=data.get('usage_threshold_hours', 1000),
            is_critical=data.get('is_critical', False),
            is_active=data.get('is_active', True),
            notes=data.get('notes')
        )
        
        # Set specifications if provided
        if data.get('specifications'):
            equipment.set_specifications(data['specifications'])
        
        # Calculate initial next maintenance date
        if installation_date:
            equipment.last_maintenance = installation_date
            equipment.next_maintenance = equipment.calculate_next_maintenance()
        
        db.session.add(equipment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': equipment.to_dict(),
            'message': 'Equipment created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['PUT'])
def update_equipment(equipment_id):
    """Update existing equipment"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        data = request.get_json()
        
        # Update basic fields
        updateable_fields = [
            'name', 'manufacturer', 'model', 'serial_number', 'location_in_studio',
            'operating_hours', 'power_cycles', 'maintenance_interval_days',
            'usage_based_maintenance', 'usage_threshold_hours', 'is_critical',
            'is_active', 'notes'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(equipment, field, data[field])
        
        # Update category if provided
        if 'category' in data:
            try:
                equipment.category = EquipmentCategory(data['category'])
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid category: {data["category"]}'}), 400
        
        # Update dates if provided
        date_fields = ['purchase_date', 'installation_date', 'warranty_expiry', 'last_maintenance']
        for field in date_fields:
            if field in data and data[field]:
                try:
                    setattr(equipment, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                except ValueError:
                    return jsonify({'success': False, 'error': f'Invalid date format for {field}. Use YYYY-MM-DD'}), 400
        
        # Update specifications if provided
        if 'specifications' in data:
            equipment.set_specifications(data['specifications'])
        
        # Recalculate next maintenance if maintenance interval changed
        if 'maintenance_interval_days' in data or 'last_maintenance' in data:
            equipment.next_maintenance = equipment.calculate_next_maintenance()
        
        equipment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': equipment.to_dict(),
            'message': 'Equipment updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/<int:equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    """Delete equipment (soft delete)"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        
        # Soft delete
        equipment.is_active = False
        equipment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Equipment deactivated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/categories', methods=['GET'])
def get_equipment_categories():
    """Get all available equipment categories"""
    try:
        categories = [{'value': cat.value, 'name': cat.value.replace('_', ' ').title()} 
                     for cat in EquipmentCategory]
        
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/maintenance-due', methods=['GET'])
def get_maintenance_due():
    """Get equipment that needs maintenance"""
    try:
        days_ahead = request.args.get('days_ahead', default=30, type=int)
        studio_id = request.args.get('studio_id', type=int)
        
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = Equipment.query.filter(
            and_(
                Equipment.is_active == True,
                Equipment.next_maintenance <= cutoff_date
            )
        )
        
        if studio_id:
            query = query.filter(Equipment.studio_id == studio_id)
        
        equipment = query.order_by(Equipment.next_maintenance).all()
        
        result = []
        for eq in equipment:
            eq_data = eq.to_dict()
            eq_data['studio_name'] = eq.studio.name if eq.studio else None
            eq_data['days_until_maintenance'] = (eq.next_maintenance - date.today()).days if eq.next_maintenance else None
            result.append(eq_data)
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/<int:equipment_id>/usage', methods=['POST'])
def update_equipment_usage(equipment_id):
    """Update equipment usage hours and power cycles"""
    try:
        equipment = Equipment.query.get_or_404(equipment_id)
        data = request.get_json()
        
        if 'operating_hours' in data:
            equipment.operating_hours = data['operating_hours']
        
        if 'power_cycles' in data:
            equipment.power_cycles = data['power_cycles']
        
        # Recalculate next maintenance based on usage
        if equipment.usage_based_maintenance:
            equipment.next_maintenance = equipment.calculate_next_maintenance()
        
        equipment.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': equipment.to_dict(),
            'message': 'Equipment usage updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@equipment_bp.route('/equipment/stats', methods=['GET'])
def get_equipment_stats():
    """Get equipment statistics across all studios"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        
        # Base query
        base_query = Equipment.query.filter(Equipment.is_active == True)
        if studio_id:
            base_query = base_query.filter(Equipment.studio_id == studio_id)
        
        # Total counts
        total_equipment = base_query.count()
        critical_equipment = base_query.filter(Equipment.is_critical == True).count()
        
        # Equipment by category
        category_stats = db.session.query(
            Equipment.category,
            func.count(Equipment.id).label('count')
        ).filter(Equipment.is_active == True)
        
        if studio_id:
            category_stats = category_stats.filter(Equipment.studio_id == studio_id)
        
        category_stats = category_stats.group_by(Equipment.category).all()
        category_data = {cat.value: count for cat, count in category_stats}
        
        # Maintenance due
        today = date.today()
        overdue = base_query.filter(Equipment.next_maintenance < today).count()
        due_soon = base_query.filter(
            and_(
                Equipment.next_maintenance >= today,
                Equipment.next_maintenance <= today + timedelta(days=30)
            )
        ).count()
        
        # Equipment by manufacturer
        manufacturer_stats = db.session.query(
            Equipment.manufacturer,
            func.count(Equipment.id).label('count')
        ).filter(Equipment.is_active == True)
        
        if studio_id:
            manufacturer_stats = manufacturer_stats.filter(Equipment.studio_id == studio_id)
        
        manufacturer_stats = manufacturer_stats.group_by(Equipment.manufacturer).all()
        manufacturer_data = {mfg or 'Unknown': count for mfg, count in manufacturer_stats}
        
        return jsonify({
            'success': True,
            'data': {
                'total_equipment': total_equipment,
                'critical_equipment': critical_equipment,
                'by_category': category_data,
                'by_manufacturer': manufacturer_data,
                'maintenance': {
                    'overdue': overdue,
                    'due_soon': due_soon
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

