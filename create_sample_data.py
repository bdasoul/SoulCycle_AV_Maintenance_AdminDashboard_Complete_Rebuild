#!/usr/bin/env python3
"""
Script to create sample data for the SoulCycle AV Maintenance System
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.models.maintenance import (
    db, Studio, Equipment, MaintenanceTask, MaintenanceSchedule, MaintenanceHistory, Alert,
    EquipmentCategory, MaintenanceType, TaskStatus, Priority
)
from src.main import app
from datetime import datetime, date, timedelta
import random

def create_sample_data():
    """Create comprehensive sample data for demonstration"""
    with app.app_context():
        print("Creating sample data for SoulCycle AV Maintenance System...")
        
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create Studios
        studios_data = [
            {
                'name': 'SoulCycle Union Square',
                'location': 'New York, NY',
                'address': '12 E 18th St, New York, NY 10003',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10003',
                'phone': '(212) 208-1300',
                'manager_name': 'Sarah Johnson',
                'manager_email': 'sarah.johnson@soul-cycle.com',
                'capacity': 55,
                'classes_per_day': 12,
                'operating_hours': '6:00 AM - 9:00 PM'
            },
            {
                'name': 'SoulCycle West Hollywood',
                'location': 'West Hollywood, CA',
                'address': '8590 Sunset Blvd, West Hollywood, CA 90069',
                'city': 'West Hollywood',
                'state': 'CA',
                'zip_code': '90069',
                'phone': '(310) 652-7685',
                'manager_name': 'Michael Chen',
                'manager_email': 'michael.chen@soul-cycle.com',
                'capacity': 60,
                'classes_per_day': 14,
                'operating_hours': '5:30 AM - 9:30 PM'
            },
            {
                'name': 'SoulCycle Lincoln Park',
                'location': 'Chicago, IL',
                'address': '1344 N Wells St, Chicago, IL 60610',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60610',
                'phone': '(312) 654-7685',
                'manager_name': 'Emily Rodriguez',
                'manager_email': 'emily.rodriguez@soul-cycle.com',
                'capacity': 50,
                'classes_per_day': 10,
                'operating_hours': '6:00 AM - 8:30 PM'
            },
            {
                'name': 'SoulCycle Back Bay',
                'location': 'Boston, MA',
                'address': '133 Newbury St, Boston, MA 02116',
                'city': 'Boston',
                'state': 'MA',
                'zip_code': '02116',
                'phone': '(617) 262-7685',
                'manager_name': 'David Kim',
                'manager_email': 'david.kim@soul-cycle.com',
                'capacity': 45,
                'classes_per_day': 9,
                'operating_hours': '6:00 AM - 8:00 PM'
            }
        ]
        
        studios = []
        for studio_data in studios_data:
            studio = Studio(**studio_data)
            db.session.add(studio)
            studios.append(studio)
        
        db.session.commit()
        print(f"Created {len(studios)} studios")
        
        # Create Maintenance Tasks
        tasks_data = [
            # Amplifier Tasks
            {
                'name': 'Amplifier Power Supply Inspection',
                'description': 'Inspect power supply components, check for overheating, verify voltage levels',
                'category': EquipmentCategory.AMPLIFIER,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 45,
                'required_tools': ['Multimeter', 'Thermal camera', 'Screwdriver set'],
                'required_skills': ['Electrical safety', 'Power electronics'],
                'safety_requirements': 'Power isolation required. Use lockout/tagout procedures.',
                'procedure_steps': [
                    'Power down amplifier and disconnect from mains',
                    'Remove amplifier cover',
                    'Visually inspect power supply components',
                    'Check for signs of overheating or component damage',
                    'Measure voltage levels at test points',
                    'Clean dust from cooling fans and heat sinks',
                    'Reassemble and test operation'
                ],
                'frequency_days': 90
            },
            {
                'name': 'Amplifier Cooling System Maintenance',
                'description': 'Clean cooling fans, check thermal management, verify temperature sensors',
                'category': EquipmentCategory.AMPLIFIER,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 30,
                'required_tools': ['Compressed air', 'Soft brushes', 'Thermal paste'],
                'required_skills': ['Thermal management', 'Fan maintenance'],
                'safety_requirements': 'Ensure amplifier is powered down and cool before maintenance.',
                'procedure_steps': [
                    'Power down and allow cooling',
                    'Remove protective covers',
                    'Clean fans with compressed air',
                    'Check fan operation and bearing condition',
                    'Clean heat sinks and thermal interfaces',
                    'Verify temperature sensor operation',
                    'Reassemble and test'
                ],
                'frequency_days': 60
            },
            # Microphone Tasks
            {
                'name': 'Wireless Microphone Battery Check',
                'description': 'Test battery performance, check charging contacts, verify battery life',
                'category': EquipmentCategory.MICROPHONE,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 20,
                'required_tools': ['Battery tester', 'Contact cleaner', 'Replacement batteries'],
                'required_skills': ['Battery maintenance', 'RF systems'],
                'safety_requirements': 'Handle batteries according to manufacturer guidelines.',
                'procedure_steps': [
                    'Remove batteries from transmitters',
                    'Test battery capacity and voltage',
                    'Clean battery contacts',
                    'Check charging dock contacts',
                    'Test charging cycle',
                    'Replace batteries if capacity below 80%',
                    'Document battery performance'
                ],
                'frequency_days': 30
            },
            {
                'name': 'Microphone RF Performance Test',
                'description': 'Test RF signal strength, check for interference, verify frequency coordination',
                'category': EquipmentCategory.MICROPHONE,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 60,
                'required_tools': ['RF spectrum analyzer', 'Signal generator', 'Antenna analyzer'],
                'required_skills': ['RF engineering', 'Spectrum analysis'],
                'safety_requirements': 'Follow FCC regulations for RF testing.',
                'procedure_steps': [
                    'Set up RF test equipment',
                    'Scan frequency spectrum for interference',
                    'Test transmitter power output',
                    'Verify receiver sensitivity',
                    'Check antenna system performance',
                    'Document frequency coordination',
                    'Update frequency plan if needed'
                ],
                'frequency_days': 120
            },
            # DSP Tasks
            {
                'name': 'DSP Configuration Backup',
                'description': 'Backup DSP settings, verify configuration integrity, test restore procedures',
                'category': EquipmentCategory.DSP,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 25,
                'required_tools': ['Laptop', 'USB cable', 'Configuration software'],
                'required_skills': ['DSP programming', 'File management'],
                'safety_requirements': 'Ensure stable power during backup operations.',
                'procedure_steps': [
                    'Connect to DSP via configuration software',
                    'Verify current configuration status',
                    'Create full configuration backup',
                    'Test backup file integrity',
                    'Store backup in multiple locations',
                    'Document configuration version',
                    'Test restore procedure on test system'
                ],
                'frequency_days': 30
            },
            {
                'name': 'DSP Performance Optimization',
                'description': 'Analyze DSP performance, optimize processing algorithms, update firmware',
                'category': EquipmentCategory.DSP,
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'estimated_duration_minutes': 90,
                'required_tools': ['Audio analyzer', 'Configuration software', 'Test signals'],
                'required_skills': ['Audio engineering', 'DSP programming'],
                'safety_requirements': 'Perform during non-operational hours to avoid audio disruption.',
                'procedure_steps': [
                    'Analyze current DSP performance metrics',
                    'Check for firmware updates',
                    'Backup current configuration',
                    'Test audio processing quality',
                    'Optimize EQ and dynamics settings',
                    'Update firmware if available',
                    'Verify all functions after update'
                ],
                'frequency_days': 180
            }
        ]
        
        tasks = []
        for task_data in tasks_data:
            task = MaintenanceTask(
                name=task_data['name'],
                description=task_data['description'],
                category=task_data['category'],
                maintenance_type=task_data['maintenance_type'],
                estimated_duration_minutes=task_data['estimated_duration_minutes'],
                safety_requirements=task_data['safety_requirements'],
                frequency_days=task_data['frequency_days']
            )
            task.set_required_tools(task_data['required_tools'])
            task.set_required_skills(task_data['required_skills'])
            task.set_procedure_steps(task_data['procedure_steps'])
            
            db.session.add(task)
            tasks.append(task)
        
        db.session.commit()
        print(f"Created {len(tasks)} maintenance tasks")
        
        # Create Equipment
        equipment_data = [
            # Union Square Equipment
            {
                'studio_id': 1,
                'name': 'Main Amplifier Rack',
                'category': EquipmentCategory.AMPLIFIER,
                'manufacturer': 'QSC',
                'model': 'PLD4.5',
                'serial_number': 'QSC-001-2023',
                'location_in_studio': 'Equipment Room A',
                'is_critical': True,
                'operating_hours': 2800,
                'power_cycles': 450,
                'specifications': {
                    'power_output': '4 x 1250W',
                    'frequency_response': '20Hz - 20kHz',
                    'thd': '<0.02%',
                    'cooling': 'Variable speed fans'
                }
            },
            {
                'studio_id': 1,
                'name': 'Instructor Wireless Mic System',
                'category': EquipmentCategory.MICROPHONE,
                'manufacturer': 'Shure',
                'model': 'ULXD4Q',
                'serial_number': 'SHR-WL-001',
                'location_in_studio': 'Front Desk',
                'is_critical': True,
                'operating_hours': 1200,
                'power_cycles': 200,
                'specifications': {
                    'frequency_range': '470-698 MHz',
                    'channels': '4',
                    'battery_life': '12 hours',
                    'range': '300 feet'
                }
            },
            {
                'studio_id': 1,
                'name': 'Audio Processing Unit',
                'category': EquipmentCategory.DSP,
                'manufacturer': 'BSS Audio',
                'model': 'BLU-806',
                'serial_number': 'BSS-DSP-001',
                'location_in_studio': 'Equipment Room A',
                'is_critical': True,
                'operating_hours': 8760,  # Always on
                'power_cycles': 12,
                'specifications': {
                    'inputs': '8 analog',
                    'outputs': '8 analog',
                    'processing': '64-bit floating point',
                    'latency': '<1.5ms'
                }
            },
            # West Hollywood Equipment
            {
                'studio_id': 2,
                'name': 'Zone Amplifier System',
                'category': EquipmentCategory.AMPLIFIER,
                'manufacturer': 'Crown',
                'model': 'DCi 8|600N',
                'serial_number': 'CRN-002-2023',
                'location_in_studio': 'Technical Closet',
                'is_critical': True,
                'operating_hours': 3200,
                'power_cycles': 380,
                'specifications': {
                    'channels': '8',
                    'power_per_channel': '600W',
                    'network': 'BLU link',
                    'efficiency': '>90%'
                }
            },
            {
                'studio_id': 2,
                'name': 'Backup Wireless Mic',
                'category': EquipmentCategory.MICROPHONE,
                'manufacturer': 'Sennheiser',
                'model': 'EW-DX SK',
                'serial_number': 'SEN-WL-002',
                'location_in_studio': 'Instructor Station',
                'is_critical': False,
                'operating_hours': 800,
                'power_cycles': 150,
                'specifications': {
                    'frequency_range': '470-694 MHz',
                    'battery_type': 'Lithium-ion',
                    'runtime': '8 hours',
                    'encryption': 'AES-256'
                }
            }
        ]
        
        equipment_list = []
        for eq_data in equipment_data:
            # Set dates
            purchase_date = date.today() - timedelta(days=random.randint(180, 720))
            installation_date = purchase_date + timedelta(days=random.randint(7, 30))
            warranty_expiry = purchase_date + timedelta(days=random.randint(365, 1095))
            last_maintenance = date.today() - timedelta(days=random.randint(30, 90))
            
            equipment = Equipment(
                studio_id=eq_data['studio_id'],
                name=eq_data['name'],
                category=eq_data['category'],
                manufacturer=eq_data['manufacturer'],
                model=eq_data['model'],
                serial_number=eq_data['serial_number'],
                purchase_date=purchase_date,
                installation_date=installation_date,
                warranty_expiry=warranty_expiry,
                location_in_studio=eq_data['location_in_studio'],
                operating_hours=eq_data['operating_hours'],
                power_cycles=eq_data['power_cycles'],
                last_maintenance=last_maintenance,
                is_critical=eq_data['is_critical']
            )
            equipment.set_specifications(eq_data['specifications'])
            equipment.next_maintenance = equipment.calculate_next_maintenance()
            
            db.session.add(equipment)
            equipment_list.append(equipment)
        
        db.session.commit()
        print(f"Created {len(equipment_list)} equipment items")
        
        # Create Maintenance Schedules
        schedules = []
        for equipment in equipment_list:
            for task in tasks:
                if task.category == equipment.category:
                    # Create some past, current, and future schedules
                    for i in range(3):
                        schedule_date = date.today() + timedelta(days=random.randint(-60, 120))
                        
                        # Determine status based on date
                        if schedule_date < date.today() - timedelta(days=7):
                            status = TaskStatus.COMPLETED
                        elif schedule_date < date.today():
                            status = TaskStatus.OVERDUE if random.random() > 0.7 else TaskStatus.COMPLETED
                        else:
                            status = TaskStatus.SCHEDULED
                        
                        schedule = MaintenanceSchedule(
                            studio_id=equipment.studio_id,
                            equipment_id=equipment.id,
                            task_id=task.id,
                            scheduled_date=schedule_date,
                            priority=Priority.HIGH if equipment.is_critical else Priority.MEDIUM,
                            status=status,
                            assigned_technician=random.choice(['John Smith', 'Maria Garcia', 'David Wilson', 'Sarah Lee']),
                            estimated_duration_minutes=task.estimated_duration_minutes
                        )
                        
                        if status == TaskStatus.COMPLETED:
                            schedule.completed_date = datetime.combine(schedule_date, datetime.min.time()) + timedelta(hours=random.randint(8, 17))
                            schedule.actual_duration_minutes = task.estimated_duration_minutes + random.randint(-10, 20)
                            schedule.completed_by = schedule.assigned_technician
                            schedule.cost = random.randint(50, 300)
                        
                        db.session.add(schedule)
                        schedules.append(schedule)
        
        db.session.commit()
        print(f"Created {len(schedules)} maintenance schedules")
        
        # Create some Alerts
        alerts_data = [
            {
                'studio_id': 1,
                'equipment_id': 1,
                'alert_type': 'maintenance_overdue',
                'priority': Priority.HIGH,
                'title': 'Overdue Maintenance: Main Amplifier Rack',
                'message': 'Amplifier power supply inspection is 5 days overdue. Immediate attention required.'
            },
            {
                'studio_id': 2,
                'alert_type': 'weekly_summary',
                'priority': Priority.MEDIUM,
                'title': 'Weekly Maintenance Summary - West Hollywood',
                'message': 'This week: 3 completed tasks, 2 upcoming tasks, 0 overdue tasks.'
            },
            {
                'studio_id': 1,
                'equipment_id': 3,
                'alert_type': 'warranty_expiring',
                'priority': Priority.MEDIUM,
                'title': 'Warranty Expiring: Audio Processing Unit',
                'message': 'Warranty expires in 45 days. Consider renewal or replacement planning.'
            }
        ]
        
        alerts = []
        for alert_data in alerts_data:
            alert = Alert(**alert_data)
            db.session.add(alert)
            alerts.append(alert)
        
        db.session.commit()
        print(f"Created {len(alerts)} alerts")
        
        print("\nSample data creation completed successfully!")
        print(f"Total records created:")
        print(f"  - Studios: {len(studios)}")
        print(f"  - Equipment: {len(equipment_list)}")
        print(f"  - Maintenance Tasks: {len(tasks)}")
        print(f"  - Maintenance Schedules: {len(schedules)}")
        print(f"  - Alerts: {len(alerts)}")

if __name__ == '__main__':
    create_sample_data()

