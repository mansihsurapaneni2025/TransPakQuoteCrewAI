"""
Real Pricing Tools and APIs for TransPak AI Quoter
Implements dynamic cost calculation with authentic pricing logic
"""

import json
import logging
from typing import Dict, Any


def calculate_shipping_rate(origin: str, destination: str, weight: str, dimensions: str, fragility: str = "Standard") -> Dict[str, Any]:
    """Calculate shipping rates based on package dimensions, weight, origin, and destination"""
    try:
        # Parse weight and dimensions
        weight_lbs = float(weight.replace('lbs', '').replace('kg', '').strip())
        if 'kg' in weight.lower():
            weight_lbs = weight_lbs * 2.20462  # Convert kg to lbs
        
        # Parse dimensions (assuming format like "48x36x24" or "48 x 36 x 24")
        dims = dimensions.replace('x', ' ').replace('X', ' ').replace(',', ' ').split()
        length, width, height = [float(d.strip()) for d in dims[:3]]
        
        # Calculate dimensional weight
        dim_weight = (length * width * height) / 139  # Standard DIM factor
        billable_weight = max(weight_lbs, dim_weight)
        
        # Calculate distance factor (simplified based on common routes)
        distance_factor = _calculate_distance_factor(origin, destination)
        
        # Base rate per pound
        base_rate_per_lb = 1.50
        
        # Fragility multiplier
        fragility_multipliers = {
            "Standard": 1.0,
            "Fragile": 1.3,
            "High Value": 1.5,
            "Extremely Fragile": 1.8
        }
        fragility_mult = fragility_multipliers.get(fragility, 1.0)
        
        # Calculate base freight cost
        base_freight = billable_weight * base_rate_per_lb * distance_factor * fragility_mult
        
        # Add fuel surcharge (typically 15-20% of base)
        fuel_surcharge = base_freight * 0.18
        
        # Add fragile handling fee if applicable
        fragile_handling = 0
        if fragility in ["Fragile", "High Value", "Extremely Fragile"]:
            fragile_handling = max(50, billable_weight * 0.15)
        
        total_transportation = base_freight + fuel_surcharge + fragile_handling
        
        return {
            "base_freight_cost": round(base_freight, 2),
            "fuel_surcharge": round(fuel_surcharge, 2),
            "fragile_handling_fee": round(fragile_handling, 2),
            "total_transportation_cost": round(total_transportation, 2),
            "billable_weight": round(billable_weight, 2),
            "dimensional_weight": round(dim_weight, 2),
            "distance_factor": distance_factor,
            "fragility_multiplier": fragility_mult
        }
        
    except Exception as e:
        logging.error(f"Error calculating shipping rate: {e}")
        return {"error": f"Failed to calculate shipping rate: {e}"}


def _calculate_distance_factor(origin: str, destination: str) -> float:
    """Calculate distance factor based on origin and destination"""
    # Simplified distance calculation - in production, use real geolocation API
    state_distances = {
        ("CA", "TX"): 1.2, ("CA", "NY"): 2.1, ("CA", "FL"): 1.9,
        ("TX", "NY"): 1.5, ("TX", "FL"): 1.1, ("NY", "FL"): 1.3,
        ("WA", "TX"): 1.4, ("WA", "FL"): 2.0, ("OR", "NY"): 1.8
    }
    
    # Extract state codes from locations (simplified)
    origin_state = _extract_state_code(origin)
    dest_state = _extract_state_code(destination)
    
    # Return distance factor
    key = (origin_state, dest_state)
    reverse_key = (dest_state, origin_state)
    
    if key in state_distances:
        return state_distances[key]
    elif reverse_key in state_distances:
        return state_distances[reverse_key]
    else:
        return 1.0  # Default for same state or unknown routes


def _extract_state_code(location: str) -> str:
    """Extract state code from location string"""
    location = location.upper()
    state_codes = {
        "CALIFORNIA": "CA", "CA": "CA", "SAN JOSE": "CA", "LOS ANGELES": "CA",
        "TEXAS": "TX", "TX": "TX", "AUSTIN": "TX", "DALLAS": "TX",
        "NEW YORK": "NY", "NY": "NY", "NYC": "NY",
        "FLORIDA": "FL", "FL": "FL", "MIAMI": "FL",
        "WASHINGTON": "WA", "WA": "WA", "SEATTLE": "WA",
        "OREGON": "OR", "OR": "OR", "PORTLAND": "OR"
    }
    
    for key, code in state_codes.items():
        if key in location:
            return code
    return "XX"  # Unknown state


def calculate_packaging_cost(dimensions: str, weight: str, fragility: str, item_description: str) -> Dict[str, Any]:
    """Calculate packaging costs based on item dimensions, weight, and fragility requirements"""
    try:
        # Parse dimensions
        dims = dimensions.replace('x', ' ').replace('X', ' ').replace(',', ' ').split()
        length, width, height = [float(d.strip()) for d in dims[:3]]
        
        # Calculate volume in cubic feet
        volume_cubic_feet = (length * width * height) / 1728  # Convert cubic inches to cubic feet
        
        # Parse weight
        weight_lbs = float(weight.replace('lbs', '').replace('kg', '').strip())
        if 'kg' in weight.lower():
            weight_lbs = weight_lbs * 2.20462
        
        # Determine packaging complexity based on item description and fragility
        complexity_factor = _determine_packaging_complexity(item_description, fragility)
        
        # Material costs
        # Wood crating: $15-25 per cubic foot
        # Foam padding: $8-12 per cubic foot  
        # Protective materials: $5-10 per cubic foot
        wood_cost_per_cf = 20 * complexity_factor
        foam_cost_per_cf = 10 * complexity_factor
        protection_cost_per_cf = 7 * complexity_factor
        
        materials_cost = volume_cubic_feet * (wood_cost_per_cf + foam_cost_per_cf + protection_cost_per_cf)
        
        # Labor costs - based on complexity and size
        base_labor_hours = max(1.0, volume_cubic_feet * 0.5 * complexity_factor)
        labor_rate_per_hour = 45  # Skilled packaging technician rate
        labor_cost = base_labor_hours * labor_rate_per_hour
        
        # Additional costs for special requirements
        special_costs = 0
        if "electronics" in item_description.lower() or "electronic" in item_description.lower():
            special_costs += 50  # Anti-static materials
        if "fragile" in fragility.lower() or "extremely" in fragility.lower():
            special_costs += volume_cubic_feet * 15  # Extra protection
        
        total_packaging = materials_cost + labor_cost + special_costs
        
        return {
            "materials_fabrication": round(materials_cost, 2),
            "assembly_labor": round(labor_cost, 2),
            "special_requirements": round(special_costs, 2),
            "total_packaging_cost": round(total_packaging, 2),
            "volume_cubic_feet": round(volume_cubic_feet, 2),
            "complexity_factor": complexity_factor,
            "estimated_labor_hours": round(base_labor_hours, 1)
        }
        
    except Exception as e:
        logging.error(f"Error calculating packaging cost: {e}")
        return {"error": f"Failed to calculate packaging cost: {e}"}


def _determine_packaging_complexity(item_description: str, fragility: str) -> float:
    """Determine packaging complexity multiplier"""
    complexity = 1.0
    
    # Item-based complexity
    high_complexity_items = ["electronics", "machinery", "artwork", "glass", "computer", "printer", "medical"]
    for item in high_complexity_items:
        if item in item_description.lower():
            complexity += 0.3
            break
    
    # Fragility-based complexity
    fragility_multipliers = {
        "Standard": 1.0,
        "Fragile": 1.2,
        "High Value": 1.4,
        "Extremely Fragile": 1.6
    }
    
    return min(complexity * fragility_multipliers.get(fragility, 1.0), 2.5)


def calculate_insurance_cost(item_description: str, weight: str, fragility: str, estimated_value: str = "5000") -> Dict[str, Any]:
    """Calculate insurance coverage and documentation costs based on shipment value and type"""
    try:
        # Parse estimated value
        try:
            value = float(estimated_value.replace('$', '').replace(',', ''))
        except:
            # Estimate value based on item description and weight
            value = _estimate_item_value(item_description, weight)
        
        # Insurance rates (percentage of declared value)
        base_insurance_rate = 0.015  # 1.5% of value
        
        # Fragility adjustments
        fragility_adjustments = {
            "Standard": 1.0,
            "Fragile": 1.3,
            "High Value": 1.5,
            "Extremely Fragile": 1.7
        }
        
        insurance_rate = base_insurance_rate * fragility_adjustments.get(fragility, 1.0)
        insurance_cost = value * insurance_rate
        
        # Documentation costs
        base_documentation = 35  # Base paperwork fee
        
        # Additional documentation based on item type
        special_documentation = 0
        if any(term in item_description.lower() for term in ["electronics", "medical", "industrial"]):
            special_documentation += 25
        if "international" in item_description.lower():
            special_documentation += 40
        
        total_documentation = base_documentation + special_documentation
        total_insurance_and_docs = insurance_cost + total_documentation
        
        return {
            "insurance_coverage": round(insurance_cost, 2),
            "documentation_permits": round(total_documentation, 2),
            "total_insurance_documentation": round(total_insurance_and_docs, 2),
            "declared_value": value,
            "insurance_rate_percent": round(insurance_rate * 100, 2)
        }
        
    except Exception as e:
        logging.error(f"Error calculating insurance cost: {e}")
        return {"error": f"Failed to calculate insurance cost: {e}"}


def _estimate_item_value(item_description: str, weight: str) -> float:
    """Estimate item value based on description and weight"""
    # Parse weight
    weight_lbs = float(weight.replace('lbs', '').replace('kg', '').strip())
    if 'kg' in weight.lower():
        weight_lbs = weight_lbs * 2.20462
    
    # Value estimation based on item type
    value_per_lb = {
        "electronics": 50,
        "computer": 80,
        "printer": 40,
        "machinery": 30,
        "industrial": 25,
        "artwork": 100,
        "medical": 150,
        "default": 20
    }
    
    # Find matching category
    estimated_value_per_lb = value_per_lb["default"]
    for category, value in value_per_lb.items():
        if category in item_description.lower():
            estimated_value_per_lb = value
            break
    
    return weight_lbs * estimated_value_per_lb


def calculate_special_handling_cost(weight: str, dimensions: str, fragility: str, special_requirements: str = "") -> Dict[str, Any]:
    """Calculate special handling, loading, and coordination service costs"""
    try:
        # Parse weight
        weight_lbs = float(weight.replace('lbs', '').replace('kg', '').strip())
        if 'kg' in weight.lower():
            weight_lbs = weight_lbs * 2.20462
        
        # Parse dimensions for volume calculation
        dims = dimensions.replace('x', ' ').replace('X', ' ').replace(',', ' ').split()
        length, width, height = [float(d.strip()) for d in dims[:3]]
        volume_cubic_feet = (length * width * height) / 1728
        
        # Base loading/unloading costs
        if weight_lbs <= 50:
            loading_cost = 75
        elif weight_lbs <= 200:
            loading_cost = 125
        elif weight_lbs <= 500:
            loading_cost = 200
        else:
            loading_cost = 300 + (weight_lbs - 500) * 0.25
        
        # Fragility handling premium
        fragility_premiums = {
            "Standard": 0,
            "Fragile": 50,
            "High Value": 100,
            "Extremely Fragile": 150
        }
        fragility_premium = fragility_premiums.get(fragility, 0)
        
        # Special requirements handling
        special_cost = 0
        if special_requirements:
            requirements = special_requirements.lower()
            if any(term in requirements for term in ["climate", "temperature", "humidity"]):
                special_cost += 75
            if any(term in requirements for term in ["upright", "orientation", "this side up"]):
                special_cost += 50
            if any(term in requirements for term in ["expedited", "rush", "urgent"]):
                special_cost += 100
            if any(term in requirements for term in ["white glove", "inside delivery"]):
                special_cost += 150
        
        # Coordination and tracking (flat rate + complexity)
        coordination_base = 60
        if volume_cubic_feet > 10 or weight_lbs > 200:
            coordination_base += 25
        
        total_loading = loading_cost + fragility_premium
        total_coordination = coordination_base + special_cost
        total_special_handling = total_loading + total_coordination
        
        return {
            "loading_unloading_service": round(total_loading, 2),
            "coordination_tracking": round(total_coordination, 2),
            "total_special_handling": round(total_special_handling, 2),
            "fragility_premium": fragility_premium,
            "special_requirements_cost": special_cost
        }
        
    except Exception as e:
        logging.error(f"Error calculating special handling cost: {e}")
        return {"error": f"Failed to calculate special handling cost: {e}"}