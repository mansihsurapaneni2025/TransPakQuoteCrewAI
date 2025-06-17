"""
A2A API Routes - REST endpoints for Agent2Agent protocol communication
Enables external agents to discover and communicate with TransPak agents
"""

import asyncio
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

from a2a_protocol import agent_registry, a2a_protocol, skill_negotiator, A2AMessage
from a2a_agent_adapters import transpak_a2a

logger = logging.getLogger(__name__)

# Create A2A blueprint
a2a_bp = Blueprint('a2a', __name__, url_prefix='/api/v1/a2a')

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

@a2a_bp.route('/agents', methods=['GET'])
def discover_agents():
    """Agent discovery endpoint - returns all registered agents"""
    try:
        agents = []
        for agent_card in agent_registry.agents.values():
            agents.append(agent_card.to_dict())
        
        return jsonify({
            'success': True,
            'total_agents': len(agents),
            'agents': agents,
            'discovery_timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Agent discovery failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent_details(agent_id):
    """Get detailed information about a specific agent"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        return jsonify({
            'success': True,
            'agent': agent.to_dict()
        })
    except Exception as e:
        logger.error(f"Failed to get agent details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/<agent_id>/capabilities', methods=['GET'])
def get_agent_capabilities(agent_id):
    """Get agent capabilities and skills"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        capabilities = []
        for cap in agent.capabilities:
            cap_dict = {
                'skill_id': cap.skill_id,
                'name': cap.name,
                'description': cap.description,
                'category': cap.category.value,
                'input_types': cap.input_types,
                'output_types': cap.output_types,
                'parameters': cap.parameters,
                'version': cap.version,
                'supported_modes': [mode.value for mode in cap.supported_modes] if cap.supported_modes else []
            }
            capabilities.append(cap_dict)
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'capabilities': capabilities,
            'total_capabilities': len(capabilities)
        })
    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/discover', methods=['POST'])
def discover_agents_by_criteria():
    """Discover agents based on specific criteria"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No search criteria provided'}), 400
        
        matching_agents = agent_registry.query_capabilities(data)
        
        agents_data = []
        for agent in matching_agents:
            agents_data.append(agent.to_dict())
        
        return jsonify({
            'success': True,
            'criteria': data,
            'matching_agents': agents_data,
            'total_matches': len(agents_data)
        })
    except Exception as e:
        logger.error(f"Agent discovery by criteria failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/skills/<skill_id>/agents', methods=['GET'])
def discover_agents_by_skill(skill_id):
    """Discover agents that support a specific skill"""
    try:
        agents = agent_registry.discover_agents_by_skill(skill_id)
        
        agents_data = []
        for agent in agents:
            capability = agent.get_capability(skill_id)
            agent_info = {
                'agent_id': agent.agent_id,
                'name': agent.name,
                'framework': agent.framework.value,
                'capability': {
                    'skill_id': capability.skill_id,
                    'name': capability.name,
                    'description': capability.description,
                    'parameters': capability.parameters
                } if capability else None,
                'endpoints': agent.endpoints
            }
            agents_data.append(agent_info)
        
        return jsonify({
            'success': True,
            'skill_id': skill_id,
            'available_agents': agents_data,
            'total_agents': len(agents_data)
        })
    except Exception as e:
        logger.error(f"Skill-based discovery failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/<agent_id>/skills/<skill_id>/query', methods=['POST'])
@async_route
async def query_agent_skill(agent_id, skill_id):
    """Query if an agent supports a skill with specific parameters"""
    try:
        data = request.get_json() or {}
        parameters = data.get('parameters', {})
        
        result = await skill_negotiator.query_skill(agent_id, skill_id, parameters)
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'skill_id': skill_id,
            'query_result': result,
            'query_timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Skill query failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/<agent_id>/message', methods=['POST'])
@async_route
async def send_agent_message(agent_id):
    """Send A2A protocol message to an agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No message data provided'}), 400
        
        # Create A2A message
        message = A2AMessage(
            sender_id=data.get('sender_id', 'external_client'),
            receiver_id=agent_id,
            message_type=data.get('message_type', 'task_request'),
            payload=data.get('payload', {}),
            conversation_id=data.get('conversation_id')
        )
        
        # Send message through A2A protocol
        result = await a2a_protocol.send_message(message)
        
        return jsonify({
            'success': result.get('success', False),
            'message_id': message.message_id,
            'conversation_id': message.conversation_id,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Message sending failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/agents/<agent_id>/execute', methods=['POST'])
@async_route
async def execute_agent_skill(agent_id):
    """Execute a specific skill on an agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No execution data provided'}), 400
        
        skill_id = data.get('skill_id')
        parameters = data.get('parameters', {})
        
        if not skill_id:
            return jsonify({'success': False, 'error': 'skill_id is required'}), 400
        
        # Find the corresponding adapter
        adapter = None
        for name, agent_adapter in transpak_a2a.agent_adapters.items():
            if agent_adapter.agent_id == agent_id:
                adapter = agent_adapter
                break
        
        if not adapter:
            return jsonify({'success': False, 'error': 'Agent adapter not found'}), 404
        
        # Execute skill
        result = await adapter.execute_skill(skill_id, parameters)
        
        return jsonify({
            'success': result.get('success', False),
            'agent_id': agent_id,
            'skill_id': skill_id,
            'execution_result': result,
            'execution_timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Skill execution failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/workflow/execute', methods=['POST'])
@async_route
async def execute_cross_framework_workflow():
    """Execute a complete cross-framework workflow"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No workflow data provided'}), 400
        
        shipment_data = data.get('shipment_data')
        if not shipment_data:
            return jsonify({'success': False, 'error': 'shipment_data is required'}), 400
        
        # Execute cross-framework workflow
        result = await transpak_a2a.execute_cross_framework_workflow(shipment_data)
        
        return jsonify({
            'success': result.get('success', False),
            'workflow_result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Cross-framework workflow failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/communication/negotiate', methods=['POST'])
@async_route
async def negotiate_communication_mode():
    """Negotiate optimal communication mode with an agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No negotiation data provided'}), 400
        
        agent_id = data.get('agent_id')
        preferred_modes = data.get('preferred_modes', ['text'])
        
        if not agent_id:
            return jsonify({'success': False, 'error': 'agent_id is required'}), 400
        
        # Convert string modes to enum
        from a2a_protocol import CommunicationMode
        mode_enums = []
        for mode_str in preferred_modes:
            try:
                mode_enums.append(CommunicationMode(mode_str.lower()))
            except ValueError:
                continue
        
        negotiated_mode = await skill_negotiator.negotiate_communication_mode(agent_id, mode_enums)
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'requested_modes': preferred_modes,
            'negotiated_mode': negotiated_mode.value,
            'negotiation_timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Communication negotiation failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/registry/status', methods=['GET'])
def get_registry_status():
    """Get current status of the agent registry"""
    try:
        total_agents = len(agent_registry.agents)
        total_capabilities = len(agent_registry.capabilities_index)
        
        framework_counts = {}
        for agent in agent_registry.agents.values():
            framework = agent.framework.value
            framework_counts[framework] = framework_counts.get(framework, 0) + 1
        
        return jsonify({
            'success': True,
            'registry_status': {
                'total_agents': total_agents,
                'total_unique_capabilities': total_capabilities,
                'framework_distribution': framework_counts,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Registry status check failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@a2a_bp.route('/test/ping', methods=['GET'])
def ping_a2a_system():
    """Test endpoint to verify A2A system is operational"""
    return jsonify({
        'success': True,
        'message': 'A2A system is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Error handlers for A2A blueprint
@a2a_bp.errorhandler(404)
def a2a_not_found(error):
    return jsonify({
        'success': False,
        'error': 'A2A endpoint not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@a2a_bp.errorhandler(500)
def a2a_internal_error(error):
    return jsonify({
        'success': False,
        'error': 'A2A internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500