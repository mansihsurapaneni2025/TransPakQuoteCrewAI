import os
from crewai import Agent
from crewai_tools import SerperDevTool, WebsiteSearchTool

class TransPakAgents:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
    
    def sales_briefing_agent(self):
        """
        Sales Briefing Agent - Gathers shipment details from user input
        """
        return Agent(
            role="Sales Briefing Specialist",
            goal="Gather comprehensive shipment details to enable accurate quoting",
            backstory="""You are an experienced sales representative who specializes in 
            understanding complex shipping requirements. You excel at asking the right 
            questions to capture all necessary details about shipments, including dimensions, 
            weight, destination, fragility, and special handling requirements.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
    
    def crating_design_agent(self):
        """
        Crating Design Agent - Acts as virtual packaging engineer
        """
        return Agent(
            role="Packaging Engineering Specialist",
            goal="Design optimal and cost-efficient crating solutions based on shipment specifications",
            backstory="""You are a skilled packaging engineer with years of experience in 
            designing custom crating solutions. You understand material properties, 
            structural requirements, and cost optimization. You can determine the best 
            packaging approach for any type of shipment, from delicate electronics to 
            heavy machinery.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
    
    def logistics_planner_agent(self):
        """
        Logistics Planner Agent - Determines optimal shipping routes and costs
        """
        return Agent(
            role="Logistics Planning Expert",
            goal="Determine optimal transportation routes, calculate freight costs, and handle compliance issues",
            backstory="""You are a logistics expert with comprehensive knowledge of 
            shipping routes, freight carriers, customs regulations, and compliance 
            requirements. You can optimize shipping paths for cost and speed while 
            ensuring all regulatory requirements are met.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
    
    def quote_consolidator_agent(self):
        """
        Quote Consolidator Agent - Assembles final professional quote
        """
        return Agent(
            role="Quote Consolidation Manager",
            goal="Compile comprehensive quotes by integrating all cost factors and applying business rules",
            backstory="""You are a project manager who specializes in creating 
            professional, detailed quotes. You understand TransPak's business model, 
            profit margins, and pricing strategies. You excel at presenting complex 
            information in a clear, professional format that helps customers make 
            informed decisions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )
