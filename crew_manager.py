import os
import json
import logging
from crewai import Crew, Process
from agents import TransPakAgents
from tasks import TransPakTasks

class TransPakCrewManager:
    def __init__(self):
        self.agents = TransPakAgents()
        self.tasks = TransPakTasks()
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
            
            self.logger.info("Quote generation completed successfully")
            return {
                'success': True,
                'quote': result,
                'message': 'Quote generated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error in quote generation: {str(e)}")
            return {
                'success': False,
                'quote': None,
                'message': f'Error generating quote: {str(e)}'
            }
    
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
