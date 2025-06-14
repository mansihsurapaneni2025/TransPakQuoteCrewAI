import json
import re
from datetime import datetime
from typing import Dict, Any, Tuple
import openai
import os

class AIEnhancementEngine:
    """Enhanced AI capabilities with confidence scoring and learning"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Latest OpenAI model
        
    def analyze_quote_confidence(self, quote_content: str, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze confidence level of generated quote"""
        try:
            confidence_prompt = f"""
            Analyze this shipping quote for accuracy and completeness. Rate the confidence level from 0-100 based on:
            1. Completeness of information
            2. Realistic pricing estimates
            3. Proper handling requirements
            4. Clear timeline estimates
            5. Professional presentation
            
            Shipment Details: {json.dumps(shipment_data)}
            Quote: {quote_content}
            
            Respond with JSON format:
            {{
                "confidence_score": number (0-100),
                "completeness_score": number (0-100),
                "accuracy_indicators": ["factor1", "factor2"],
                "improvement_suggestions": ["suggestion1", "suggestion2"],
                "risk_factors": ["risk1", "risk2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": confidence_prompt}],
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis['analyzed_at'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            return {
                "confidence_score": 75,  # Default moderate confidence
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
    
    def extract_quote_pricing(self, quote_content: str) -> Dict[str, Any]:
        """Extract and analyze pricing information from quote"""
        try:
            # Use regex to find monetary amounts
            price_patterns = [
                r'\$[\d,]+\.?\d*',
                r'USD\s*[\d,]+\.?\d*',
                r'Total[:\s]*\$?[\d,]+\.?\d*'
            ]
            
            prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, quote_content, re.IGNORECASE)
                prices.extend(matches)
            
            # Use AI to extract structured pricing
            pricing_prompt = f"""
            Extract all pricing information from this shipping quote.
            
            Quote: {quote_content}
            
            Respond with JSON format:
            {{
                "total_cost": number or null,
                "cost_breakdown": {{
                    "materials": number or null,
                    "labor": number or null,
                    "shipping": number or null,
                    "handling": number or null
                }},
                "currency": "USD",
                "pricing_confidence": number (0-100)
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": pricing_prompt}],
                response_format={"type": "json_object"}
            )
            
            pricing_data = json.loads(response.choices[0].message.content)
            pricing_data['extracted_prices'] = prices
            
            return pricing_data
            
        except Exception as e:
            return {"error": str(e), "extracted_prices": []}
    
    def generate_cargo_specific_insights(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specialized insights based on cargo type"""
        try:
            cargo_prompt = f"""
            Based on this shipment description, provide specialized handling insights:
            
            Item: {shipment_data.get('item_description', '')}
            Dimensions: {shipment_data.get('dimensions', '')}
            Weight: {shipment_data.get('weight', '')}
            Fragility: {shipment_data.get('fragility', 'Standard')}
            
            Provide insights in JSON format:
            {{
                "cargo_category": "electronics|machinery|artwork|furniture|hazardous|other",
                "risk_level": "low|medium|high",
                "special_considerations": ["consideration1", "consideration2"],
                "recommended_packaging": "description",
                "handling_requirements": ["requirement1", "requirement2"],
                "insurance_recommendations": "description"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": cargo_prompt}],
                response_format={"type": "json_object"}
            )
            
            insights = json.loads(response.choices[0].message.content)
            return insights
            
        except Exception as e:
            return {"error": str(e)}
    
    def learn_from_quote_feedback(self, quote_id: int, feedback_data: Dict[str, Any]) -> bool:
        """Store learning data from quote feedback for future improvements"""
        try:
            # In a production system, this would store to a learning database
            # For now, we'll log the feedback for analysis
            learning_data = {
                "quote_id": quote_id,
                "feedback": feedback_data,
                "timestamp": datetime.now().isoformat(),
                "learning_type": "quote_feedback"
            }
            
            # Log to file for analysis (in production, use proper data store)
            with open("ai_learning_data.jsonl", "a") as f:
                f.write(json.dumps(learning_data) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Learning data storage error: {e}")
            return False
    
    def validate_quote_completeness(self, quote_content: str) -> Tuple[bool, list]:
        """Validate that quote contains all required elements"""
        required_elements = [
            "packaging",
            "shipping",
            "timeline",
            "cost",
            "handling"
        ]
        
        missing_elements = []
        quote_lower = quote_content.lower()
        
        for element in required_elements:
            if element not in quote_lower:
                missing_elements.append(element)
        
        is_complete = len(missing_elements) == 0
        return is_complete, missing_elements
    
    def suggest_quote_improvements(self, quote_content: str, confidence_analysis: Dict[str, Any]) -> list:
        """Suggest improvements based on confidence analysis"""
        suggestions = []
        
        confidence_score = confidence_analysis.get('confidence_score', 75)
        
        if confidence_score < 80:
            suggestions.append("Consider adding more detailed cost breakdown")
            
        if confidence_score < 70:
            suggestions.append("Include specific timeline milestones")
            suggestions.append("Add insurance and liability information")
            
        if confidence_score < 60:
            suggestions.append("Provide more detailed packaging specifications")
            suggestions.append("Include contingency planning information")
        
        # Add suggestions from AI analysis
        ai_suggestions = confidence_analysis.get('improvement_suggestions', [])
        suggestions.extend(ai_suggestions)
        
        return list(set(suggestions))  # Remove duplicates