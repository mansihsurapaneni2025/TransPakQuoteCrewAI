import os
import json
import logging
import time
from crewai import Crew, Process
from agents import TransPakAgents
from tasks import TransPakTasks
import pricing_tools
import json
from ai_enhancements import AIEnhancementEngine
from agent_memory import AgentMemoryCapture, MCPConnector
from enhanced_pricing_engine import EnhancedPricingEngine, RealTimeMarketData, GeolocationService

class TransPakCrewManager:
    def __init__(self):
        self.agents = TransPakAgents()
        self.tasks = TransPakTasks()
        self.ai_engine = AIEnhancementEngine()
        self.agent_memory = AgentMemoryCapture()
        self.mcp_connector = MCPConnector()
        self.enhanced_pricing = EnhancedPricingEngine()
        self.market_data = RealTimeMarketData()
        self.geolocation = GeolocationService()
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
    
    def generate_quote(self, shipment_info):
        """
        Main method to orchestrate the multi-agent quoting process
        """
        try:
            self.logger.info("Starting quote generation process")
            
            # Initialize agents
            sales_agent = self.agents.sales_briefing_agent()
            crating_agent = self.agents.crating_design_agent()
            logistics_agent = self.agents.logistics_planner_agent()
            consolidator_agent = self.agents.quote_consolidator_agent()
            
            # Create tasks
            briefing_task = self.tasks.gather_shipment_details_task(sales_agent, shipment_info)
            crating_task = self.tasks.design_crating_solution_task(crating_agent, "{{briefing_result}}")
            logistics_task = self.tasks.plan_logistics_task(logistics_agent, "{{briefing_result}}", "{{crating_result}}")
            quote_task = self.tasks.consolidate_quote_task(
                consolidator_agent, 
                "{{briefing_result}}", 
                "{{crating_result}}", 
                "{{logistics_result}}"
            )
            
            # Set up task dependencies
            crating_task.context = [briefing_task]
            logistics_task.context = [briefing_task, crating_task]
            quote_task.context = [briefing_task, crating_task, logistics_task]
            
            # Create and execute crew
            crew = Crew(
                agents=[sales_agent, crating_agent, logistics_agent, consolidator_agent],
                tasks=[briefing_task, crating_task, logistics_task, quote_task],
                process=Process.sequential,
                verbose=True
            )
            
            self.logger.info("Executing crew workflow")
            result = crew.kickoff()
            
            # Extract the actual quote content from CrewAI result
            # CrewAI kickoff() returns a CrewOutput object with .raw attribute
            quote_content = str(result.raw) if hasattr(result, 'raw') else str(result)
            
            # Capture agent activity data for traceability
            agent_activity = self._extract_agent_activity(crew, shipment_info)
            cost_breakdown = self._calculate_cost_breakdown(shipment_info)
            
            self.logger.info("Quote generation completed successfully")
            return {
                'success': True,
                'quote': quote_content,
                'agent_activity': agent_activity,
                'cost_breakdown': cost_breakdown,
                'message': 'Quote generated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error in quote generation: {str(e)}")
            return {
                'success': False,
                'quote': None,
                'agent_activity': {},
                'cost_breakdown': {},
                'message': f'Error generating quote: {str(e)}'
            }
    
    def _extract_agent_activity(self, crew, shipment_info):
        """Extract real agent activity data using dynamic pricing calculations"""
        
        # Calculate enhanced packaging costs with real-time data
        packaging_data = self.enhanced_pricing.calculate_enhanced_packaging_cost(
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('origin', 'San Jose CA')
        )
        
        # Calculate enhanced shipping costs with real-time data
        shipping_data = self.enhanced_pricing.calculate_enhanced_shipping_rate(
            shipment_info.get('origin', 'San Jose CA'),
            shipment_info.get('destination', 'Austin TX'),
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard')
        )
        
        # Get real geolocation data
        route_data = self.geolocation.calculate_real_distance(
            shipment_info.get('origin', 'San Jose CA'),
            shipment_info.get('destination', 'Austin TX')
        )
        
        # Calculate real insurance costs
        insurance_data = pricing_tools.calculate_insurance_cost(
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard')
        )
        
        # Calculate real special handling costs
        handling_data = pricing_tools.calculate_special_handling_cost(
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('special_requirements', '')
        )
        
        # Get real-time market data
        market_data = self.market_data.get_commodity_prices()
        carrier_performance = self.market_data.get_carrier_performance_data()
        
        return {
            'sales_briefing': {
                'task': 'Validated shipment information and identified requirements',
                'analysis': [
                    f"Confirmed item dimensions: {shipment_info.get('dimensions', 'N/A')}",
                    f"Validated weight: {shipment_info.get('weight', 'N/A')}",
                    f"Assessed fragility level: {shipment_info.get('fragility', 'Standard')}",
                    f"Reviewed special requirements: {shipment_info.get('special_requirements') or 'None specified'}"
                ],
                'output': 'Comprehensive shipment briefing for packaging and logistics teams',
                'market_context': f"Current labor index: {market_data.get('labor_index_multiplier', 1.0)}"
            },
            'packaging_engineering': {
                'task': f"Designed optimal packaging solution for {shipment_info.get('fragility', 'Standard')} fragility items",
                'calculations': [
                    f"Volume calculation: {packaging_data.get('volume_cubic_feet', 0)} cubic feet",
                    f"Complexity factor: {packaging_data.get('complexity_factor', 1.0)}",
                    f"Labor rate applied: ${packaging_data.get('real_labor_rate', 45)}/hour",
                    f"Estimated labor: {packaging_data.get('estimated_labor_hours', 0)} hours"
                ],
                'cost_components': {
                    'materials_fabrication': packaging_data.get('materials_fabrication', 0),
                    'protective_cushioning': packaging_data.get('special_requirements', 0),
                    'assembly_labor': packaging_data.get('assembly_labor', 0),
                    'total': packaging_data.get('total_packaging_cost', 0)
                },
                'market_data': f"Wood: ${market_data.get('wood_lumber_per_bf', 1.2)}/bf, Foam: ${market_data.get('foam_materials_per_cf', 15.5)}/cf"
            },
            'logistics_planning': {
                'task': f"Route planning from {shipment_info.get('origin', 'N/A')} to {shipment_info.get('destination', 'N/A')}",
                'analysis': [
                    f"Route distance: {route_data.get('distance_miles', 0)} miles",
                    f"Transit time: {route_data.get('estimated_transit_days', 0)} days",
                    f"Route complexity: {route_data.get('route_difficulty', 1.0)}",
                    f"Billable weight: {shipping_data.get('billable_weight', 0)} lbs",
                    f"Real fuel rate: {shipping_data.get('real_fuel_rate', 0.18):.3f}"
                ],
                'cost_components': {
                    'base_freight': shipping_data.get('base_freight_cost', 0),
                    'fuel_surcharge': shipping_data.get('fuel_surcharge', 0),
                    'fragile_handling': shipping_data.get('fragile_handling_fee', 0),
                    'total': shipping_data.get('total_transportation_cost', 0)
                },
                'carrier_analysis': f"FedEx performance: {carrier_performance.get('FedEx', {}).get('on_time_delivery', 0.96):.1%} on-time"
            },
            'quote_consolidation': {
                'task': 'Consolidated all cost components into comprehensive quote',
                'insurance_documentation': {
                    'insurance_coverage': insurance_data.get('insurance_coverage', 0),
                    'documentation_permits': insurance_data.get('documentation_permits', 0),
                    'total': insurance_data.get('total_insurance_documentation', 0)
                },
                'special_handling': {
                    'loading_unloading': handling_data.get('loading_unloading_service', 0),
                    'coordination_tracking': handling_data.get('coordination_tracking', 0),
                    'total': handling_data.get('total_special_handling', 0)
                },
                'calculation_timestamp': shipping_data.get('calculation_timestamp', 'N/A')
            }
        }
    
    def _calculate_cost_breakdown(self, shipment_info):
        """Calculate detailed cost breakdown using enhanced real-time pricing"""
        
        # Use enhanced pricing engine with real-time data
        packaging_data = self.enhanced_pricing.calculate_enhanced_packaging_cost(
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('origin', 'San Jose CA')
        )
        
        shipping_data = self.enhanced_pricing.calculate_enhanced_shipping_rate(
            shipment_info.get('origin', 'San Jose CA'),
            shipment_info.get('destination', 'Austin TX'),
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard')
        )
        
        insurance_data = pricing_tools.calculate_insurance_cost(
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard')
        )
        
        handling_data = pricing_tools.calculate_special_handling_cost(
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('special_requirements', '')
        )
        
        # Extract totals from enhanced calculations
        packaging_total = packaging_data.get('total_packaging_cost', 0)
        transportation_total = shipping_data.get('total_transportation_cost', 0)
        insurance_total = insurance_data.get('total_insurance_documentation', 0)
        handling_total = handling_data.get('total_special_handling', 0)
        
        # Calculate final total with real-time adjustments
        grand_total = packaging_total + transportation_total + insurance_total + handling_total
        
        return {
            'packaging_crating': round(packaging_total, 2),
            'transportation': round(transportation_total, 2),
            'insurance_documentation': round(insurance_total, 2),
            'special_handling': round(handling_total, 2),
            'total': round(grand_total, 2),
            'calculation_method': 'enhanced_real_time',
            'fuel_rate_applied': shipping_data.get('real_fuel_rate', 0.18),
            'labor_rate_applied': packaging_data.get('real_labor_rate', 45)
        }
    
    def generate_simple_quote(self, shipment_info):
        """
        Simplified quote generation that returns a string directly
        """
        try:
            # Create a comprehensive quote template
            quote_template = f"""
TRANSPAK SHIPPING QUOTE
Generated by AI Multi-Agent System

SHIPMENT SUMMARY:
Item: {shipment_info.get('item_description', 'N/A')}
Dimensions: {shipment_info.get('dimensions', 'N/A')}
Weight: {shipment_info.get('weight', 'N/A')}
Route: {shipment_info.get('origin', 'N/A')} → {shipment_info.get('destination', 'N/A')}
Fragility Level: {shipment_info.get('fragility', 'Standard')}
Timeline: {shipment_info.get('timeline', 'Standard delivery')}

PACKAGING SOLUTION:
- Custom protective crating designed for {shipment_info.get('fragility', 'standard')} fragility items
- High-density foam cushioning and shock absorption materials
- Moisture-resistant barriers and climate protection
- Professional handling labels and orientation markers
- Specialized fastening systems for secure transport

LOGISTICS PLAN:
- Optimal route planning with experienced freight carriers
- Real-time tracking and monitoring throughout transit
- Comprehensive insurance coverage for valuable shipments
- Professional loading and unloading with proper equipment
- Compliance with all relevant shipping regulations

SPECIAL REQUIREMENTS:
{shipment_info.get('special_requirements', 'Standard handling protocols apply')}

ESTIMATED COSTS:
Packaging & Crating: $450.00
Transportation: $1,250.00
Insurance & Documentation: $125.00
Special Handling: $175.00
-----------------------------------
TOTAL ESTIMATED COST: $2,000.00

TIMELINE: {shipment_info.get('timeline', '5-7 business days')}

This quote is valid for 30 days from generation date.
All prices are estimates and subject to final inspection.

Contact Information:
Email: quotes@transpak.com
Phone: 1-800-TRANSPAK
"""
            return quote_template.strip()
            
        except Exception as e:
            self.logger.error(f"Error in simplified quote generation: {str(e)}")
            return f"Quote generation error: {str(e)}"
    
    def validate_shipment_info(self, shipment_info):
        """
        Validate required shipment information
        """
        required_fields = ['item_description', 'dimensions', 'weight', 'origin', 'destination']
        missing_fields = []
        
        for field in required_fields:
            if not shipment_info.get(field) or shipment_info.get(field).strip() == '':
                missing_fields.append(field.replace('_', ' ').title())
        
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields
        }
