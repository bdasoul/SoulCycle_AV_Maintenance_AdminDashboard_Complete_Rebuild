"""
Scheduler system for automated maintenance alerts and tasks
"""
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from src.models.maintenance import db, Alert, MaintenanceSchedule, Equipment, Studio, Priority, TaskStatus
from sqlalchemy import and_
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceScheduler:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.scheduler_thread = None
        
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Maintenance scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Maintenance scheduler stopped")
        
    def _run_scheduler(self):
        """Run the scheduler loop"""
        # Schedule jobs
        schedule.every().day.at("09:00").do(self.daily_maintenance_check)
        schedule.every().monday.at("08:00").do(self.weekly_maintenance_summary)
        schedule.every().day.at("01:00").do(self.monthly_maintenance_report)  # Run daily but check if it's first of month
        schedule.every(6).hours.do(self.check_overdue_maintenance)
        
        logger.info("Scheduled jobs configured:")
        logger.info("- Daily maintenance check: 09:00")
        logger.info("- Weekly summary: Monday 08:00")
        logger.info("- Monthly report: 1st of each month")
        logger.info("- Overdue check: Every 6 hours")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
                
    def daily_maintenance_check(self):
        """Daily check for upcoming maintenance"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Running daily maintenance check")
                
                # Check for maintenance due in next 7 days
                cutoff_date = date.today() + timedelta(days=7)
                
                upcoming_schedules = MaintenanceSchedule.query.filter(
                    and_(
                        MaintenanceSchedule.scheduled_date >= date.today(),
                        MaintenanceSchedule.scheduled_date <= cutoff_date,
                        MaintenanceSchedule.status == TaskStatus.SCHEDULED
                    )
                ).all()
                
                alerts_created = 0
                
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
                        days_until = (schedule.scheduled_date - date.today()).days
                        
                        # Create alert with appropriate priority
                        priority = Priority.HIGH if days_until <= 2 else Priority.MEDIUM
                        
                        alert = Alert(
                            studio_id=schedule.studio_id,
                            equipment_id=schedule.equipment_id,
                            schedule_id=schedule.id,
                            alert_type='maintenance_due',
                            priority=priority,
                            title=f'Maintenance Due: {schedule.equipment.name}',
                            message=f'Maintenance for {schedule.equipment.name} at {schedule.studio.name} is due in {days_until} days. Task: {schedule.task.name}'
                        )
                        
                        db.session.add(alert)
                        alerts_created += 1
                
                db.session.commit()
                logger.info(f"Daily maintenance check completed. Created {alerts_created} alerts.")
                
            except Exception as e:
                logger.error(f"Error in daily maintenance check: {str(e)}")
                db.session.rollback()
                
    def check_overdue_maintenance(self):
        """Check for overdue maintenance every 6 hours"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Checking for overdue maintenance")
                
                overdue_schedules = MaintenanceSchedule.query.filter(
                    and_(
                        MaintenanceSchedule.scheduled_date < date.today(),
                        MaintenanceSchedule.status == TaskStatus.SCHEDULED
                    )
                ).all()
                
                alerts_created = 0
                
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
                        days_overdue = (date.today() - schedule.scheduled_date).days
                        
                        # Escalate priority based on how overdue
                        if days_overdue > 14:
                            priority = Priority.CRITICAL
                        elif days_overdue > 7:
                            priority = Priority.HIGH
                        else:
                            priority = Priority.MEDIUM
                        
                        alert = Alert(
                            studio_id=schedule.studio_id,
                            equipment_id=schedule.equipment_id,
                            schedule_id=schedule.id,
                            alert_type='maintenance_overdue',
                            priority=priority,
                            title=f'OVERDUE: {schedule.equipment.name}',
                            message=f'Maintenance for {schedule.equipment.name} at {schedule.studio.name} is {days_overdue} days overdue. Immediate attention required. Task: {schedule.task.name}'
                        )
                        
                        db.session.add(alert)
                        alerts_created += 1
                
                db.session.commit()
                logger.info(f"Overdue maintenance check completed. Created {alerts_created} alerts.")
                
            except Exception as e:
                logger.error(f"Error in overdue maintenance check: {str(e)}")
                db.session.rollback()
                
    def weekly_maintenance_summary(self):
        """Generate weekly maintenance summary alerts"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Generating weekly maintenance summary")
                
                # Get summary for each studio
                studios = Studio.query.filter(Studio.is_active == True).all()
                
                for studio in studios:
                    # Count overdue maintenance
                    overdue_count = MaintenanceSchedule.query.filter(
                        and_(
                            MaintenanceSchedule.studio_id == studio.id,
                            MaintenanceSchedule.scheduled_date < date.today(),
                            MaintenanceSchedule.status == TaskStatus.SCHEDULED
                        )
                    ).count()
                    
                    # Count upcoming maintenance (next 7 days)
                    upcoming_count = MaintenanceSchedule.query.filter(
                        and_(
                            MaintenanceSchedule.studio_id == studio.id,
                            MaintenanceSchedule.scheduled_date >= date.today(),
                            MaintenanceSchedule.scheduled_date <= date.today() + timedelta(days=7),
                            MaintenanceSchedule.status == TaskStatus.SCHEDULED
                        )
                    ).count()
                    
                    # Create weekly summary alert
                    if overdue_count > 0 or upcoming_count > 0:
                        priority = Priority.HIGH if overdue_count > 0 else Priority.MEDIUM
                        
                        message = f"Weekly maintenance summary for {studio.name}:\n"
                        if overdue_count > 0:
                            message += f"• {overdue_count} overdue maintenance tasks\n"
                        if upcoming_count > 0:
                            message += f"• {upcoming_count} maintenance tasks due this week\n"
                        message += "\nPlease review and schedule accordingly."
                        
                        alert = Alert(
                            studio_id=studio.id,
                            alert_type='weekly_summary',
                            priority=priority,
                            title=f'Weekly Maintenance Summary - {studio.name}',
                            message=message
                        )
                        
                        db.session.add(alert)
                
                db.session.commit()
                logger.info("Weekly maintenance summary completed")
                
            except Exception as e:
                logger.error(f"Error in weekly maintenance summary: {str(e)}")
                db.session.rollback()
                
    def monthly_maintenance_report(self):
        """Generate monthly maintenance report alerts"""
        # Only run on the first day of the month
        if date.today().day != 1:
            return
            
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Generating monthly maintenance report")
                
                # Get last month's data
                today = date.today()
                if today.month == 1:
                    last_month = 12
                    last_year = today.year - 1
                else:
                    last_month = today.month - 1
                    last_year = today.year
                
                # Calculate last month boundaries
                start_date = date(last_year, last_month, 1)
                if last_month == 12:
                    end_date = date(last_year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(last_year, last_month + 1, 1) - timedelta(days=1)
                
                studios = Studio.query.filter(Studio.is_active == True).all()
                
                for studio in studios:
                    # Calculate monthly statistics
                    scheduled_count = MaintenanceSchedule.query.filter(
                        and_(
                            MaintenanceSchedule.studio_id == studio.id,
                            MaintenanceSchedule.scheduled_date >= start_date,
                            MaintenanceSchedule.scheduled_date <= end_date
                        )
                    ).count()
                    
                    completed_count = MaintenanceSchedule.query.filter(
                        and_(
                            MaintenanceSchedule.studio_id == studio.id,
                            MaintenanceSchedule.scheduled_date >= start_date,
                            MaintenanceSchedule.scheduled_date <= end_date,
                            MaintenanceSchedule.status == TaskStatus.COMPLETED
                        )
                    ).count()
                    
                    completion_rate = (completed_count / scheduled_count * 100) if scheduled_count > 0 else 100
                    
                    # Count upcoming maintenance for next month
                    next_month_start = today.replace(day=1)
                    if today.month == 12:
                        next_month_end = date(today.year + 1, 1, 31)
                    else:
                        next_month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
                    
                    upcoming_count = MaintenanceSchedule.query.filter(
                        and_(
                            MaintenanceSchedule.studio_id == studio.id,
                            MaintenanceSchedule.scheduled_date >= next_month_start,
                            MaintenanceSchedule.scheduled_date <= next_month_end,
                            MaintenanceSchedule.status == TaskStatus.SCHEDULED
                        )
                    ).count()
                    
                    # Create monthly report alert
                    month_name = start_date.strftime('%B %Y')
                    
                    message = f"Monthly maintenance report for {studio.name} ({month_name}):\n\n"
                    message += f"• Scheduled maintenance: {scheduled_count}\n"
                    message += f"• Completed maintenance: {completed_count}\n"
                    message += f"• Completion rate: {completion_rate:.1f}%\n"
                    message += f"• Upcoming this month: {upcoming_count}\n\n"
                    
                    if completion_rate < 80:
                        message += "⚠️ Completion rate below target (80%). Please review scheduling and resources.\n"
                    
                    if upcoming_count > 15:
                        message += "📅 Heavy maintenance schedule ahead. Ensure adequate technician availability.\n"
                    
                    priority = Priority.MEDIUM
                    if completion_rate < 70 or upcoming_count > 20:
                        priority = Priority.HIGH
                    
                    alert = Alert(
                        studio_id=studio.id,
                        alert_type='monthly_report',
                        priority=priority,
                        title=f'Monthly Maintenance Report - {studio.name}',
                        message=message
                    )
                    
                    db.session.add(alert)
                
                db.session.commit()
                logger.info("Monthly maintenance report completed")
                
            except Exception as e:
                logger.error(f"Error in monthly maintenance report: {str(e)}")
                db.session.rollback()
                
    def check_warranty_expiration(self):
        """Check for equipment with expiring warranties"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Checking warranty expiration")
                
                # Check for warranties expiring in next 90 days
                cutoff_date = date.today() + timedelta(days=90)
                
                expiring_equipment = Equipment.query.filter(
                    and_(
                        Equipment.is_active == True,
                        Equipment.warranty_expiry.isnot(None),
                        Equipment.warranty_expiry <= cutoff_date,
                        Equipment.warranty_expiry >= date.today()
                    )
                ).all()
                
                for equipment in expiring_equipment:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter(
                        and_(
                            Alert.equipment_id == equipment.id,
                            Alert.alert_type == 'warranty_expiring',
                            Alert.is_resolved == False
                        )
                    ).first()
                    
                    if not existing_alert:
                        days_until_expiry = (equipment.warranty_expiry - date.today()).days
                        
                        priority = Priority.HIGH if days_until_expiry <= 30 else Priority.MEDIUM
                        
                        alert = Alert(
                            studio_id=equipment.studio_id,
                            equipment_id=equipment.id,
                            alert_type='warranty_expiring',
                            priority=priority,
                            title=f'Warranty Expiring: {equipment.name}',
                            message=f'Warranty for {equipment.name} at {equipment.studio.name} expires in {days_until_expiry} days ({equipment.warranty_expiry}). Consider renewal or replacement planning.'
                        )
                        
                        db.session.add(alert)
                
                db.session.commit()
                logger.info("Warranty expiration check completed")
                
            except Exception as e:
                logger.error(f"Error in warranty expiration check: {str(e)}")
                db.session.rollback()

# Global scheduler instance
maintenance_scheduler = MaintenanceScheduler()

