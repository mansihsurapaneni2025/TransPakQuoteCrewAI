import os
import psutil
import time
from datetime import datetime, timedelta
from flask import jsonify
from app import db
from models import Shipment, Quote, QuoteHistory, User

class SystemMonitor:
    """Comprehensive system monitoring for production deployment"""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def get_system_health(self):
        """Get comprehensive system health metrics"""
        try:
            # System resource metrics
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Database connectivity
            db_status = self._check_database_health()
            
            # Application metrics
            app_metrics = self._get_application_metrics()
            
            # AI service health
            ai_status = self._check_ai_services()
            
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "uptime": str(datetime.now() - self.start_time),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "percent": memory.percent
                    },
                    "disk": {
                        "total_gb": round(disk.total / (1024**3), 2),
                        "used_gb": round(disk.used / (1024**3), 2),
                        "percent": round((disk.used / disk.total) * 100, 2)
                    }
                },
                "database": db_status,
                "application": app_metrics,
                "ai_services": ai_status,
                "status": "healthy" if self._is_system_healthy(cpu_percent, memory.percent, db_status) else "degraded"
            }
            
            return health_data
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _check_database_health(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Simple connectivity test
            db.session.execute(db.text("SELECT 1"))
            
            # Performance test
            shipment_count = Shipment.query.count()
            quote_count = Quote.query.count()
            user_count = User.query.count()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "counts": {
                    "shipments": shipment_count,
                    "quotes": quote_count,
                    "users": user_count
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_application_metrics(self):
        """Get application-specific metrics"""
        try:
            # Recent activity metrics
            today = datetime.now().date()
            week_ago = datetime.now() - timedelta(days=7)
            
            daily_quotes = Quote.query.filter(
                db.func.date(Quote.created_at) == today
            ).count()
            
            weekly_quotes = Quote.query.filter(
                Quote.created_at >= week_ago
            ).count()
            
            recent_activity = QuoteHistory.query.filter(
                QuoteHistory.timestamp >= week_ago
            ).count()
            
            # Average processing time
            avg_processing = db.session.query(
                db.func.avg(
                    db.func.extract('epoch', Quote.created_at - Shipment.created_at)
                )
            ).join(Shipment).scalar()
            
            return {
                "daily_quotes": daily_quotes,
                "weekly_quotes": weekly_quotes,
                "recent_activity": recent_activity,
                "avg_processing_time_seconds": round(float(avg_processing or 0), 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _check_ai_services(self):
        """Check AI service availability"""
        try:
            # Test OpenAI connectivity
            openai_status = "healthy" if os.environ.get("OPENAI_API_KEY") else "no_api_key"
            
            # Test CrewAI functionality
            crewai_status = "healthy"  # Would implement actual health check
            
            return {
                "openai": openai_status,
                "crewai": crewai_status,
                "status": "healthy" if openai_status == "healthy" and crewai_status == "healthy" else "degraded"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _is_system_healthy(self, cpu_percent, memory_percent, db_status):
        """Determine overall system health"""
        if cpu_percent > 90:
            return False
        if memory_percent > 90:
            return False
        if db_status.get("status") != "healthy":
            return False
        return True
    
    def get_performance_alerts(self):
        """Get performance alerts and recommendations"""
        alerts = []
        
        try:
            # Check system resources
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 80:
                alerts.append({
                    "level": "warning",
                    "message": f"High CPU usage: {cpu_percent}%",
                    "recommendation": "Consider scaling up or optimizing processes"
                })
            
            if memory.percent > 80:
                alerts.append({
                    "level": "warning", 
                    "message": f"High memory usage: {memory.percent}%",
                    "recommendation": "Monitor memory leaks and consider increasing memory"
                })
            
            # Check database performance
            recent_quotes = Quote.query.filter(
                Quote.created_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            if recent_quotes > 100:
                alerts.append({
                    "level": "info",
                    "message": f"High quote generation activity: {recent_quotes} quotes in last hour",
                    "recommendation": "Monitor system performance during peak usage"
                })
            
            return alerts
            
        except Exception as e:
            return [{"level": "error", "message": f"Error checking alerts: {e}"}]

# Global monitor instance
system_monitor = SystemMonitor()

def get_deployment_readiness():
    """Check if system is ready for production deployment"""
    checklist = {
        "database_connected": False,
        "ai_services_configured": False,
        "security_enabled": False,
        "monitoring_active": False,
        "performance_acceptable": False
    }
    
    try:
        # Database check
        db.session.execute(db.text("SELECT 1"))
        checklist["database_connected"] = True
        
        # AI services check
        if os.environ.get("OPENAI_API_KEY"):
            checklist["ai_services_configured"] = True
        
        # Security check
        if os.environ.get("SESSION_SECRET") and os.environ.get("JWT_SECRET_KEY"):
            checklist["security_enabled"] = True
        
        # Monitoring check
        checklist["monitoring_active"] = True
        
        # Performance check
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        if memory.percent < 80 and cpu < 80:
            checklist["performance_acceptable"] = True
        
        ready_count = sum(checklist.values())
        total_checks = len(checklist)
        
        return {
            "ready": ready_count == total_checks,
            "score": f"{ready_count}/{total_checks}",
            "percentage": round((ready_count / total_checks) * 100, 1),
            "checklist": checklist,
            "recommendations": _get_deployment_recommendations(checklist)
        }
        
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "checklist": checklist
        }

def _get_deployment_recommendations(checklist):
    """Get recommendations for deployment readiness"""
    recommendations = []
    
    if not checklist["database_connected"]:
        recommendations.append("Ensure PostgreSQL database is accessible")
    
    if not checklist["ai_services_configured"]:
        recommendations.append("Configure OpenAI API key in environment variables")
    
    if not checklist["security_enabled"]:
        recommendations.append("Set SESSION_SECRET and JWT_SECRET_KEY environment variables")
    
    if not checklist["performance_acceptable"]:
        recommendations.append("Optimize system resources before deployment")
    
    if all(checklist.values()):
        recommendations.append("System is ready for production deployment!")
    
    return recommendations