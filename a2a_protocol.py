"""
Agent2Agent (A2A) Protocol Implementation
Following Google A2A MCP Standards for cross-framework agent communication
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AgentFramework(Enum):
    """Supported agent frameworks"""
    CREWAI = "crewai"
    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    CUSTOM = "custom"
    EXTERNAL = "external"

class CommunicationMode(Enum):
    """Agent communication modalities"""
    TEXT = "text"
    JSON = "json"
    FORM = "form"
    MEDIA = "media"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"

class SkillCategory(Enum):
    """Agent skill categories"""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    PROCESSING = "processing"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    COMMUNICATION = "communication"

@dataclass
class AgentCapability:
    """Individual agent capability definition"""
    skill_id: str
    name: str
    description: str
    category: SkillCategory
    input_types: List[str]
    output_types: List[str]
    parameters: Dict[str, Any]
    version: str = "1.0"
    supported_modes: Optional[List[CommunicationMode]] = None

    def __post_init__(self):
        if self.supported_modes is None:
            self.supported_modes = [CommunicationMode.TEXT, CommunicationMode.JSON]

@dataclass
class AgentCard:
    """
    Standardized Agent Card following A2A protocol
    Contains agent discovery and connection information
    """
    agent_id: str
    name: str
    framework: AgentFramework
    version: str
    description: str
    capabilities: List[AgentCapability]
    endpoints: Dict[str, str]
    auth_schemes: List[str]
    credentials: Optional[Dict[str, Any]] = None
    status: str = "active"
    last_updated: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert AgentCard to dictionary for serialization"""
        return asdict(self)

    def supports_skill(self, skill_id: str) -> bool:
        """Check if agent supports a specific skill"""
        return any(cap.skill_id == skill_id for cap in self.capabilities)

    def get_capability(self, skill_id: str) -> Optional[AgentCapability]:
        """Get specific capability by skill ID"""
        for cap in self.capabilities:
            if cap.skill_id == skill_id:
                return cap
        return None

class A2AMessage:
    """A2A protocol message structure"""
    
    def __init__(self, 
                 sender_id: str,
                 receiver_id: str,
                 message_type: str,
                 payload: Dict[str, Any],
                 conversation_id: str = None,
                 message_id: str = None):
        self.message_id = message_id or str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.payload = payload
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.status = "sent"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type,
            'payload': self.payload,
            'conversation_id': self.conversation_id,
            'timestamp': self.timestamp,
            'status': self.status
        }

class AgentRegistry:
    """Central registry for agent discovery and management"""
    
    def __init__(self):
        self.agents: Dict[str, AgentCard] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # skill_id -> [agent_ids]
        
    def register_agent(self, agent_card: AgentCard) -> bool:
        """Register a new agent in the registry"""
        try:
            self.agents[agent_card.agent_id] = agent_card
            
            # Index capabilities
            for capability in agent_card.capabilities:
                if capability.skill_id not in self.capabilities_index:
                    self.capabilities_index[capability.skill_id] = []
                if agent_card.agent_id not in self.capabilities_index[capability.skill_id]:
                    self.capabilities_index[capability.skill_id].append(agent_card.agent_id)
            
            logger.info(f"Registered agent: {agent_card.name} ({agent_card.agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_card.agent_id}: {str(e)}")
            return False

    def discover_agents_by_skill(self, skill_id: str) -> List[AgentCard]:
        """Discover agents that support a specific skill"""
        agent_ids = self.capabilities_index.get(skill_id, [])
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]

    def discover_agents_by_framework(self, framework: AgentFramework) -> List[AgentCard]:
        """Discover agents by framework type"""
        return [agent for agent in self.agents.values() if agent.framework == framework]

    def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent card by ID"""
        return self.agents.get(agent_id)

    def query_capabilities(self, query: Dict[str, Any]) -> List[AgentCard]:
        """Query agents based on capability requirements"""
        matching_agents = []
        
        for agent in self.agents.values():
            if self._matches_query(agent, query):
                matching_agents.append(agent)
                
        return matching_agents

    def _matches_query(self, agent: AgentCard, query: Dict[str, Any]) -> bool:
        """Check if agent matches capability query"""
        # Basic implementation - can be enhanced
        required_skills = query.get('skills', [])
        framework = query.get('framework')
        
        if framework and agent.framework.value != framework:
            return False
            
        for skill in required_skills:
            if not agent.supports_skill(skill):
                return False
                
        return True

class A2ACommunicationProtocol:
    """A2A communication protocol implementation"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry
        self.message_handlers: Dict[str, callable] = {}
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
    def register_message_handler(self, message_type: str, handler: callable):
        """Register handler for specific message types"""
        self.message_handlers[message_type] = handler

    async def send_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Send A2A message to target agent"""
        try:
            # Validate receiver exists
            receiver = self.registry.get_agent(message.receiver_id)
            if not receiver:
                return {'success': False, 'error': 'Receiver agent not found'}

            # Route message based on receiver framework
            if receiver.framework == AgentFramework.CREWAI:
                return await self._send_to_crewai_agent(message, receiver)
            elif receiver.framework == AgentFramework.EXTERNAL:
                return await self._send_to_external_agent(message, receiver)
            else:
                return await self._send_to_generic_agent(message, receiver)
                
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _send_to_crewai_agent(self, message: A2AMessage, receiver: AgentCard) -> Dict[str, Any]:
        """Send message to CrewAI-based agent"""
        # Implementation for CrewAI agent communication
        try:
            # For now, simulate successful delivery
            logger.info(f"Sending message to CrewAI agent {receiver.name}")
            return {
                'success': True,
                'message_id': message.message_id,
                'status': 'delivered',
                'response': await self._process_crewai_message(message, receiver)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _send_to_external_agent(self, message: A2AMessage, receiver: AgentCard) -> Dict[str, Any]:
        """Send message to external agent via HTTP/WebSocket"""
        import aiohttp
        
        try:
            endpoint = receiver.endpoints.get('message', receiver.endpoints.get('default'))
            if not endpoint:
                return {'success': False, 'error': 'No message endpoint configured'}

            async with aiohttp.ClientSession() as session:
                headers = {'Content-Type': 'application/json'}
                
                # Add authentication if available
                if receiver.credentials:
                    auth_type = receiver.auth_schemes[0] if receiver.auth_schemes else 'bearer'
                    if auth_type == 'bearer' and 'token' in receiver.credentials:
                        headers['Authorization'] = f"Bearer {receiver.credentials['token']}"

                async with session.post(endpoint, 
                                      json=message.to_dict(), 
                                      headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {'success': True, 'response': result}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _send_to_generic_agent(self, message: A2AMessage, receiver: AgentCard) -> Dict[str, Any]:
        """Send message to generic agent framework"""
        # Placeholder for other framework implementations
        return {'success': False, 'error': 'Framework not yet supported'}

    async def _process_crewai_message(self, message: A2AMessage, receiver: AgentCard) -> Dict[str, Any]:
        """Process message for CrewAI agent"""
        # This would integrate with our existing CrewAI agents
        message_type = message.message_type
        payload = message.payload
        
        if message_type == 'skill_query':
            return await self._handle_skill_query(receiver, payload)
        elif message_type == 'task_request':
            return await self._handle_task_request(receiver, payload)
        else:
            return {'error': 'Unknown message type'}

    async def _handle_skill_query(self, agent: AgentCard, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill query message"""
        skill_id = payload.get('skill_id')
        
        capability = agent.get_capability(skill_id)
        if capability:
            return {
                'available': True,
                'capability': asdict(capability),
                'estimated_time': '30-60 seconds',
                'cost_estimate': 'varies'
            }
        else:
            return {
                'available': False,
                'alternative_skills': [cap.skill_id for cap in agent.capabilities[:3]]
            }

    async def _handle_task_request(self, agent: AgentCard, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task execution request"""
        # This would integrate with actual agent execution
        return {
            'task_accepted': True,
            'estimated_completion': (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
            'tracking_id': str(uuid.uuid4())
        }

class DynamicSkillNegotiator:
    """Handles dynamic skill negotiation between agents"""
    
    def __init__(self, registry: AgentRegistry, protocol: A2ACommunicationProtocol):
        self.registry = registry
        self.protocol = protocol
        
    async def query_skill(self, agent_id: str, skill_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query if an agent supports a specific skill with given parameters"""
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {'available': False, 'error': 'Agent not found'}
            
        # Check if skill is in agent's capability list
        capability = agent.get_capability(skill_id)
        if not capability:
            return {
                'available': False,
                'error': 'Skill not supported',
                'alternatives': await self._suggest_alternatives(skill_id)
            }
            
        # Validate parameters against capability requirements
        if parameters:
            validation_result = self._validate_parameters(capability, parameters)
            if not validation_result['valid']:
                return {
                    'available': False,
                    'error': 'Invalid parameters',
                    'details': validation_result['errors']
                }
        
        # Send dynamic query to agent for real-time availability
        message = A2AMessage(
            sender_id="system",
            receiver_id=agent_id,
            message_type="skill_query",
            payload={
                'skill_id': skill_id,
                'parameters': parameters or {},
                'query_time': datetime.utcnow().isoformat()
            }
        )
        
        response = await self.protocol.send_message(message)
        return response.get('response', {'available': False, 'error': 'No response'})

    async def negotiate_communication_mode(self, 
                                         agent_id: str, 
                                         preferred_modes: List[CommunicationMode]) -> CommunicationMode:
        """Negotiate optimal communication mode with agent"""
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return CommunicationMode.TEXT
            
        # Find intersection of preferred modes with agent capabilities
        agent_modes = set()
        for capability in agent.capabilities:
            agent_modes.update(capability.supported_modes)
            
        preferred_set = set(preferred_modes)
        intersection = agent_modes.intersection(preferred_set)
        
        if intersection:
            # Return highest priority mode from intersection
            priority_order = [CommunicationMode.VIDEO, CommunicationMode.AUDIO, 
                            CommunicationMode.MEDIA, CommunicationMode.FORM,
                            CommunicationMode.JSON, CommunicationMode.TEXT]
            
            for mode in priority_order:
                if mode in intersection:
                    return mode
                    
        # Fallback to text if no common modes
        return CommunicationMode.TEXT

    def _validate_parameters(self, capability: AgentCapability, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters against capability requirements"""
        errors = []
        required_params = capability.parameters.get('required', [])
        
        for param in required_params:
            if param not in parameters:
                errors.append(f"Missing required parameter: {param}")
                
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    async def _suggest_alternatives(self, skill_id: str) -> List[str]:
        """Suggest alternative skills when requested skill is unavailable"""
        # Simple implementation - can be enhanced with semantic similarity
        all_agents = list(self.registry.agents.values())
        all_skills = set()
        
        for agent in all_agents:
            for capability in agent.capabilities:
                all_skills.add(capability.skill_id)
                
        # Return up to 3 alternative skills
        alternatives = [skill for skill in all_skills if skill != skill_id]
        return alternatives[:3]

# Global instances
agent_registry = AgentRegistry()
a2a_protocol = A2ACommunicationProtocol(agent_registry)
skill_negotiator = DynamicSkillNegotiator(agent_registry, a2a_protocol)