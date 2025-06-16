"""
Real-Time Agent Activity Monitor
Captures and streams live AI agent execution data for dynamic UI updates
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask
from flask_socketio import SocketIO, emit
import threading
import queue

class AgentActivityMonitor:
    """Monitor and stream real-time agent activity data"""
    
    def __init__(self, socketio=None):
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
        self.activity_queue = queue.Queue()
        self.active_sessions = {}
        
    def start_quote_session(self, session_id: str, shipment_info: Dict[str, Any]):
        """Initialize a new quote generation session"""
        self.active_sessions[session_id] = {
            'started_at': datetime.utcnow(),
            'shipment_info': shipment_info,
            'agents_progress': {},
            'current_stage': 'initializing',
            'status': 'active'
        }
        
        # Emit session start
        self._emit_activity(session_id, {
            'type': 'session_start',
            'message': 'Initializing AI Agent Workflow...',
            'timestamp': datetime.utcnow().isoformat(),
            'stage': 'initialization'
        })
        
    def log_agent_activity(self, session_id: str, agent_name: str, activity: str, 
                          stage: str = "processing", progress: int = 0, data: Optional[Dict] = None):
        """Log real-time agent activity"""
        
        if session_id not in self.active_sessions:
            return
            
        activity_data = {
            'type': 'agent_activity',
            'agent_name': agent_name,
            'activity': activity,
            'stage': stage or 'processing',
            'progress': progress,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'data': data or {}
        }
        
        # Update session progress
        if session_id in self.active_sessions:
            if agent_name not in self.active_sessions[session_id]['agents_progress']:
                self.active_sessions[session_id]['agents_progress'][agent_name] = []
            
            self.active_sessions[session_id]['agents_progress'][agent_name].append(activity_data)
            self.active_sessions[session_id]['current_stage'] = stage or 'processing'
        
        # Emit to connected clients
        self._emit_activity(session_id, activity_data)
        
        self.logger.info(f"Agent activity logged: {agent_name} - {activity}")
        
    def log_agent_reasoning(self, session_id: str, agent_name: str, reasoning: Dict[str, Any]):
        """Log detailed agent reasoning process"""
        
        reasoning_data = {
            'type': 'agent_reasoning',
            'agent_name': agent_name,
            'reasoning': reasoning,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id
        }
        
        self._emit_activity(session_id, reasoning_data)
        
    def log_cost_calculation(self, session_id: str, cost_breakdown: Dict[str, Any]):
        """Log real-time cost calculations"""
        
        cost_data = {
            'type': 'cost_calculation',
            'cost_breakdown': cost_breakdown,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id
        }
        
        self._emit_activity(session_id, cost_data)
        
    def complete_quote_session(self, session_id: str, final_quote: str, success: bool = True):
        """Mark quote session as complete"""
        
        if session_id not in self.active_sessions:
            return
            
        self.active_sessions[session_id]['status'] = 'completed' if success else 'failed'
        self.active_sessions[session_id]['completed_at'] = datetime.utcnow()
        
        completion_data = {
            'type': 'session_complete',
            'success': success,
            'final_quote': final_quote if success else None,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'duration': (datetime.utcnow() - self.active_sessions[session_id]['started_at']).total_seconds()
        }
        
        self._emit_activity(session_id, completion_data)
        
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get complete session activity summary"""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
            
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'started_at': session['started_at'].isoformat(),
            'status': session['status'],
            'current_stage': session['current_stage'],
            'agents_progress': session['agents_progress'],
            'shipment_info': session['shipment_info'],
            'duration': (datetime.utcnow() - session['started_at']).total_seconds()
        }
        
    def _emit_activity(self, session_id: str, data: Dict[str, Any]):
        """Emit activity data to connected clients"""
        
        if self.socketio:
            self.socketio.emit('agent_activity', data, room=session_id)
        else:
            # Store for polling if no WebSocket
            self.activity_queue.put((session_id, data))
            
    def get_queued_activities(self, session_id: str) -> List[Dict[str, Any]]:
        """Get queued activities for polling-based clients"""
        
        activities = []
        temp_queue = queue.Queue()
        
        while not self.activity_queue.empty():
            try:
                queued_session_id, data = self.activity_queue.get_nowait()
                if queued_session_id == session_id:
                    activities.append(data)
                else:
                    temp_queue.put((queued_session_id, data))
            except queue.Empty:
                break
                
        # Put back non-matching items
        while not temp_queue.empty():
            self.activity_queue.put(temp_queue.get())
            
        return activities

class CrewAIMonitoringWrapper:
    """Wrapper for CrewAI execution with real-time monitoring"""
    
    def __init__(self, activity_monitor: AgentActivityMonitor):
        self.monitor = activity_monitor
        self.logger = logging.getLogger(__name__)
        
    def execute_with_monitoring(self, crew, session_id: str, shipment_info: Dict[str, Any]):
        """Execute CrewAI crew with real-time monitoring"""
        
        try:
            # Monitor crew initialization
            self.monitor.log_agent_activity(
                session_id, 
                'System', 
                'Initializing CrewAI multi-agent system...', 
                'initialization',
                10
            )
            
            # Monitor individual agents
            for i, agent in enumerate(crew.agents):
                agent_name = getattr(agent, 'role', f'Agent {i+1}')
                self.monitor.log_agent_activity(
                    session_id,
                    agent_name,
                    f'Agent {agent_name} initialized and ready',
                    'initialization',
                    20 + (i * 10)
                )
                
            # Monitor task execution
            self.monitor.log_agent_activity(
                session_id,
                'System',
                'Starting sequential task execution...',
                'execution',
                60
            )
            
            # Execute the crew
            result = crew.kickoff()
            
            # Monitor completion
            self.monitor.log_agent_activity(
                session_id,
                'System',
                'All agents completed their tasks successfully',
                'completion',
                100
            )
            
            return result
            
        except Exception as e:
            self.monitor.log_agent_activity(
                session_id,
                'System',
                f'Error during execution: {str(e)}',
                'error',
                0
            )
            raise e

# Global monitor instance
agent_monitor = AgentActivityMonitor()