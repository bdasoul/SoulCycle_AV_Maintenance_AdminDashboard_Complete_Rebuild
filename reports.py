from flask import Blueprint, request, jsonify, make_response
from src.models.maintenance import (
    db, Studio, Equipment, MaintenanceSchedule, MaintenanceHistory, 
    MaintenanceTask, Alert, EquipmentCategory, MaintenanceType, TaskStatus
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json
from io import StringIO
import csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/maintenance-summary', methods=['GET'])
def generate_maintenance_summary():
    """Generate a comprehensive maintenance summary report"""
    try:
        # Get query parameters
        studio_id = request.args.get('studio_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'json')  # json, csv, html
        
        # Default date range (last 30 days)
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Build base queries
        equipment_query = Equipment.query.filter(Equipment.is_active == True)
        schedule_query = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date >= start,
                MaintenanceSchedule.scheduled_date <= end
            )
        )
        history_query = MaintenanceHistory.query.filter(
            and_(
                MaintenanceHistory.maintenance_date >= datetime.combine(start, datetime.min.time()),
                MaintenanceHistory.maintenance_date <= datetime.combine(end, datetime.max.time())
            )
        )
        
        if studio_id:
            equipment_query = equipment_query.filter(Equipment.studio_id == studio_id)
            schedule_query = schedule_query.filter(MaintenanceSchedule.studio_id == studio_id)
            history_query = history_query.join(Equipment).filter(Equipment.studio_id == studio_id)
        
        # Gather report data
        report_data = {
            'report_info': {
                'generated_at': datetime.utcnow().isoformat(),
                'period_start': start_date,
                'period_end': end_date,
                'studio_id': studio_id,
                'studio_name': None
            },
            'summary': {},
            'equipment_stats': {},
            'maintenance_performance': {},
            'upcoming_maintenance': [],
            'overdue_maintenance': [],
            'recent_completions': [],
            'alerts_summary': {},
            'recommendations': []
        }
        
        # Studio information
        if studio_id:
            studio = Studio.query.get(studio_id)
            if studio:
                report_data['report_info']['studio_name'] = studio.name
        
        # Equipment statistics
        total_equipment = equipment_query.count()
        critical_equipment = equipment_query.filter(Equipment.is_critical == True).count()
        
        # Equipment by category
        equipment_by_category = db.session.query(
            Equipment.category,
            func.count(Equipment.id).label('count')
        ).filter(Equipment.is_active == True)
        
        if studio_id:
            equipment_by_category = equipment_by_category.filter(Equipment.studio_id == studio_id)
        
        equipment_by_category = equipment_by_category.group_by(Equipment.category).all()
        category_stats = {cat.value: count for cat, count in equipment_by_category}
        
        report_data['equipment_stats'] = {
            'total_equipment': total_equipment,
            'critical_equipment': critical_equipment,
            'by_category': category_stats
        }
        
        # Maintenance performance
        scheduled_maintenance = schedule_query.count()
        completed_maintenance = schedule_query.filter(MaintenanceSchedule.status == TaskStatus.COMPLETED).count()
        overdue_count = schedule_query.filter(
            and_(
                MaintenanceSchedule.scheduled_date < date.today(),
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        ).count()
        
        completion_rate = (completed_maintenance / scheduled_maintenance * 100) if scheduled_maintenance > 0 else 0
        
        # Average completion time
        avg_duration = db.session.query(
            func.avg(MaintenanceSchedule.actual_duration_minutes)
        ).filter(
            and_(
                MaintenanceSchedule.status == TaskStatus.COMPLETED,
                MaintenanceSchedule.actual_duration_minutes.isnot(None),
                MaintenanceSchedule.scheduled_date >= start,
                MaintenanceSchedule.scheduled_date <= end
            )
        )
        
        if studio_id:
            avg_duration = avg_duration.filter(MaintenanceSchedule.studio_id == studio_id)
        
        avg_duration = avg_duration.scalar() or 0
        
        report_data['maintenance_performance'] = {
            'scheduled_tasks': scheduled_maintenance,
            'completed_tasks': completed_maintenance,
            'overdue_tasks': overdue_count,
            'completion_rate': round(completion_rate, 2),
            'avg_duration_minutes': round(avg_duration, 2)
        }
        
        # Upcoming maintenance (next 30 days)
        upcoming_cutoff = date.today() + timedelta(days=30)
        upcoming_query = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date >= date.today(),
                MaintenanceSchedule.scheduled_date <= upcoming_cutoff,
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        )
        
        if studio_id:
            upcoming_query = upcoming_query.filter(MaintenanceSchedule.studio_id == studio_id)
        
        upcoming_schedules = upcoming_query.order_by(MaintenanceSchedule.scheduled_date).all()
        
        for schedule in upcoming_schedules:
            report_data['upcoming_maintenance'].append({
                'id': schedule.id,
                'equipment_name': schedule.equipment.name,
                'studio_name': schedule.studio.name,
                'task_name': schedule.task.name,
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'priority': schedule.priority.value,
                'days_until': (schedule.scheduled_date - date.today()).days
            })
        
        # Overdue maintenance
        overdue_query = MaintenanceSchedule.query.filter(
            and_(
                MaintenanceSchedule.scheduled_date < date.today(),
                MaintenanceSchedule.status == TaskStatus.SCHEDULED
            )
        )
        
        if studio_id:
            overdue_query = overdue_query.filter(MaintenanceSchedule.studio_id == studio_id)
        
        overdue_schedules = overdue_query.order_by(MaintenanceSchedule.scheduled_date).all()
        
        for schedule in overdue_schedules:
            report_data['overdue_maintenance'].append({
                'id': schedule.id,
                'equipment_name': schedule.equipment.name,
                'studio_name': schedule.studio.name,
                'task_name': schedule.task.name,
                'scheduled_date': schedule.scheduled_date.isoformat(),
                'priority': schedule.priority.value,
                'days_overdue': (date.today() - schedule.scheduled_date).days
            })
        
        # Recent completions
        recent_completions = schedule_query.filter(
            MaintenanceSchedule.status == TaskStatus.COMPLETED
        ).order_by(MaintenanceSchedule.completed_date.desc()).limit(10).all()
        
        for schedule in recent_completions:
            report_data['recent_completions'].append({
                'id': schedule.id,
                'equipment_name': schedule.equipment.name,
                'studio_name': schedule.studio.name,
                'task_name': schedule.task.name,
                'completed_date': schedule.completed_date.isoformat() if schedule.completed_date else None,
                'completed_by': schedule.completed_by,
                'duration_minutes': schedule.actual_duration_minutes,
                'cost': float(schedule.cost) if schedule.cost else None
            })
        
        # Alerts summary
        alert_query = Alert.query.filter(Alert.is_resolved == False)
        if studio_id:
            alert_query = alert_query.filter(Alert.studio_id == studio_id)
        
        total_alerts = alert_query.count()
        critical_alerts = alert_query.filter(Alert.priority.in_(['high', 'critical'])).count()
        
        report_data['alerts_summary'] = {
            'total_unresolved': total_alerts,
            'critical_alerts': critical_alerts
        }
        
        # Generate recommendations
        recommendations = []
        
        if overdue_count > 0:
            recommendations.append({
                'type': 'urgent',
                'title': 'Address Overdue Maintenance',
                'description': f'{overdue_count} maintenance tasks are overdue and require immediate attention.'
            })
        
        if completion_rate < 80:
            recommendations.append({
                'type': 'improvement',
                'title': 'Improve Maintenance Completion Rate',
                'description': f'Current completion rate is {completion_rate:.1f}%. Consider reviewing scheduling and resource allocation.'
            })
        
        if critical_alerts > 0:
            recommendations.append({
                'type': 'urgent',
                'title': 'Critical Alerts Require Attention',
                'description': f'{critical_alerts} critical alerts need immediate resolution.'
            })
        
        if len(upcoming_schedules) > 20:
            recommendations.append({
                'type': 'planning',
                'title': 'Heavy Maintenance Schedule Ahead',
                'description': f'{len(upcoming_schedules)} maintenance tasks scheduled in the next 30 days. Ensure adequate resources.'
            })
        
        report_data['recommendations'] = recommendations
        
        # Summary statistics
        report_data['summary'] = {
            'total_equipment': total_equipment,
            'maintenance_completion_rate': round(completion_rate, 2),
            'overdue_tasks': overdue_count,
            'upcoming_tasks': len(upcoming_schedules),
            'critical_alerts': critical_alerts,
            'avg_task_duration': round(avg_duration, 2)
        }
        
        # Return based on format
        if format_type == 'csv':
            return generate_csv_report(report_data)
        elif format_type == 'html':
            return generate_html_report(report_data)
        else:
            return jsonify({
                'success': True,
                'data': report_data
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_csv_report(report_data):
    """Generate CSV format report"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['SoulCycle AV Maintenance Report'])
    writer.writerow(['Generated:', report_data['report_info']['generated_at']])
    writer.writerow(['Period:', f"{report_data['report_info']['period_start']} to {report_data['report_info']['period_end']}"])
    writer.writerow([])
    
    # Summary
    writer.writerow(['SUMMARY'])
    for key, value in report_data['summary'].items():
        writer.writerow([key.replace('_', ' ').title(), value])
    writer.writerow([])
    
    # Overdue Maintenance
    if report_data['overdue_maintenance']:
        writer.writerow(['OVERDUE MAINTENANCE'])
        writer.writerow(['Equipment', 'Studio', 'Task', 'Scheduled Date', 'Days Overdue', 'Priority'])
        for item in report_data['overdue_maintenance']:
            writer.writerow([
                item['equipment_name'],
                item['studio_name'],
                item['task_name'],
                item['scheduled_date'],
                item['days_overdue'],
                item['priority']
            ])
        writer.writerow([])
    
    # Upcoming Maintenance
    if report_data['upcoming_maintenance']:
        writer.writerow(['UPCOMING MAINTENANCE (Next 30 Days)'])
        writer.writerow(['Equipment', 'Studio', 'Task', 'Scheduled Date', 'Days Until', 'Priority'])
        for item in report_data['upcoming_maintenance']:
            writer.writerow([
                item['equipment_name'],
                item['studio_name'],
                item['task_name'],
                item['scheduled_date'],
                item['days_until'],
                item['priority']
            ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=maintenance_report_{date.today().isoformat()}.csv'
    return response

def generate_html_report(report_data):
    """Generate HTML format report for printing"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SoulCycle AV Maintenance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ color: #f59e0b; font-size: 24px; font-weight: bold; }}
            .summary {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .section {{ margin-bottom: 30px; }}
            .section h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
            th {{ background-color: #f9fafb; font-weight: bold; }}
            .urgent {{ color: #dc2626; font-weight: bold; }}
            .warning {{ color: #d97706; }}
            .success {{ color: #059669; }}
            .recommendations {{ background: #fef3c7; padding: 15px; border-radius: 8px; }}
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">SoulCycle AV Maintenance System</div>
            <h1>Maintenance Report</h1>
            <p>Generated: {report_data['report_info']['generated_at']}</p>
            <p>Period: {report_data['report_info']['period_start']} to {report_data['report_info']['period_end']}</p>
            {f"<p>Studio: {report_data['report_info']['studio_name']}</p>" if report_data['report_info']['studio_name'] else ""}
        </div>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                <div>
                    <strong>Total Equipment:</strong> {report_data['summary']['total_equipment']}<br>
                    <strong>Completion Rate:</strong> {report_data['summary']['maintenance_completion_rate']}%
                </div>
                <div>
                    <strong>Overdue Tasks:</strong> <span class="{'urgent' if report_data['summary']['overdue_tasks'] > 0 else 'success'}">{report_data['summary']['overdue_tasks']}</span><br>
                    <strong>Upcoming Tasks:</strong> {report_data['summary']['upcoming_tasks']}
                </div>
                <div>
                    <strong>Critical Alerts:</strong> <span class="{'urgent' if report_data['summary']['critical_alerts'] > 0 else 'success'}">{report_data['summary']['critical_alerts']}</span><br>
                    <strong>Avg Task Duration:</strong> {report_data['summary']['avg_task_duration']} min
                </div>
            </div>
        </div>
    """
    
    # Overdue Maintenance Section
    if report_data['overdue_maintenance']:
        html_content += """
        <div class="section">
            <h2 class="urgent">⚠️ Overdue Maintenance (Immediate Action Required)</h2>
            <table>
                <tr>
                    <th>Equipment</th>
                    <th>Studio</th>
                    <th>Task</th>
                    <th>Scheduled Date</th>
                    <th>Days Overdue</th>
                    <th>Priority</th>
                </tr>
        """
        for item in report_data['overdue_maintenance']:
            html_content += f"""
                <tr>
                    <td>{item['equipment_name']}</td>
                    <td>{item['studio_name']}</td>
                    <td>{item['task_name']}</td>
                    <td>{item['scheduled_date']}</td>
                    <td class="urgent">{item['days_overdue']}</td>
                    <td>{item['priority'].title()}</td>
                </tr>
            """
        html_content += "</table></div>"
    
    # Upcoming Maintenance Section
    if report_data['upcoming_maintenance']:
        html_content += """
        <div class="section">
            <h2>📅 Upcoming Maintenance (Next 30 Days)</h2>
            <table>
                <tr>
                    <th>Equipment</th>
                    <th>Studio</th>
                    <th>Task</th>
                    <th>Scheduled Date</th>
                    <th>Days Until</th>
                    <th>Priority</th>
                </tr>
        """
        for item in report_data['upcoming_maintenance']:
            html_content += f"""
                <tr>
                    <td>{item['equipment_name']}</td>
                    <td>{item['studio_name']}</td>
                    <td>{item['task_name']}</td>
                    <td>{item['scheduled_date']}</td>
                    <td>{item['days_until']}</td>
                    <td>{item['priority'].title()}</td>
                </tr>
            """
        html_content += "</table></div>"
    
    # Equipment Statistics
    html_content += f"""
        <div class="section">
            <h2>📊 Equipment Statistics</h2>
            <p><strong>Total Equipment:</strong> {report_data['equipment_stats']['total_equipment']}</p>
            <p><strong>Critical Equipment:</strong> {report_data['equipment_stats']['critical_equipment']}</p>
            <h3>Equipment by Category:</h3>
            <ul>
    """
    for category, count in report_data['equipment_stats']['by_category'].items():
        html_content += f"<li>{category.replace('_', ' ').title()}: {count}</li>"
    
    html_content += "</ul></div>"
    
    # Recommendations
    if report_data['recommendations']:
        html_content += """
        <div class="section">
            <h2>💡 Recommendations</h2>
            <div class="recommendations">
        """
        for rec in report_data['recommendations']:
            icon = "🚨" if rec['type'] == 'urgent' else "📈" if rec['type'] == 'improvement' else "📋"
            html_content += f"""
                <div style="margin-bottom: 15px;">
                    <strong>{icon} {rec['title']}</strong><br>
                    {rec['description']}
                </div>
            """
        html_content += "</div></div>"
    
    html_content += """
        <div class="section" style="margin-top: 40px; text-align: center; color: #6b7280;">
            <p>This report was automatically generated by the SoulCycle AV Maintenance System</p>
            <p>For questions or support, contact your IT administrator</p>
        </div>
    </body>
    </html>
    """
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    return response

@reports_bp.route('/reports/equipment-status', methods=['GET'])
def generate_equipment_status_report():
    """Generate equipment status report"""
    try:
        studio_id = request.args.get('studio_id', type=int)
        category = request.args.get('category')
        format_type = request.args.get('format', 'json')
        
        query = Equipment.query.filter(Equipment.is_active == True)
        
        if studio_id:
            query = query.filter(Equipment.studio_id == studio_id)
        
        if category:
            try:
                cat_enum = EquipmentCategory(category)
                query = query.filter(Equipment.category == cat_enum)
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid category: {category}'}), 400
        
        equipment = query.all()
        
        report_data = {
            'report_info': {
                'generated_at': datetime.utcnow().isoformat(),
                'studio_id': studio_id,
                'category_filter': category
            },
            'equipment': []
        }
        
        for eq in equipment:
            # Calculate maintenance status
            maintenance_status = 'up_to_date'
            if eq.next_maintenance and eq.next_maintenance < date.today():
                maintenance_status = 'overdue'
            elif eq.next_maintenance and eq.next_maintenance <= date.today() + timedelta(days=30):
                maintenance_status = 'due_soon'
            
            # Get recent maintenance history
            recent_maintenance = MaintenanceHistory.query.filter_by(equipment_id=eq.id)\
                .order_by(MaintenanceHistory.maintenance_date.desc()).first()
            
            equipment_data = {
                'id': eq.id,
                'name': eq.name,
                'category': eq.category.value,
                'manufacturer': eq.manufacturer,
                'model': eq.model,
                'serial_number': eq.serial_number,
                'studio_name': eq.studio.name if eq.studio else None,
                'location_in_studio': eq.location_in_studio,
                'is_critical': eq.is_critical,
                'operating_hours': eq.operating_hours,
                'power_cycles': eq.power_cycles,
                'last_maintenance': eq.last_maintenance.isoformat() if eq.last_maintenance else None,
                'next_maintenance': eq.next_maintenance.isoformat() if eq.next_maintenance else None,
                'maintenance_status': maintenance_status,
                'failure_count': eq.failure_count,
                'warranty_expiry': eq.warranty_expiry.isoformat() if eq.warranty_expiry else None,
                'recent_maintenance': {
                    'date': recent_maintenance.maintenance_date.isoformat() if recent_maintenance else None,
                    'type': recent_maintenance.maintenance_type.value if recent_maintenance else None,
                    'technician': recent_maintenance.technician if recent_maintenance else None
                } if recent_maintenance else None
            }
            
            report_data['equipment'].append(equipment_data)
        
        if format_type == 'csv':
            return generate_equipment_csv(report_data)
        else:
            return jsonify({
                'success': True,
                'data': report_data
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_equipment_csv(report_data):
    """Generate CSV format equipment report"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['SoulCycle Equipment Status Report'])
    writer.writerow(['Generated:', report_data['report_info']['generated_at']])
    writer.writerow([])
    
    # Equipment data
    writer.writerow([
        'Equipment Name', 'Category', 'Manufacturer', 'Model', 'Serial Number',
        'Studio', 'Location', 'Critical', 'Operating Hours', 'Power Cycles',
        'Last Maintenance', 'Next Maintenance', 'Status', 'Failure Count'
    ])
    
    for eq in report_data['equipment']:
        writer.writerow([
            eq['name'],
            eq['category'],
            eq['manufacturer'] or '',
            eq['model'] or '',
            eq['serial_number'] or '',
            eq['studio_name'] or '',
            eq['location_in_studio'] or '',
            'Yes' if eq['is_critical'] else 'No',
            eq['operating_hours'],
            eq['power_cycles'],
            eq['last_maintenance'] or '',
            eq['next_maintenance'] or '',
            eq['maintenance_status'].replace('_', ' ').title(),
            eq['failure_count']
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=equipment_status_{date.today().isoformat()}.csv'
    return response

@reports_bp.route('/reports/monthly-summary', methods=['GET'])
def generate_monthly_summary():
    """Generate monthly maintenance summary for alerts"""
    try:
        month = request.args.get('month', type=int) or date.today().month
        year = request.args.get('year', type=int) or date.today().year
        
        # Calculate month boundaries
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get all studios for the summary
        studios = Studio.query.filter(Studio.is_active == True).all()
        
        monthly_data = {
            'report_info': {
                'month': month,
                'year': year,
                'period': f"{start_date.strftime('%B %Y')}",
                'generated_at': datetime.utcnow().isoformat()
            },
            'studios': []
        }
        
        for studio in studios:
            # Equipment counts
            total_equipment = Equipment.query.filter_by(studio_id=studio.id, is_active=True).count()
            critical_equipment = Equipment.query.filter_by(studio_id=studio.id, is_active=True, is_critical=True).count()
            
            # Maintenance in this month
            maintenance_completed = MaintenanceSchedule.query.filter(
                and_(
                    MaintenanceSchedule.studio_id == studio.id,
                    MaintenanceSchedule.scheduled_date >= start_date,
                    MaintenanceSchedule.scheduled_date <= end_date,
                    MaintenanceSchedule.status == TaskStatus.COMPLETED
                )
            ).count()
            
            maintenance_scheduled = MaintenanceSchedule.query.filter(
                and_(
                    MaintenanceSchedule.studio_id == studio.id,
                    MaintenanceSchedule.scheduled_date >= start_date,
                    MaintenanceSchedule.scheduled_date <= end_date
                )
            ).count()
            
            # Upcoming maintenance (next month)
            next_month_start = end_date + timedelta(days=1)
            next_month_end = next_month_start + timedelta(days=30)
            
            upcoming_maintenance = MaintenanceSchedule.query.filter(
                and_(
                    MaintenanceSchedule.studio_id == studio.id,
                    MaintenanceSchedule.scheduled_date >= next_month_start,
                    MaintenanceSchedule.scheduled_date <= next_month_end,
                    MaintenanceSchedule.status == TaskStatus.SCHEDULED
                )
            ).count()
            
            # Current overdue
            overdue_maintenance = MaintenanceSchedule.query.filter(
                and_(
                    MaintenanceSchedule.studio_id == studio.id,
                    MaintenanceSchedule.scheduled_date < date.today(),
                    MaintenanceSchedule.status == TaskStatus.SCHEDULED
                )
            ).count()
            
            studio_data = {
                'id': studio.id,
                'name': studio.name,
                'location': studio.location,
                'manager_name': studio.manager_name,
                'manager_email': studio.manager_email,
                'equipment': {
                    'total': total_equipment,
                    'critical': critical_equipment
                },
                'maintenance': {
                    'completed_this_month': maintenance_completed,
                    'scheduled_this_month': maintenance_scheduled,
                    'completion_rate': round((maintenance_completed / maintenance_scheduled * 100) if maintenance_scheduled > 0 else 100, 2),
                    'upcoming_next_month': upcoming_maintenance,
                    'currently_overdue': overdue_maintenance
                }
            }
            
            monthly_data['studios'].append(studio_data)
        
        return jsonify({
            'success': True,
            'data': monthly_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

