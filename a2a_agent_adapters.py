"""
A2A Agent Adapters - Integration layer between existing CrewAI agents and A2A protocol
Enables cross-framework communication and dynamic skill discovery
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from agents import TransPakAgents
from crew_manager import TransPakCrewManager
from a2a_protocol import (
    AgentCard, AgentCapability, AgentFramework, SkillCategory, 
    CommunicationMode, agent_registry, a2a_protocol, skill_negotiator
)

logger = logging.getLogger(__name__)

class CrewAIAgentAdapter:
    """Adapter to expose CrewAI agents through A2A protocol"""
    
    def __init__(self, agent_name: str, crewai_agent, capabilities: List[AgentCapability]):
        self.agent_name = agent_name
        self.crewai_agent = crewai_agent
        self.agent_id = f"transpak_{agent_name.lower().replace(' ', '_')}"
        self.capabilities = capabilities
        self.active_tasks = {}
        
    def create_agent_card(self) -> AgentCard:
        """Create A2A-compliant agent card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.agent_name,
            framework=AgentFramework.CREWAI,
            version="1.0.0",
            description=getattr(self.crewai_agent, 'backstory', f'{self.agent_name} agent'),
            capabilities=self.capabilities,
            endpoints={
                'message': f'/api/v1/agents/{self.agent_id}/message',
                'skill_query': f'/api/v1/agents/{self.agent_id}/skills',
                'task': f'/api/v1/agents/{self.agent_id}/task'
            },
            auth_schemes=['bearer', 'api_key'],
            metadata={
                'framework_specific': {
                    'role': getattr(self.crewai_agent, 'role', 'Unknown'),
                    'goal': getattr(self.crewai_agent, 'goal', 'Unknown'),
                    'allow_delegation': getattr(self.crewai_agent, 'allow_delegation', False)
                }
            }
        )

    async def execute_skill(self, skill_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific skill on this agent"""
        capability = next((cap for cap in self.capabilities if cap.skill_id == skill_id), None)
        if not capability:
            return {'success': False, 'error': 'Skill not supported'}
            
        try:
            # Map A2A skill execution to CrewAI agent execution
            if skill_id == 'analyze_shipment':
                return await self._analyze_shipment(parameters)
            elif skill_id == 'design_packaging':
                return await self._design_packaging(parameters)
            elif skill_id == 'plan_logistics':
                return await self._plan_logistics(parameters)
            elif skill_id == 'consolidate_quote':
                return await self._consolidate_quote(parameters)
            else:
                return await self._generic_skill_execution(skill_id, parameters)
                
        except Exception as e:
            logger.error(f"Skill execution failed for {skill_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _analyze_shipment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shipment analysis skill"""
        shipment_data = parameters.get('shipment_data', {})
        
        # Simulate CrewAI agent processing
        analysis_result = {
            'item_classification': self._classify_item(shipment_data.get('item_description', '')),
            'risk_assessment': self._assess_risks(shipment_data),
            'requirements_validation': self._validate_requirements(shipment_data),
            'processing_time': 1.2,
            'confidence_score': 0.95
        }
        
        return {
            'success': True,
            'result': analysis_result,
            'agent_id': self.agent_id,
            'skill_id': 'analyze_shipment',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _design_packaging(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute packaging design skill"""
        shipment_data = parameters.get('shipment_data', {})
        analysis_data = parameters.get('analysis_result', {})
        
        packaging_design = {
            'crate_type': self._determine_crate_type(shipment_data, analysis_data),
            'materials': self._select_materials(shipment_data),
            'dimensions': self._calculate_crate_dimensions(shipment_data),
            'cost_estimate': self._estimate_packaging_cost(shipment_data),
            'special_requirements': self._determine_special_requirements(shipment_data)
        }
        
        return {
            'success': True,
            'result': packaging_design,
            'agent_id': self.agent_id,
            'skill_id': 'design_packaging',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _plan_logistics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logistics planning skill"""
        shipment_data = parameters.get('shipment_data', {})
        packaging_data = parameters.get('packaging_result', {})
        
        logistics_plan = {
            'transportation_mode': self._select_transport_mode(shipment_data, packaging_data),
            'route_optimization': self._optimize_route(shipment_data),
            'carrier_selection': self._select_carrier(shipment_data),
            'cost_breakdown': self._calculate_shipping_costs(shipment_data, packaging_data),
            'delivery_timeline': self._estimate_delivery_time(shipment_data)
        }
        
        return {
            'success': True,
            'result': logistics_plan,
            'agent_id': self.agent_id,
            'skill_id': 'plan_logistics',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _consolidate_quote(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quote consolidation skill"""
        analysis_result = parameters.get('analysis_result', {})
        packaging_result = parameters.get('packaging_result', {})
        logistics_result = parameters.get('logistics_result', {})
        
        consolidated_quote = {
            'quote_id': f"TQ-{datetime.now().strftime('%Y%m%d')}-{hash(str(parameters)) % 10000:04d}",
            'total_cost': self._calculate_total_cost(packaging_result, logistics_result),
            'breakdown': self._create_cost_breakdown(packaging_result, logistics_result),
            'terms': self._generate_terms_conditions(),
            'validity_period': '30 days',
            'confidence_rating': self._calculate_quote_confidence(analysis_result, packaging_result, logistics_result)
        }
        
        return {
            'success': True,
            'result': consolidated_quote,
            'agent_id': self.agent_id,
            'skill_id': 'consolidate_quote',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _generic_skill_execution(self, skill_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic skill execution for extensibility"""
        return {
            'success': True,
            'result': f"Executed {skill_id} with parameters: {json.dumps(parameters, indent=2)}",
            'agent_id': self.agent_id,
            'skill_id': skill_id,
            'timestamp': datetime.utcnow().isoformat()
        }

    # Helper methods for skill implementation
    def _classify_item(self, description: str) -> Dict[str, Any]:
        """Classify item based on description"""
        classification = {
            'category': 'general',
            'fragility_level': 'standard',
            'hazmat_classification': 'none',
            'value_category': 'medium'
        }
        
        description_lower = description.lower()
        if any(word in description_lower for word in ['electronic', 'computer', 'equipment']):
            classification['category'] = 'electronics'
            classification['fragility_level'] = 'high'
        elif any(word in description_lower for word in ['glass', 'crystal', 'fragile']):
            classification['fragility_level'] = 'extremely_high'
        elif any(word in description_lower for word in ['machinery', 'engine', 'equipment']):
            classification['category'] = 'machinery'
            classification['value_category'] = 'high'
            
        return classification

    def _assess_risks(self, shipment_data: Dict[str, Any]) -> Dict[str, str]:
        """Assess shipping risks"""
        return {
            'damage_risk': 'medium',
            'theft_risk': 'low',
            'weather_risk': 'low',
            'delay_risk': 'low',
            'regulatory_risk': 'none'
        }

    def _validate_requirements(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate shipment requirements"""
        missing_fields = []
        required_fields = ['item_description', 'dimensions', 'weight', 'origin', 'destination']
        
        for field in required_fields:
            if not shipment_data.get(field):
                missing_fields.append(field)
                
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'completeness_score': 1.0 - (len(missing_fields) / len(required_fields))
        }

    def _determine_crate_type(self, shipment_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """Determine appropriate crate type"""
        fragility = analysis_data.get('item_classification', {}).get('fragility_level', 'standard')
        
        if fragility == 'extremely_high':
            return 'custom_protective_crate'
        elif fragility == 'high':
            return 'padded_wooden_crate'
        else:
            return 'standard_wooden_crate'

    def _select_materials(self, shipment_data: Dict[str, Any]) -> List[str]:
        """Select packaging materials"""
        return ['plywood', 'foam_padding', 'moisture_barrier', 'corner_protectors']

    def _calculate_crate_dimensions(self, shipment_data: Dict[str, Any]) -> Dict[str, str]:
        """Calculate crate dimensions"""
        return {
            'length': '52 inches',
            'width': '40 inches', 
            'height': '28 inches',
            'internal_volume': '29,120 cubic inches'
        }

    def _estimate_packaging_cost(self, shipment_data: Dict[str, Any]) -> Dict[str, float]:
        """Estimate packaging costs"""
        return {
            'materials': 125.00,
            'labor': 200.00,
            'equipment': 50.00,
            'total': 375.00
        }

    def _determine_special_requirements(self, shipment_data: Dict[str, Any]) -> List[str]:
        """Determine special packaging requirements"""
        requirements = []
        special_reqs = shipment_data.get('special_requirements', '').lower()
        
        if 'temperature' in special_reqs:
            requirements.append('temperature_control')
        if 'humidity' in special_reqs:
            requirements.append('moisture_control')
        if 'orientation' in special_reqs:
            requirements.append('orientation_marking')
            
        return requirements

    def _select_transport_mode(self, shipment_data: Dict[str, Any], packaging_data: Dict[str, Any]) -> str:
        """Select transportation mode"""
        return 'ground_freight'

    def _optimize_route(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize shipping route"""
        return {
            'primary_route': f"{shipment_data.get('origin', 'Unknown')} -> {shipment_data.get('destination', 'Unknown')}",
            'distance_miles': 287,
            'estimated_transit_days': 3,
            'route_type': 'direct'
        }

    def _select_carrier(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select shipping carrier"""
        return {
            'carrier_name': 'Regional Freight Lines',
            'service_level': 'standard',
            'reliability_rating': 4.2,
            'tracking_available': True
        }

    def _calculate_shipping_costs(self, shipment_data: Dict[str, Any], packaging_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate shipping costs"""
        return {
            'base_freight': 450.00,
            'fuel_surcharge': 67.50,
            'insurance': 25.00,
            'handling': 75.00,
            'total': 617.50
        }

    def _estimate_delivery_time(self, shipment_data: Dict[str, Any]) -> Dict[str, str]:
        """Estimate delivery timeline"""
        return {
            'pickup_date': '2024-01-15',
            'estimated_delivery': '2024-01-18',
            'business_days': '3',
            'total_transit_time': '72 hours'
        }

    def _calculate_total_cost(self, packaging_result: Dict[str, Any], logistics_result: Dict[str, Any]) -> float:
        """Calculate total quote cost"""
        packaging_cost = packaging_result.get('result', {}).get('cost_estimate', {}).get('total', 0)
        shipping_cost = logistics_result.get('result', {}).get('cost_breakdown', {}).get('total', 0)
        return packaging_cost + shipping_cost

    def _create_cost_breakdown(self, packaging_result: Dict[str, Any], logistics_result: Dict[str, Any]) -> Dict[str, float]:
        """Create detailed cost breakdown"""
        packaging_costs = packaging_result.get('result', {}).get('cost_estimate', {})
        shipping_costs = logistics_result.get('result', {}).get('cost_breakdown', {})
        
        return {
            'packaging_materials': packaging_costs.get('materials', 0),
            'packaging_labor': packaging_costs.get('labor', 0),
            'packaging_equipment': packaging_costs.get('equipment', 0),
            'freight_base': shipping_costs.get('base_freight', 0),
            'fuel_surcharge': shipping_costs.get('fuel_surcharge', 0),
            'insurance': shipping_costs.get('insurance', 0),
            'handling_fees': shipping_costs.get('handling', 0)
        }

    def _generate_terms_conditions(self) -> List[str]:
        """Generate standard terms and conditions"""
        return [
            "Quote valid for 30 days from issue date",
            "Payment terms: Net 30 days",
            "Insurance coverage included up to $10,000",
            "Customer responsible for accurate item description",
            "Delivery times are estimates and not guaranteed"
        ]

    def _calculate_quote_confidence(self, analysis_result: Dict[str, Any], 
                                  packaging_result: Dict[str, Any], 
                                  logistics_result: Dict[str, Any]) -> float:
        """Calculate overall quote confidence score"""
        analysis_confidence = analysis_result.get('result', {}).get('confidence_score', 0.8)
        completeness = analysis_result.get('result', {}).get('requirements_validation', {}).get('completeness_score', 0.8)
        
        return (analysis_confidence + completeness) / 2

class TransPakA2AIntegration:
    """Main integration class for TransPak A2A implementation"""
    
    def __init__(self):
        self.agents = TransPakAgents()
        self.crew_manager = TransPakCrewManager()
        self.agent_adapters = {}
        self.initialize_a2a_agents()

    def initialize_a2a_agents(self):
        """Initialize A2A-compliant agent adapters"""
        
        # Sales Briefing Agent capabilities
        sales_capabilities = [
            AgentCapability(
                skill_id="analyze_shipment",
                name="Shipment Analysis",
                description="Analyze shipment requirements and validate information completeness",
                category=SkillCategory.ANALYSIS,
                input_types=["shipment_data"],
                output_types=["analysis_result"],
                parameters={
                    "required": ["shipment_data"],
                    "optional": ["validation_level"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT, CommunicationMode.FORM]
            ),
            AgentCapability(
                skill_id="validate_requirements",
                name="Requirements Validation",
                description="Validate completeness and accuracy of shipment requirements",
                category=SkillCategory.VALIDATION,
                input_types=["requirements_data"],
                output_types=["validation_result"],
                parameters={"required": ["requirements_data"]}
            )
        ]

        # Crating Design Agent capabilities
        crating_capabilities = [
            AgentCapability(
                skill_id="design_packaging",
                name="Packaging Design",
                description="Design optimal packaging solutions for shipments",
                category=SkillCategory.GENERATION,
                input_types=["shipment_data", "analysis_result"],
                output_types=["packaging_design"],
                parameters={
                    "required": ["shipment_data"],
                    "optional": ["cost_constraints", "material_preferences"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT, CommunicationMode.MEDIA]
            ),
            AgentCapability(
                skill_id="estimate_materials",
                name="Material Cost Estimation",
                description="Estimate material costs for packaging solutions",
                category=SkillCategory.ANALYSIS,
                input_types=["packaging_design"],
                output_types=["cost_estimate"],
                parameters={"required": ["packaging_design"]}
            )
        ]

        # Logistics Planner Agent capabilities
        logistics_capabilities = [
            AgentCapability(
                skill_id="plan_logistics",
                name="Logistics Planning",
                description="Plan optimal shipping routes and transportation methods",
                category=SkillCategory.PROCESSING,
                input_types=["shipment_data", "packaging_result"],
                output_types=["logistics_plan"],
                parameters={
                    "required": ["shipment_data"],
                    "optional": ["time_constraints", "cost_preferences"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT]
            ),
            AgentCapability(
                skill_id="optimize_route",
                name="Route Optimization",
                description="Optimize shipping routes for cost and time efficiency",
                category=SkillCategory.PROCESSING,
                input_types=["origin_destination", "constraints"],
                output_types=["optimized_route"],
                parameters={"required": ["origin", "destination"]}
            )
        ]

        # Quote Consolidator Agent capabilities
        consolidator_capabilities = [
            AgentCapability(
                skill_id="consolidate_quote",
                name="Quote Consolidation",
                description="Consolidate all components into final professional quote",
                category=SkillCategory.INTEGRATION,
                input_types=["analysis_result", "packaging_result", "logistics_result"],
                output_types=["final_quote"],
                parameters={
                    "required": ["analysis_result", "packaging_result", "logistics_result"],
                    "optional": ["formatting_preferences"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT, CommunicationMode.FILE]
            ),
            AgentCapability(
                skill_id="generate_documentation",
                name="Documentation Generation",
                description="Generate shipping and compliance documentation",
                category=SkillCategory.GENERATION,
                input_types=["quote_data", "requirements"],
                output_types=["documentation_package"],
                parameters={"required": ["quote_data"]}
            )
        ]

        # Create agent adapters
        sales_agent = self.agents.sales_briefing_agent()
        crating_agent = self.agents.crating_design_agent()
        logistics_agent = self.agents.logistics_planner_agent()
        consolidator_agent = self.agents.quote_consolidator_agent()

        self.agent_adapters = {
            'sales': CrewAIAgentAdapter("Sales Briefing Agent", sales_agent, sales_capabilities),
            'crating': CrewAIAgentAdapter("Crating Design Agent", crating_agent, crating_capabilities),
            'logistics': CrewAIAgentAdapter("Logistics Planner Agent", logistics_agent, logistics_capabilities),
            'consolidator': CrewAIAgentAdapter("Quote Consolidator Agent", consolidator_agent, consolidator_capabilities)
        }

        # Register agents in A2A registry
        for adapter in self.agent_adapters.values():
            agent_card = adapter.create_agent_card()
            agent_registry.register_agent(agent_card)
            
        logger.info(f"Registered {len(self.agent_adapters)} A2A-compliant agents")

    async def execute_cross_framework_workflow(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using A2A protocol between agents"""
        try:
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 1: Shipment Analysis
            analysis_result = await self.agent_adapters['sales'].execute_skill(
                'analyze_shipment', 
                {'shipment_data': shipment_data}
            )
            
            if not analysis_result['success']:
                return {'success': False, 'error': 'Analysis failed', 'details': analysis_result}

            # Step 2: Packaging Design
            packaging_result = await self.agent_adapters['crating'].execute_skill(
                'design_packaging',
                {
                    'shipment_data': shipment_data,
                    'analysis_result': analysis_result['result']
                }
            )
            
            if not packaging_result['success']:
                return {'success': False, 'error': 'Packaging design failed', 'details': packaging_result}

            # Step 3: Logistics Planning
            logistics_result = await self.agent_adapters['logistics'].execute_skill(
                'plan_logistics',
                {
                    'shipment_data': shipment_data,
                    'packaging_result': packaging_result['result']
                }
            )
            
            if not logistics_result['success']:
                return {'success': False, 'error': 'Logistics planning failed', 'details': logistics_result}

            # Step 4: Quote Consolidation
            quote_result = await self.agent_adapters['consolidator'].execute_skill(
                'consolidate_quote',
                {
                    'analysis_result': analysis_result,
                    'packaging_result': packaging_result,
                    'logistics_result': logistics_result
                }
            )
            
            if not quote_result['success']:
                return {'success': False, 'error': 'Quote consolidation failed', 'details': quote_result}

            return {
                'success': True,
                'workflow_id': workflow_id,
                'results': {
                    'analysis': analysis_result,
                    'packaging': packaging_result,
                    'logistics': logistics_result,
                    'final_quote': quote_result
                },
                'total_processing_time': sum([
                    analysis_result.get('result', {}).get('processing_time', 0),
                    1.5, 1.8, 2.1  # Simulated processing times
                ]),
                'workflow_completion_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cross-framework workflow failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_agent_capabilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all agent capabilities for discovery"""
        capabilities = {}
        for name, adapter in self.agent_adapters.items():
            capabilities[name] = [cap.__dict__ for cap in adapter.capabilities]
        return capabilities

    async def query_agent_skill(self, agent_name: str, skill_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query specific agent skill availability"""
        if agent_name not in self.agent_adapters:
            return {'available': False, 'error': 'Agent not found'}
            
        adapter = self.agent_adapters[agent_name]
        return await skill_negotiator.query_skill(adapter.agent_id, skill_id, parameters)

# Global A2A integration instance
transpak_a2a = TransPakA2AIntegration()