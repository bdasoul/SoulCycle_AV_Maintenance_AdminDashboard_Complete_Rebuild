# SoulCycle AV Maintenance System - Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions for deploying the SoulCycle AV Maintenance System in production environments. The system is designed to run on-premises or in cloud environments with minimal infrastructure requirements.

## 📋 System Requirements

### Minimum Hardware Requirements
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4 GB
- **Storage**: 20 GB available space
- **Network**: 100 Mbps internet connection

### Recommended Hardware Requirements
- **CPU**: 4 cores, 3.0 GHz
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 1 Gbps internet connection

### Software Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher
- **Database**: SQLite (included) or PostgreSQL for production
- **Web Server**: Nginx (recommended) or Apache

## 🚀 Production Deployment

### Option 1: Single Server Deployment

#### Step 1: Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx git

# Create application user
sudo useradd -m -s /bin/bash soulcycle
sudo usermod -aG sudo soulcycle
```

#### Step 2: Application Setup
```bash
# Switch to application user
sudo su - soulcycle

# Clone repository
git clone <repository-url> /home/soulcycle/maintenance
cd /home/soulcycle/maintenance

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies and build frontend
cd frontend
npm install
npm run build

# Copy frontend to Flask static directory
cd ..
cp -r frontend/dist/* src/static/

# Create database and sample data
python create_sample_data.py
```

#### Step 3: Production Configuration
```bash
# Create production configuration
cat > /home/soulcycle/maintenance/.env << EOF
FLASK_ENV=production
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:///home/soulcycle/maintenance/src/database/production.db
MAIL_SERVER=smtp.soulcycle.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=maintenance@soulcycle.com
MAIL_PASSWORD=your-email-password
EOF

# Set proper permissions
chmod 600 /home/soulcycle/maintenance/.env
```

#### Step 4: Systemd Service Setup
```bash
# Create systemd service file
sudo tee /etc/systemd/system/soulcycle-maintenance.service << EOF
[Unit]
Description=SoulCycle AV Maintenance System
After=network.target

[Service]
Type=simple
User=soulcycle
Group=soulcycle
WorkingDirectory=/home/soulcycle/maintenance
Environment=PATH=/home/soulcycle/maintenance/venv/bin
ExecStart=/home/soulcycle/maintenance/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable soulcycle-maintenance
sudo systemctl start soulcycle-maintenance
```

#### Step 5: Nginx Configuration
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/soulcycle-maintenance << EOF
server {
    listen 80;
    server_name maintenance.soulcycle.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/soulcycle/maintenance/src/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/soulcycle-maintenance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy frontend to Flask static directory
WORKDIR /app
RUN cp -r frontend/dist/* src/static/

# Create database
RUN python create_sample_data.py

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "src/main.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  maintenance:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
    volumes:
      - ./data:/app/src/database
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - maintenance
    restart: unless-stopped
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d maintenance.soulcycle.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Database Security
```bash
# For PostgreSQL production deployment
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE soulcycle_maintenance;
CREATE USER maintenance_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE soulcycle_maintenance TO maintenance_user;
\q
EOF

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://maintenance_user:secure_password@localhost/soulcycle_maintenance
```

## 📊 Monitoring & Logging

### Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-flask-exporter

# Add to main.py
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

### Log Configuration
```bash
# Create log directory
sudo mkdir -p /var/log/soulcycle-maintenance
sudo chown soulcycle:soulcycle /var/log/soulcycle-maintenance

# Configure log rotation
sudo tee /etc/logrotate.d/soulcycle-maintenance << EOF
/var/log/soulcycle-maintenance/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 soulcycle soulcycle
}
EOF
```

### Health Check Endpoint
Add to Flask application:
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# Create backup script
cat > /home/soulcycle/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/soulcycle/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /home/soulcycle/maintenance/src/database/production.db $BACKUP_DIR/db_backup_$DATE.db

# Backup configuration
cp /home/soulcycle/maintenance/.env $BACKUP_DIR/env_backup_$DATE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "env_backup_*" -mtime +30 -delete
EOF

chmod +x /home/soulcycle/backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/soulcycle/backup.sh
```

### Recovery Procedures
```bash
# Stop application
sudo systemctl stop soulcycle-maintenance

# Restore database
cp /home/soulcycle/backups/db_backup_YYYYMMDD_HHMMSS.db /home/soulcycle/maintenance/src/database/production.db

# Restore configuration
cp /home/soulcycle/backups/env_backup_YYYYMMDD /home/soulcycle/maintenance/.env

# Start application
sudo systemctl start soulcycle-maintenance
```

## 📧 Email Configuration

### SMTP Setup
```python
# Add to main.py
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.soulcycle.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'maintenance@soulcycle.com'
app.config['MAIL_PASSWORD'] = 'your-password'

mail = Mail(app)
```

### Alert Email Templates
```html
<!-- templates/alert_email.html -->
<!DOCTYPE html>
<html>
<head>
    <title>SoulCycle Maintenance Alert</title>
</head>
<body>
    <h2>{{ alert.title }}</h2>
    <p><strong>Studio:</strong> {{ studio.name }}</p>
    <p><strong>Equipment:</strong> {{ equipment.name }}</p>
    <p><strong>Priority:</strong> {{ alert.priority }}</p>
    <p><strong>Message:</strong> {{ alert.message }}</p>
    <p><strong>Generated:</strong> {{ alert.created_at }}</p>
</body>
</html>
```

## 🔧 Maintenance & Updates

### Application Updates
```bash
# Create update script
cat > /home/soulcycle/update.sh << EOF
#!/bin/bash
cd /home/soulcycle/maintenance

# Backup current version
cp -r . ../maintenance_backup_$(date +%Y%m%d)

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend
cd frontend
npm install
npm run build
cd ..
cp -r frontend/dist/* src/static/

# Restart service
sudo systemctl restart soulcycle-maintenance
EOF

chmod +x /home/soulcycle/update.sh
```

### Database Migrations
```python
# migrations/migrate_v1_to_v2.py
from src.models.maintenance import db

def upgrade():
    # Add new columns or tables
    db.engine.execute('ALTER TABLE equipment ADD COLUMN new_field TEXT')
    
def downgrade():
    # Remove changes if needed
    db.engine.execute('ALTER TABLE equipment DROP COLUMN new_field')
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_equipment_studio ON equipment(studio_id);
CREATE INDEX idx_schedule_date ON maintenance_schedule(scheduled_date);
CREATE INDEX idx_alerts_priority ON alerts(priority, is_resolved);
```

### Caching Configuration
```python
# Add Redis caching
from flask_caching import Cache

app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379'
cache = Cache(app)

@cache.memoize(timeout=300)
def get_equipment_stats():
    # Expensive database query
    pass
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status soulcycle-maintenance

# Check logs
sudo journalctl -u soulcycle-maintenance -f

# Check Python environment
source /home/soulcycle/maintenance/venv/bin/activate
python -c "import flask; print(flask.__version__)"
```

#### Database Connection Issues
```bash
# Check database file permissions
ls -la /home/soulcycle/maintenance/src/database/

# Test database connection
python -c "from src.models.maintenance import db; print(db.engine.execute('SELECT 1').scalar())"
```

#### Frontend Not Loading
```bash
# Check static files
ls -la /home/soulcycle/maintenance/src/static/

# Rebuild frontend
cd /home/soulcycle/maintenance/frontend
npm run build
cp -r dist/* ../src/static/
```

### Performance Issues
```bash
# Monitor system resources
htop
iotop
netstat -tulpn

# Check application logs
tail -f /var/log/soulcycle-maintenance/app.log

# Database query analysis
sqlite3 /home/soulcycle/maintenance/src/database/production.db
.timer on
.explain on
```

## 📞 Support Contacts

### Escalation Procedures
1. **Level 1**: Local IT administrator
2. **Level 2**: Regional IT support
3. **Level 3**: Development team

### Emergency Contacts
- **Critical System Failure**: [Emergency contact]
- **Security Incident**: [Security team contact]
- **Data Loss**: [Backup recovery team]

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Server meets minimum requirements
- [ ] All dependencies installed
- [ ] Database created and populated
- [ ] SSL certificates configured
- [ ] Firewall rules configured
- [ ] Backup procedures tested

### Post-Deployment
- [ ] Application starts successfully
- [ ] Web interface accessible
- [ ] API endpoints responding
- [ ] Scheduler running
- [ ] Email notifications working
- [ ] Monitoring configured
- [ ] Backup script tested

### Go-Live
- [ ] DNS records updated
- [ ] Load balancer configured (if applicable)
- [ ] Staff training completed
- [ ] Documentation distributed
- [ ] Support procedures established

---

*This deployment guide is part of the SoulCycle AV Maintenance System documentation. For technical support during deployment, contact the development team.*

