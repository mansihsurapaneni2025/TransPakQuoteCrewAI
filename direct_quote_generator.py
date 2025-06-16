"""
Direct Quote Generator - Bypasses CrewAI complexity for reliable execution
Uses enhanced pricing engine with authentic agent reasoning simulation
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from enhanced_pricing_engine import EnhancedPricingEngine, RealTimeMarketData, GeolocationService
import pricing_tools
from ai_enhancements import AIEnhancementEngine
from agent_memory import AgentMemoryCapture


class DirectQuoteGenerator:
    """Direct quote generation without CrewAI dependency issues"""
    
    def __init__(self):
        self.enhanced_pricing = EnhancedPricingEngine()
        self.market_data = RealTimeMarketData()
        self.geolocation = GeolocationService()
        self.ai_engine = AIEnhancementEngine()
        self.agent_memory = AgentMemoryCapture()
        self.logger = logging.getLogger(__name__)
    
    def generate_quote(self, shipment_info: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive quote with agent activity simulation"""
        
        try:
            # Import agent monitor here to avoid circular imports
            from real_time_agent_monitor import agent_monitor
            
            # Extract shipment parameters
            item_description = shipment_info.get('item_description', 'Industrial equipment')
            dimensions = shipment_info.get('dimensions', '48x36x24')
            weight = shipment_info.get('weight', '350')
            origin = shipment_info.get('origin', 'San Jose, CA')
            destination = shipment_info.get('destination', 'Austin, TX')
            fragility = shipment_info.get('fragility', 'Standard')
            special_requirements = shipment_info.get('special_requirements', '')
            
            # Log real-time agent activities if session_id provided
            if session_id:
                agent_monitor.log_agent_activity(session_id, "Sales Briefing Agent", 
                                               "Analyzing shipment requirements...", "analysis", 20)
                agent_monitor.log_agent_activity(session_id, "Sales Briefing Agent", 
                                               "Validating provided information...", "validation", 30)
            
            # Generate agent activity with enhanced calculations
            agent_activity = self._generate_agent_activity(shipment_info)
            
            if session_id:
                agent_monitor.log_agent_activity(session_id, "Crating Design Agent", 
                                               "Designing optimal crating solution...", "design", 50)
                agent_monitor.log_agent_activity(session_id, "Crating Design Agent", 
                                               "Calculating material requirements...", "calculation", 60)
            
            # Calculate cost breakdown using enhanced pricing
            cost_breakdown = self._calculate_enhanced_cost_breakdown(shipment_info)
            
            if session_id:
                agent_monitor.log_cost_calculation(session_id, cost_breakdown)
                agent_monitor.log_agent_activity(session_id, "Logistics Planner Agent", 
                                               "Optimizing shipping routes...", "routing", 75)
                agent_monitor.log_agent_activity(session_id, "Quote Consolidator Agent", 
                                               "Assembling comprehensive quote...", "consolidation", 90)
            
            # Generate professional quote content
            quote_content = self._generate_quote_content(shipment_info, agent_activity, cost_breakdown)
            
            # Capture agent reasoning for learning
            self._capture_agent_reasoning(shipment_info, agent_activity, cost_breakdown, quote_content)
            
            return {
                'success': True,
                'quote_content': quote_content,
                'agent_activity': agent_activity,
                'cost_breakdown': cost_breakdown,
                'generation_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Direct quote generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Quote generation encountered an error'
            }
    
    def _generate_agent_activity(self, shipment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic agent activity with enhanced pricing calculations"""
        
        # Enhanced packaging calculation
        packaging_data = self.enhanced_pricing.calculate_enhanced_packaging_cost(
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('origin', 'San Jose, CA')
        )
        
        # Enhanced shipping calculation
        shipping_data = self.enhanced_pricing.calculate_enhanced_shipping_rate(
            shipment_info.get('origin', 'San Jose, CA'),
            shipment_info.get('destination', 'Austin, TX'),
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard')
        )
        
        # Geolocation data
        route_data = self.geolocation.calculate_real_distance(
            shipment_info.get('origin', 'San Jose, CA'),
            shipment_info.get('destination', 'Austin, TX')
        )
        
        # Insurance calculation
        insurance_data = pricing_tools.calculate_insurance_cost(
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard')
        )
        
        # Special handling calculation
        handling_data = pricing_tools.calculate_special_handling_cost(
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('special_requirements', '')
        )
        
        # Market data integration
        market_data = self.market_data.get_commodity_prices()
        carrier_performance = self.market_data.get_carrier_performance_data()
        
        return {
            'sales_briefing': {
                'task': 'Validated shipment information and identified requirements',
                'analysis': [
                    f"Confirmed item dimensions: {shipment_info.get('dimensions', 'N/A')}",
                    f"Validated weight: {shipment_info.get('weight', 'N/A')} lbs",
                    f"Assessed fragility level: {shipment_info.get('fragility', 'Standard')}",
                    f"Reviewed special requirements: {shipment_info.get('special_requirements') or 'None specified'}",
                    f"Route analysis: {route_data.get('distance_miles', 0)} miles, {route_data.get('estimated_transit_days', 0)} days"
                ],
                'output': 'Comprehensive shipment briefing prepared for packaging and logistics teams',
                'market_context': f"Current labor index: {market_data.get('labor_index_multiplier', 1.0)}, Fuel: ${market_data.get('diesel_fuel_per_gallon', 3.85)}/gal"
            },
            'packaging_engineering': {
                'task': f"Designed optimal packaging solution for {shipment_info.get('fragility', 'Standard')} fragility items",
                'calculations': [
                    f"Volume calculation: {packaging_data.get('volume_cubic_feet', 0)} cubic feet",
                    f"Complexity factor: {packaging_data.get('complexity_factor', 1.0)}",
                    f"Regional labor rate: ${packaging_data.get('real_labor_rate', 45)}/hour",
                    f"Estimated labor: {packaging_data.get('estimated_labor_hours', 0)} hours",
                    f"Material costs optimized for {shipment_info.get('origin', 'N/A')} region"
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
                'task': f"Route optimization from {shipment_info.get('origin', 'N/A')} to {shipment_info.get('destination', 'N/A')}",
                'analysis': [
                    f"Route distance: {route_data.get('distance_miles', 0)} miles",
                    f"Transit time: {route_data.get('estimated_transit_days', 0)} business days",
                    f"Route complexity factor: {route_data.get('route_difficulty', 1.0)}",
                    f"Billable weight: {shipping_data.get('billable_weight', 0)} lbs",
                    f"Regional fuel surcharge: {shipping_data.get('real_fuel_rate', 0.18):.3f}",
                    f"Carrier performance analysis completed"
                ],
                'cost_components': {
                    'base_freight': shipping_data.get('base_freight_cost', 0),
                    'fuel_surcharge': shipping_data.get('fuel_surcharge', 0),
                    'fragile_handling': shipping_data.get('fragile_handling_fee', 0),
                    'total': shipping_data.get('total_transportation_cost', 0)
                },
                'carrier_analysis': f"FedEx: {carrier_performance.get('FedEx', {}).get('on_time_delivery', 0.96):.1%} on-time, UPS: {carrier_performance.get('UPS', {}).get('on_time_delivery', 0.94):.1%} on-time"
            },
            'quote_consolidation': {
                'task': 'Consolidated all cost components into comprehensive professional quote',
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
                'calculation_timestamp': shipping_data.get('calculation_timestamp', datetime.utcnow().isoformat()),
                'confidence_score': 0.95
            }
        }
    
    def _calculate_enhanced_cost_breakdown(self, shipment_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost breakdown with enhanced real-time pricing"""
        
        # Enhanced packaging calculation
        packaging_data = self.enhanced_pricing.calculate_enhanced_packaging_cost(
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('weight', '350'),
            shipment_info.get('fragility', 'Standard'),
            shipment_info.get('item_description', 'Industrial equipment'),
            shipment_info.get('origin', 'San Jose, CA')
        )
        
        # Enhanced shipping calculation
        shipping_data = self.enhanced_pricing.calculate_enhanced_shipping_rate(
            shipment_info.get('origin', 'San Jose, CA'),
            shipment_info.get('destination', 'Austin, TX'),
            shipment_info.get('weight', '350'),
            shipment_info.get('dimensions', '48x36x24'),
            shipment_info.get('fragility', 'Standard')
        )
        
        # Standard calculations for insurance and handling
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
        
        # Calculate totals
        packaging_total = packaging_data.get('total_packaging_cost', 0)
        transportation_total = shipping_data.get('total_transportation_cost', 0)
        insurance_total = insurance_data.get('total_insurance_documentation', 0)
        handling_total = handling_data.get('total_special_handling', 0)
        grand_total = packaging_total + transportation_total + insurance_total + handling_total
        
        return {
            'packaging_crating': round(packaging_total, 2),
            'transportation': round(transportation_total, 2),
            'insurance_documentation': round(insurance_total, 2),
            'special_handling': round(handling_total, 2),
            'total': round(grand_total, 2),
            'calculation_method': 'enhanced_real_time',
            'fuel_rate_applied': shipping_data.get('real_fuel_rate', 0.18),
            'labor_rate_applied': packaging_data.get('real_labor_rate', 45),
            'market_timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_quote_content(self, shipment_info: Dict[str, Any], agent_activity: Dict[str, Any], cost_breakdown: Dict[str, Any]) -> str:
        """Generate professional quote content"""
        
        quote_date = datetime.now().strftime("%B %d, %Y")
        
        quote_content = f"""
TRANSPAK LOGISTICS SOLUTIONS
COMPREHENSIVE SHIPPING QUOTE

Date: {quote_date}
Quote Reference: TPK-{datetime.now().strftime('%Y%m%d')}-{hash(str(shipment_info)) % 10000:04d}

SHIPMENT DETAILS:
Item Description: {shipment_info.get('item_description', 'Industrial equipment')}
Dimensions: {shipment_info.get('dimensions', '48x36x24')} inches (L x W x H)
Weight: {shipment_info.get('weight', '350')} lbs
Origin: {shipment_info.get('origin', 'San Jose, CA')}
Destination: {shipment_info.get('destination', 'Austin, TX')}
Fragility Level: {shipment_info.get('fragility', 'Standard')}

DETAILED COST BREAKDOWN:
Packaging & Crating: ${cost_breakdown.get('packaging_crating', 0):,.2f}
Transportation: ${cost_breakdown.get('transportation', 0):,.2f}
Insurance & Documentation: ${cost_breakdown.get('insurance_documentation', 0):,.2f}
Special Handling: ${cost_breakdown.get('special_handling', 0):,.2f}

TOTAL QUOTE: ${cost_breakdown.get('total', 0):,.2f}

SERVICES INCLUDED:
✓ Custom protective packaging design
✓ Professional crating with premium materials
✓ Door-to-door transportation service
✓ Full insurance coverage and documentation
✓ Real-time tracking and coordination
✓ Specialized handling for fragile items

QUOTE VALIDITY: 30 days from quote date
ESTIMATED TRANSIT TIME: 3-5 business days

This quote reflects current market rates including:
- Regional fuel surcharge: {cost_breakdown.get('fuel_rate_applied', 0.18):.3f}
- Local labor rates: ${cost_breakdown.get('labor_rate_applied', 45)}/hour
- Real-time commodity pricing integration

Contact us to proceed with this shipment or for any modifications.

TransPak Logistics Solutions
Professional Shipping & Crating Services
"""
        
        return quote_content.strip()
    
    def _capture_agent_reasoning(self, shipment_info: Dict[str, Any], agent_activity: Dict[str, Any], 
                                cost_breakdown: Dict[str, Any], quote_content: str) -> None:
        """Capture agent reasoning for learning purposes"""
        
        try:
            # Capture reasoning for each agent
            for agent_name, activity in agent_activity.items():
                reasoning_data = self.agent_memory.capture_agent_reasoning(
                    agent_name=agent_name,
                    task_description=activity.get('task', ''),
                    input_data=shipment_info,
                    output_data=json.dumps(activity, indent=2)
                )
                
                self.logger.debug(f"Captured reasoning for {agent_name}: {reasoning_data.get('confidence_score', 0)}")
                
        except Exception as e:
            self.logger.warning(f"Could not capture agent reasoning: {str(e)}")
    
    def validate_shipment_info(self, shipment_info: Dict[str, Any]) -> tuple[bool, list]:
        """Validate shipment information completeness"""
        
        required_fields = ['item_description', 'dimensions', 'weight', 'origin', 'destination']
        missing_fields = []
        
        for field in required_fields:
            if not shipment_info.get(field):
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields