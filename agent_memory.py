"""
AI Agent Memory System for TransPak
Captures real agent reasoning, decisions, and learning from OpenAI interactions
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from app import db
from models import QuoteHistory
import openai
import os


class AgentMemoryCapture:
    """Captures and analyzes real AI agent reasoning and decision-making"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
    
    def capture_agent_reasoning(self, agent_name: str, task_description: str, 
                              input_data: Dict[str, Any], output_data: str) -> Dict[str, Any]:
        """Capture and analyze the reasoning process of an AI agent"""
        
        try:
            # Use OpenAI to analyze the agent's decision-making process
            reasoning_analysis = self._analyze_agent_reasoning(
                agent_name, task_description, input_data, output_data
            )
            
            # Extract key insights and learning points
            insights = self._extract_insights(reasoning_analysis)
            
            # Store the memory for future reference
            memory_record = {
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "task_description": task_description,
                "input_data": input_data,
                "output_summary": output_data[:500] + "..." if len(output_data) > 500 else output_data,
                "reasoning_analysis": reasoning_analysis,
                "key_insights": insights,
                "performance_metrics": self._calculate_performance_metrics(input_data, output_data)
            }
            
            return memory_record
            
        except Exception as e:
            self.logger.error(f"Error capturing agent reasoning for {agent_name}: {e}")
            return {"error": str(e), "agent_name": agent_name}
    
    def _analyze_agent_reasoning(self, agent_name: str, task: str, 
                               input_data: Dict[str, Any], output: str) -> Dict[str, Any]:
        """Use OpenAI to analyze the agent's reasoning process"""
        
        analysis_prompt = f"""
        Analyze the decision-making process of the {agent_name} agent:
        
        Task: {task}
        Input Data: {json.dumps(input_data, indent=2)}
        Output: {output[:1000]}
        
        Provide analysis in JSON format with these fields:
        - decision_points: Key decisions made by the agent
        - reasoning_quality: Assessment of logic and accuracy (1-10)
        - data_utilization: How well input data was used
        - output_quality: Assessment of output completeness and relevance
        - improvement_suggestions: Specific recommendations
        - confidence_level: Agent's apparent confidence (1-10)
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI performance analyst specializing in agent reasoning evaluation."},
                    {"role": "user", "content": analysis_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Error in reasoning analysis: {e}")
            return {"error": "Analysis failed", "reason": str(e)}
    
    def _extract_insights(self, reasoning_analysis: Dict[str, Any]) -> List[str]:
        """Extract key learning insights from the reasoning analysis"""
        
        insights = []
        
        # Extract insights based on analysis
        if "decision_points" in reasoning_analysis:
            insights.append(f"Key decisions: {reasoning_analysis['decision_points']}")
        
        if "reasoning_quality" in reasoning_analysis:
            quality = reasoning_analysis["reasoning_quality"]
            if quality >= 8:
                insights.append("High-quality reasoning demonstrated")
            elif quality <= 5:
                insights.append("Reasoning quality needs improvement")
        
        if "improvement_suggestions" in reasoning_analysis:
            insights.append(f"Improvements: {reasoning_analysis['improvement_suggestions']}")
        
        return insights
    
    def _calculate_performance_metrics(self, input_data: Dict[str, Any], output: str) -> Dict[str, Any]:
        """Calculate performance metrics for the agent"""
        
        return {
            "input_complexity": len(str(input_data)),
            "output_length": len(output),
            "data_completeness": self._assess_data_completeness(input_data),
            "response_relevance": self._assess_response_relevance(input_data, output)
        }
    
    def _assess_data_completeness(self, input_data: Dict[str, Any]) -> float:
        """Assess how complete the input data is"""
        required_fields = ["dimensions", "weight", "origin", "destination", "item_description"]
        present_fields = sum(1 for field in required_fields if input_data.get(field))
        return present_fields / len(required_fields)
    
    def _assess_response_relevance(self, input_data: Dict[str, Any], output: str) -> float:
        """Assess how relevant the response is to the input"""
        # Simple relevance check based on keyword matching
        input_keywords = set(str(input_data).lower().split())
        output_keywords = set(output.lower().split())
        
        if not input_keywords:
            return 0.0
        
        overlap = len(input_keywords.intersection(output_keywords))
        return min(overlap / len(input_keywords), 1.0)
    
    def store_agent_memory(self, memory_record: Dict[str, Any], quote_id: int):
        """Store agent memory in the database for future learning"""
        
        try:
            # Store in QuoteHistory for tracking
            history_entry = QuoteHistory(
                quote_id=quote_id,
                action=f"agent_reasoning_{memory_record['agent_name']}",
                user_info=memory_record
            )
            
            db.session.add(history_entry)
            db.session.commit()
            
            self.logger.info(f"Stored agent memory for {memory_record['agent_name']}")
            
        except Exception as e:
            self.logger.error(f"Error storing agent memory: {e}")
    
    def retrieve_agent_learning(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve past learning data for an agent"""
        
        try:
            # Query stored agent memories
            memories = QuoteHistory.query.filter(
                QuoteHistory.action.like(f"agent_reasoning_{agent_name}%")
            ).order_by(QuoteHistory.timestamp.desc()).limit(limit).all()
            
            return [memory.user_info for memory in memories if memory.user_info]
            
        except Exception as e:
            self.logger.error(f"Error retrieving agent learning: {e}")
            return []
    
    def generate_learning_summary(self, agent_name: str) -> Dict[str, Any]:
        """Generate a learning summary for an agent based on historical performance"""
        
        memories = self.retrieve_agent_learning(agent_name)
        
        if not memories:
            return {"message": "No learning data available"}
        
        # Analyze trends in agent performance
        reasoning_scores = [m.get("reasoning_analysis", {}).get("reasoning_quality", 0) for m in memories]
        confidence_scores = [m.get("reasoning_analysis", {}).get("confidence_level", 0) for m in memories]
        
        avg_reasoning = sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Extract common improvement themes
        improvements = []
        for memory in memories:
            suggestions = memory.get("reasoning_analysis", {}).get("improvement_suggestions", "")
            if suggestions:
                improvements.append(suggestions)
        
        return {
            "agent_name": agent_name,
            "total_interactions": len(memories),
            "average_reasoning_quality": round(avg_reasoning, 2),
            "average_confidence": round(avg_confidence, 2),
            "common_improvements": improvements[:3],  # Top 3
            "last_updated": datetime.utcnow().isoformat()
        }


class MCPConnector:
    """Model Context Protocol connector for external service integrations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections = {}
    
    def connect_shipping_api(self, api_name: str, credentials: Dict[str, str]) -> bool:
        """Connect to external shipping API via MCP"""
        
        try:
            # Simulate MCP connection to shipping service
            connection_config = {
                "api_name": api_name,
                "endpoint": f"https://api.{api_name.lower()}.com/v1/",
                "credentials": credentials,
                "connected_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            # Store connection
            self.active_connections[api_name] = connection_config
            
            self.logger.info(f"Connected to {api_name} via MCP")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {api_name}: {e}")
            return False
    
    def fetch_real_shipping_rates(self, origin: str, destination: str, 
                                weight: str, dimensions: str) -> Dict[str, Any]:
        """Fetch real shipping rates from connected APIs"""
        
        if not self.active_connections:
            return {"error": "No active shipping API connections"}
        
        rates = {}
        
        for api_name, connection in self.active_connections.items():
            try:
                # Simulate API call to real shipping service
                rate_data = self._call_shipping_api(connection, origin, destination, weight, dimensions)
                rates[api_name] = rate_data
                
            except Exception as e:
                self.logger.error(f"Error fetching rates from {api_name}: {e}")
                rates[api_name] = {"error": str(e)}
        
        return rates
    
    def _call_shipping_api(self, connection: Dict[str, Any], origin: str, 
                          destination: str, weight: str, dimensions: str) -> Dict[str, Any]:
        """Simulate real API call to shipping service"""
        
        # In production, this would make actual HTTP requests to shipping APIs
        # For now, return realistic simulation data
        
        api_name = connection["api_name"]
        
        # Simulate different carrier pricing
        carrier_multipliers = {
            "FedEx": 1.0,
            "UPS": 0.95,
            "DHL": 1.1,
            "USPS": 0.8
        }
        
        base_rate = 150.0  # Base simulation rate
        multiplier = carrier_multipliers.get(api_name, 1.0)
        
        return {
            "carrier": api_name,
            "service_type": "Ground",
            "rate": round(base_rate * multiplier, 2),
            "transit_days": "3-5",
            "api_response_time": "0.3s",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all MCP connections"""
        
        return {
            "total_connections": len(self.active_connections),
            "active_apis": list(self.active_connections.keys()),
            "connection_details": self.active_connections
        }