"""
External Agent Connector - Demonstrates cross-framework agent communication
Simulates external agents from different frameworks connecting to TransPak A2A system
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
import aiohttp
from a2a_protocol import (
    AgentCard, AgentCapability, AgentFramework, SkillCategory, 
    CommunicationMode, agent_registry, A2AMessage
)

logger = logging.getLogger(__name__)

class ExternalPricingAgent:
    """Simulates an external pricing validation agent from a different framework"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.agent_id = "external_pricing_validator"
        self.base_url = base_url
        self.capabilities = [
            AgentCapability(
                skill_id="validate_pricing",
                name="Price Validation",
                description="Validate quote pricing against market rates and historical data",
                category=SkillCategory.VALIDATION,
                input_types=["quote_data", "market_data"],
                output_types=["validation_result"],
                parameters={
                    "required": ["quote_data"],
                    "optional": ["market_context", "validation_threshold"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT]
            ),
            AgentCapability(
                skill_id="market_analysis",
                name="Market Rate Analysis",
                description="Analyze current market rates for shipping and packaging services",
                category=SkillCategory.ANALYSIS,
                input_types=["region_data", "service_type"],
                output_types=["market_analysis"],
                parameters={
                    "required": ["region", "service_type"],
                    "optional": ["time_frame", "competitor_data"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT, CommunicationMode.MEDIA]
            )
        ]
        
    def create_agent_card(self) -> AgentCard:
        """Create agent card for external pricing agent"""
        return AgentCard(
            agent_id=self.agent_id,
            name="External Pricing Validation Agent",
            framework=AgentFramework.EXTERNAL,
            version="2.1.0",
            description="Independent pricing validation agent specializing in freight and packaging cost verification",
            capabilities=self.capabilities,
            endpoints={
                "message": f"{self.base_url}/api/v1/external/pricing/message",
                "skill_query": f"{self.base_url}/api/v1/external/pricing/skills",
                "validate": f"{self.base_url}/api/v1/external/pricing/validate"
            },
            auth_schemes=["bearer", "api_key"],
            credentials={"token": "ext_pricing_token_123"},
            metadata={
                "provider": "ThirdParty Logistics Validator",
                "certification": "ISO 9001:2015",
                "coverage_regions": ["North America", "Europe"],
                "data_sources": ["market_feeds", "historical_data", "competitor_analysis"]
            }
        )

    async def validate_quote_pricing(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quote pricing against market standards"""
        try:
            # Simulate external pricing validation logic
            total_cost = quote_data.get('total_cost', 0)
            cost_breakdown = quote_data.get('breakdown', {})
            
            # Analyze each cost component
            validation_results = {}
            
            # Packaging costs validation
            packaging_cost = cost_breakdown.get('packaging_materials', 0) + cost_breakdown.get('packaging_labor', 0)
            packaging_market_avg = packaging_cost * 0.95  # Simulate market comparison
            packaging_variance = abs(packaging_cost - packaging_market_avg) / packaging_market_avg
            
            validation_results['packaging'] = {
                'quoted_cost': packaging_cost,
                'market_average': packaging_market_avg,
                'variance_percentage': packaging_variance * 100,
                'status': 'within_range' if packaging_variance < 0.15 else 'outside_range',
                'recommendation': 'Pricing aligns with market standards' if packaging_variance < 0.15 else 'Consider market adjustment'
            }
            
            # Freight costs validation
            freight_cost = cost_breakdown.get('freight_base', 0) + cost_breakdown.get('fuel_surcharge', 0)
            freight_market_avg = freight_cost * 1.02  # Simulate market comparison
            freight_variance = abs(freight_cost - freight_market_avg) / freight_market_avg
            
            validation_results['freight'] = {
                'quoted_cost': freight_cost,
                'market_average': freight_market_avg,
                'variance_percentage': freight_variance * 100,
                'status': 'within_range' if freight_variance < 0.12 else 'outside_range',
                'recommendation': 'Competitive freight pricing' if freight_variance < 0.12 else 'Review carrier rates'
            }
            
            # Overall validation
            overall_variance = abs(total_cost - (packaging_market_avg + freight_market_avg)) / total_cost
            
            return {
                'success': True,
                'validation_id': f"VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'quote_id': quote_data.get('quote_id', 'unknown'),
                'overall_status': 'approved' if overall_variance < 0.15 else 'review_required',
                'confidence_score': max(0.6, 1.0 - overall_variance),
                'component_validations': validation_results,
                'market_position': 'competitive' if overall_variance < 0.1 else 'premium' if total_cost > (packaging_market_avg + freight_market_avg) else 'discount',
                'recommendations': self._generate_pricing_recommendations(validation_results),
                'validation_timestamp': datetime.utcnow().isoformat(),
                'validator_agent': self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Pricing validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': datetime.utcnow().isoformat()
            }

    def _generate_pricing_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate pricing recommendations based on validation results"""
        recommendations = []
        
        for component, results in validation_results.items():
            if results['status'] == 'outside_range':
                if results['variance_percentage'] > 15:
                    recommendations.append(f"Consider adjusting {component} pricing - {results['variance_percentage']:.1f}% variance from market")
                    
        if not recommendations:
            recommendations.append("Pricing is aligned with current market rates")
            
        return recommendations

class ExternalComplianceAgent:
    """Simulates an external regulatory compliance agent"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.agent_id = "external_compliance_checker"
        self.base_url = base_url
        self.capabilities = [
            AgentCapability(
                skill_id="check_regulations",
                name="Regulatory Compliance Check",
                description="Verify shipment compliance with international and domestic regulations",
                category=SkillCategory.VALIDATION,
                input_types=["shipment_data", "route_data"],
                output_types=["compliance_report"],
                parameters={
                    "required": ["origin", "destination", "item_description"],
                    "optional": ["customs_info", "hazmat_details"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.TEXT, CommunicationMode.FILE]
            ),
            AgentCapability(
                skill_id="generate_documentation",
                name="Compliance Documentation",
                description="Generate required shipping and customs documentation",
                category=SkillCategory.GENERATION,
                input_types=["compliance_report", "shipment_details"],
                output_types=["documentation_package"],
                parameters={
                    "required": ["compliance_report"],
                    "optional": ["format_preferences"]
                },
                supported_modes=[CommunicationMode.JSON, CommunicationMode.FILE]
            )
        ]

    def create_agent_card(self) -> AgentCard:
        """Create agent card for external compliance agent"""
        return AgentCard(
            agent_id=self.agent_id,
            name="External Compliance Verification Agent",
            framework=AgentFramework.EXTERNAL,
            version="3.0.1",
            description="Specialized regulatory compliance agent for international shipping verification",
            capabilities=self.capabilities,
            endpoints={
                "message": f"{self.base_url}/api/v1/external/compliance/message",
                "skill_query": f"{self.base_url}/api/v1/external/compliance/skills",
                "check": f"{self.base_url}/api/v1/external/compliance/check"
            },
            auth_schemes=["bearer", "oauth2"],
            credentials={"token": "ext_compliance_token_456"},
            metadata={
                "provider": "Global Trade Compliance Solutions",
                "certifications": ["C-TPAT", "AEO", "IATA"],
                "regulatory_databases": ["CBP", "ITAR", "EAR", "CITES"],
                "coverage": "Global"
            }
        )

    async def check_shipment_compliance(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check shipment compliance with regulations"""
        try:
            origin = shipment_data.get('origin', '')
            destination = shipment_data.get('destination', '')
            item_description = shipment_data.get('item_description', '')
            
            compliance_checks = {
                'customs_classification': self._check_customs_classification(item_description),
                'export_controls': self._check_export_controls(item_description, origin, destination),
                'documentation_requirements': self._check_documentation_requirements(origin, destination),
                'restricted_items': self._check_restricted_items(item_description),
                'packaging_requirements': self._check_packaging_requirements(item_description)
            }
            
            # Calculate overall compliance status
            all_passed = all(check.get('status') == 'compliant' for check in compliance_checks.values())
            has_warnings = any(check.get('warnings') for check in compliance_checks.values())
            
            overall_status = 'compliant' if all_passed else 'requires_attention'
            if has_warnings and all_passed:
                overall_status = 'compliant_with_warnings'
                
            return {
                'success': True,
                'compliance_id': f"COMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'overall_status': overall_status,
                'checks_performed': compliance_checks,
                'required_documentation': self._get_required_documentation(origin, destination, item_description),
                'recommendations': self._generate_compliance_recommendations(compliance_checks),
                'compliance_timestamp': datetime.utcnow().isoformat(),
                'validator_agent': self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'compliance_timestamp': datetime.utcnow().isoformat()
            }

    def _check_customs_classification(self, item_description: str) -> Dict[str, Any]:
        """Check customs classification requirements"""
        # Simulate HS code classification
        return {
            'status': 'compliant',
            'hs_code': '8471.30.01',
            'classification': 'Electronic equipment',
            'duty_rate': '0%',
            'notes': 'Standard electronic equipment classification'
        }

    def _check_export_controls(self, item_description: str, origin: str, destination: str) -> Dict[str, Any]:
        """Check export control regulations"""
        return {
            'status': 'compliant',
            'export_license_required': False,
            'controlled_items': [],
            'notes': 'No export controls applicable for this shipment'
        }

    def _check_documentation_requirements(self, origin: str, destination: str) -> Dict[str, Any]:
        """Check required documentation"""
        return {
            'status': 'compliant',
            'required_documents': ['commercial_invoice', 'packing_list', 'bill_of_lading'],
            'optional_documents': ['certificate_of_origin'],
            'notes': 'Standard documentation package required'
        }

    def _check_restricted_items(self, item_description: str) -> Dict[str, Any]:
        """Check for restricted items"""
        return {
            'status': 'compliant',
            'restrictions': [],
            'prohibitions': [],
            'notes': 'No restrictions identified'
        }

    def _check_packaging_requirements(self, item_description: str) -> Dict[str, Any]:
        """Check packaging requirements"""
        return {
            'status': 'compliant',
            'special_requirements': [],
            'marking_requirements': ['fragile', 'this_side_up'],
            'notes': 'Standard packaging requirements apply'
        }

    def _get_required_documentation(self, origin: str, destination: str, item_description: str) -> List[str]:
        """Get list of required documentation"""
        return [
            'Commercial Invoice',
            'Packing List', 
            'Bill of Lading',
            'Export Declaration (if applicable)'
        ]

    def _generate_compliance_recommendations(self, compliance_checks: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        for check_name, check_result in compliance_checks.items():
            if check_result.get('status') != 'compliant':
                recommendations.append(f"Address {check_name} requirements before shipping")
                
        if not recommendations:
            recommendations.append("All compliance checks passed - shipment ready for processing")
            
        return recommendations

class CrossFrameworkOrchestrator:
    """Orchestrates communication between TransPak agents and external agents"""
    
    def __init__(self):
        self.external_agents = {}
        self.register_external_agents()
        
    def register_external_agents(self):
        """Register external agents in the A2A registry"""
        # Create and register external pricing agent
        pricing_agent = ExternalPricingAgent()
        pricing_card = pricing_agent.create_agent_card()
        agent_registry.register_agent(pricing_card)
        self.external_agents['pricing'] = pricing_agent
        
        # Create and register external compliance agent
        compliance_agent = ExternalComplianceAgent()
        compliance_card = compliance_agent.create_agent_card()
        agent_registry.register_agent(compliance_card)
        self.external_agents['compliance'] = compliance_agent
        
        logger.info(f"Registered {len(self.external_agents)} external agents")

    async def execute_enhanced_workflow_with_external_validation(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced workflow including external agent validation"""
        try:
            # Import the A2A integration
            from a2a_agent_adapters import transpak_a2a
            
            # Step 1: Execute standard TransPak workflow
            logger.info("Starting enhanced workflow with external validation")
            transpak_result = await transpak_a2a.execute_cross_framework_workflow(shipment_data)
            
            if not transpak_result.get('success'):
                return transpak_result
                
            # Step 2: External pricing validation
            quote_data = transpak_result['results']['final_quote']['result']
            pricing_validation = await self.external_agents['pricing'].validate_quote_pricing(quote_data)
            
            # Step 3: External compliance check
            compliance_check = await self.external_agents['compliance'].check_shipment_compliance(shipment_data)
            
            # Step 4: Consolidate results
            enhanced_result = {
                'success': True,
                'workflow_type': 'enhanced_with_external_validation',
                'transpak_workflow': transpak_result,
                'external_validations': {
                    'pricing_validation': pricing_validation,
                    'compliance_check': compliance_check
                },
                'final_status': self._determine_final_status(transpak_result, pricing_validation, compliance_check),
                'recommendations': self._consolidate_recommendations(pricing_validation, compliance_check),
                'total_processing_time': transpak_result.get('total_processing_time', 0) + 3.2,  # Add external processing time
                'completion_timestamp': datetime.utcnow().isoformat()
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced workflow failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'workflow_type': 'enhanced_with_external_validation'
            }

    def _determine_final_status(self, transpak_result: Dict[str, Any], 
                               pricing_validation: Dict[str, Any], 
                               compliance_check: Dict[str, Any]) -> str:
        """Determine final workflow status based on all validations"""
        if not transpak_result.get('success'):
            return 'failed'
            
        pricing_status = pricing_validation.get('overall_status', 'unknown')
        compliance_status = compliance_check.get('overall_status', 'unknown')
        
        if pricing_status == 'approved' and compliance_status == 'compliant':
            return 'fully_approved'
        elif pricing_status in ['approved', 'review_required'] and compliance_status in ['compliant', 'compliant_with_warnings']:
            return 'approved_with_conditions'
        else:
            return 'requires_review'

    def _consolidate_recommendations(self, pricing_validation: Dict[str, Any], 
                                   compliance_check: Dict[str, Any]) -> List[str]:
        """Consolidate recommendations from all validations"""
        recommendations = []
        
        # Add pricing recommendations
        pricing_recs = pricing_validation.get('recommendations', [])
        recommendations.extend([f"Pricing: {rec}" for rec in pricing_recs])
        
        # Add compliance recommendations
        compliance_recs = compliance_check.get('recommendations', [])
        recommendations.extend([f"Compliance: {rec}" for rec in compliance_recs])
        
        return recommendations

# Global orchestrator instance
cross_framework_orchestrator = CrossFrameworkOrchestrator()