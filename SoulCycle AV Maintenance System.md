# SoulCycle AV Maintenance System

A comprehensive preventative maintenance system designed specifically for SoulCycle's audio-visual equipment across all studio locations. This system automates maintenance scheduling, tracks equipment health, generates alerts, and provides detailed reporting for studio operations.

## 🎯 Key Features

### Equipment Management
- **Categorized by System Type**: Amplifiers, Microphones, DSP Units, Power Systems
- **Usage Tracking**: Operating hours, power cycles, failure history
- **Critical Equipment Identification**: Priority-based maintenance scheduling
- **Warranty Management**: Expiration tracking and renewal alerts

### Preventative Maintenance
- **Automated Scheduling**: Based on time intervals and usage patterns
- **Task Templates**: Pre-defined maintenance procedures for each equipment type
- **Technician Assignment**: Workload distribution and skill matching
- **Progress Tracking**: Real-time status updates and completion verification

### Alert System
- **Monthly Alerts**: Automated email notifications for upcoming maintenance
- **Overdue Notifications**: Escalating priority alerts for missed maintenance
- **Critical Equipment Monitoring**: Immediate alerts for high-priority equipment
- **Weekly Summaries**: Studio-specific maintenance reports

### Reporting & Analytics
- **Printable Reports**: Professional maintenance reports for studio operations
- **Performance Metrics**: Completion rates, average task duration, cost tracking
- **Equipment Statistics**: Usage patterns, failure analysis, warranty status
- **Export Options**: CSV, HTML, and PDF formats

## 🏗️ System Architecture

### Backend (Flask)
- **RESTful API**: Complete CRUD operations for all entities
- **Database**: SQLite with SQLAlchemy ORM
- **Scheduler**: Automated background tasks for alerts and maintenance checks
- **Report Generation**: Dynamic report creation with multiple export formats

### Frontend (React)
- **Modern UI**: Professional dashboard with responsive design
- **Real-time Data**: Live updates from backend API
- **Interactive Charts**: Equipment status and maintenance metrics
- **Mobile-Friendly**: Touch-optimized interface for tablet use

### Database Schema
- **Studios**: Location management and contact information
- **Equipment**: Detailed asset tracking with specifications
- **Maintenance Tasks**: Standardized procedures and requirements
- **Schedules**: Time-based and usage-based maintenance planning
- **Alerts**: Multi-priority notification system
- **History**: Complete audit trail of all maintenance activities

## 📋 Equipment Categories & Maintenance Tasks

### Amplifiers
- **Power Supply Inspection** (Every 90 days)
  - Voltage level verification
  - Component overheating check
  - Cooling system maintenance
  - Safety compliance verification

- **Cooling System Maintenance** (Every 60 days)
  - Fan cleaning and lubrication
  - Heat sink maintenance
  - Temperature sensor calibration
  - Thermal management optimization

### Microphones
- **Wireless Battery Management** (Every 30 days)
  - Battery capacity testing
  - Charging contact cleaning
  - Performance verification
  - Replacement scheduling

- **RF Performance Testing** (Every 120 days)
  - Signal strength analysis
  - Interference detection
  - Frequency coordination
  - Antenna system optimization

### DSP Units
- **Configuration Backup** (Every 30 days)
  - Settings preservation
  - Version control
  - Restore procedure testing
  - Documentation updates

- **Performance Optimization** (Every 180 days)
  - Algorithm tuning
  - Firmware updates
  - Audio quality analysis
  - System integration testing

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- SQLite 3
- Modern web browser

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd soulcycle_maintenance

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create sample data
python create_sample_data.py

# Frontend setup
cd frontend
npm install
npm run build

# Copy frontend to Flask static directory
cd ..
cp -r frontend/dist/* src/static/

# Start the application
python src/main.py
```

### Access the Application
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api
- **Admin Dashboard**: Available through web interface

## 📊 Usage Guide

### Dashboard Overview
The main dashboard provides:
- **Equipment Statistics**: Total counts by category and status
- **Maintenance Metrics**: Completion rates and overdue tasks
- **Alert Summary**: Critical notifications requiring attention
- **Quick Actions**: Common maintenance management tasks

### Studio Management
- Add and manage studio locations
- Assign equipment to specific studios
- Track studio-specific maintenance schedules
- Generate studio performance reports

### Equipment Tracking
- Register new equipment with detailed specifications
- Monitor usage patterns and operating hours
- Track warranty status and renewal dates
- Maintain complete service history

### Maintenance Scheduling
- Create recurring maintenance schedules
- Assign tasks to qualified technicians
- Track completion status and duration
- Generate work orders and checklists

### Alert Management
- Configure notification preferences
- Set escalation rules for overdue tasks
- Manage alert priorities and recipients
- Track alert resolution status

### Report Generation
- **Maintenance Summary**: Comprehensive overview of all activities
- **Equipment Status**: Detailed asset condition reports
- **Monthly Reports**: Automated monthly summaries
- **Custom Reports**: Filtered by date, studio, or equipment type

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///src/database/app.db
SECRET_KEY=your-secret-key-here
```

### Scheduler Configuration
The system includes automated scheduling for:
- **Daily Maintenance Check**: 9:00 AM
- **Weekly Summary**: Monday 8:00 AM
- **Monthly Reports**: 1st of each month 1:00 AM
- **Overdue Check**: Every 6 hours

### Alert Settings
Configure alert priorities and escalation rules:
- **Critical**: Immediate notification for safety-critical equipment
- **High**: 24-hour response time for important equipment
- **Medium**: 72-hour response time for standard equipment
- **Low**: Weekly summary inclusion for minor items

## 📈 Maintenance Best Practices

### Equipment Categorization
- **Critical Equipment**: Cannot fail without impacting class operations
- **Important Equipment**: Backup systems and secondary components
- **Standard Equipment**: Regular maintenance items
- **Auxiliary Equipment**: Non-essential but monitored items

### Scheduling Strategies
- **Time-Based**: Regular intervals regardless of usage
- **Usage-Based**: Triggered by operating hours or power cycles
- **Condition-Based**: Responsive to equipment health indicators
- **Predictive**: AI-driven maintenance recommendations

### Technician Management
- **Skill Matching**: Assign tasks based on technician qualifications
- **Workload Balancing**: Distribute tasks evenly across team
- **Training Tracking**: Monitor certification and skill development
- **Performance Metrics**: Track completion rates and quality scores

## 🔒 Security & Compliance

### Data Protection
- **Encrypted Storage**: Sensitive data protection
- **Access Controls**: Role-based permissions
- **Audit Trails**: Complete activity logging
- **Backup Procedures**: Regular data preservation

### Compliance Standards
- **OSHA Safety**: Equipment maintenance safety protocols
- **FCC Regulations**: RF equipment compliance
- **Manufacturer Guidelines**: Warranty preservation procedures
- **Industry Standards**: Audio equipment best practices

## 📞 Support & Maintenance

### System Monitoring
- **Health Checks**: Automated system status monitoring
- **Performance Metrics**: Response time and availability tracking
- **Error Logging**: Comprehensive error capture and analysis
- **Backup Verification**: Regular backup integrity checks

### Troubleshooting
- **Common Issues**: Database connectivity, scheduler problems
- **Log Analysis**: Error pattern identification
- **Performance Optimization**: Query optimization and caching
- **Scaling Considerations**: Multi-studio deployment strategies

### Updates & Upgrades
- **Version Control**: Systematic update management
- **Testing Procedures**: Pre-deployment validation
- **Rollback Plans**: Safe update procedures
- **Feature Requests**: Enhancement prioritization

## 📋 API Documentation

### Studios Endpoint
```
GET /api/studios - List all studios
POST /api/studios - Create new studio
GET /api/studios/{id} - Get studio details
PUT /api/studios/{id} - Update studio
DELETE /api/studios/{id} - Delete studio
```

### Equipment Endpoint
```
GET /api/equipment - List all equipment
POST /api/equipment - Register new equipment
GET /api/equipment/{id} - Get equipment details
PUT /api/equipment/{id} - Update equipment
DELETE /api/equipment/{id} - Remove equipment
GET /api/equipment/stats - Get equipment statistics
```

### Maintenance Endpoint
```
GET /api/maintenance/schedules - List maintenance schedules
POST /api/maintenance/schedules - Create new schedule
GET /api/maintenance/schedules/{id} - Get schedule details
PUT /api/maintenance/schedules/{id} - Update schedule
DELETE /api/maintenance/schedules/{id} - Cancel schedule
POST /api/maintenance/complete/{id} - Mark as completed
```

### Reports Endpoint
```
GET /api/reports/maintenance-summary - Generate maintenance summary
GET /api/reports/equipment-status - Generate equipment status report
GET /api/reports/monthly-summary - Generate monthly summary
```

### Alerts Endpoint
```
GET /api/alerts - List all alerts
POST /api/alerts - Create new alert
GET /api/alerts/{id} - Get alert details
PUT /api/alerts/{id}/resolve - Resolve alert
DELETE /api/alerts/{id} - Delete alert
GET /api/alerts/stats - Get alert statistics
```

## 🎯 Future Enhancements

### Planned Features
- **Mobile App**: Native iOS/Android applications
- **IoT Integration**: Direct equipment monitoring sensors
- **AI Predictions**: Machine learning for failure prediction
- **Vendor Integration**: Direct parts ordering and scheduling
- **Advanced Analytics**: Predictive maintenance algorithms

### Scalability Improvements
- **Multi-Tenant Architecture**: Support for multiple organizations
- **Cloud Deployment**: AWS/Azure hosting options
- **Real-Time Notifications**: WebSocket-based live updates
- **Advanced Reporting**: Business intelligence dashboards

## 📄 License

This system is proprietary software developed specifically for SoulCycle's operational needs. All rights reserved.

## 👥 Development Team

Developed by the Manus AI team for SoulCycle's audio-visual maintenance operations.

For technical support or feature requests, please contact your IT administrator.

---

*This documentation is automatically generated and maintained as part of the SoulCycle AV Maintenance System.*

