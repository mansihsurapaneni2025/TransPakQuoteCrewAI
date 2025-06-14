#!/usr/bin/env python3
"""
Simple TransPak AI Quote Generator - Single File Version
Based on the provided requirements for a working CrewAI implementation
"""

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Setup OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)

llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

def get_shipment_details():
    """Interactive function to gather shipment details from user"""
    print("\n=== Welcome to TransPak AI Quoter ===")
    print("Please provide the following shipment details:\n")
    
    item_description = input("Item Description: ")
    dimensions = input("Dimensions (L x W x H): ")
    weight = input("Weight: ")
    origin = input("Origin Location: ")
    destination = input("Destination Location: ")
    fragility = input("Fragility Level (Standard/High/Extremely High): ")
    special_requirements = input("Special Requirements (optional): ")
    
    # Format into comprehensive string
    shipment_details = f"""
    SHIPMENT DETAILS:
    - Item: {item_description}
    - Dimensions: {dimensions}
    - Weight: {weight}
    - Origin: {origin}
    - Destination: {destination}
    - Fragility: {fragility}
    - Special Requirements: {special_requirements if special_requirements else 'None'}
    """
    
    return shipment_details

# Define the four agents
sales_briefing_agent = Agent(
    role="Sales Briefing Specialist",
    goal="Gather and structure shipment details for accurate quote generation",
    backstory="You are an experienced logistics coordinator who specializes in gathering comprehensive shipment information. You excel at identifying missing details and ensuring all necessary information is captured for accurate quoting.",
    llm=llm,
    verbose=True
)

crating_design_agent = Agent(
    role="Packaging Engineering Specialist", 
    goal="Design optimal crating solutions and estimate packaging costs",
    backstory="You are a packaging engineer with 15+ years of experience in custom crating and protective packaging. You specialize in creating cost-effective solutions that ensure safe transport of valuable and fragile items.",
    llm=llm,
    verbose=True
)

logistics_planner_agent = Agent(
    role="Logistics Planning Specialist",
    goal="Determine optimal shipping routes and calculate freight costs",
    backstory="You are a logistics expert who specializes in freight planning and cost optimization. You have extensive knowledge of shipping routes, carrier capabilities, and regulatory requirements.",
    llm=llm,
    verbose=True
)

quote_consolidator_agent = Agent(
    role="Quote Consolidation Manager",
    goal="Assemble comprehensive professional quotes from all specialist inputs",
    backstory="You are a project manager who specializes in creating professional, detailed quotes. You excel at consolidating technical information into clear, actionable proposals for clients.",
    llm=llm,
    verbose=True
)

def create_tasks(shipment_details):
    """Create the four sequential tasks with shipment details"""
    
    briefing_task = Task(
        description=f"""
        Analyze the following shipment details and create a comprehensive briefing:
        
        {shipment_details}
        
        Your task:
        1. Validate all provided information
        2. Identify any critical missing details
        3. Provide recommendations for information gathering
        4. Create a comprehensive briefing for the packaging and logistics teams
        
        Focus on accuracy and completeness for professional quote generation.
        """,
        agent=sales_briefing_agent,
        expected_output="Comprehensive shipment analysis with validation, missing details identification, and team briefing"
    )
    
    crating_task = Task(
        description="""
        Based on the shipment briefing, design an optimal crating solution:
        
        Your task:
        1. Analyze the item's protection requirements
        2. Design appropriate crating/packaging solution
        3. Select optimal materials (wood, foam, steel, etc.)
        4. Calculate material costs and labor requirements
        5. Consider any special handling needs
        6. Provide detailed specifications and cost breakdown
        
        Focus on cost-effective protection that ensures safe delivery.
        """,
        agent=crating_design_agent,
        expected_output="Detailed crating design with specifications, materials list, and cost breakdown"
    )
    
    logistics_task = Task(
        description="""
        Based on the shipment briefing and crating design, create a logistics plan:
        
        Your task:
        1. Determine optimal transportation mode (ground, air, sea)
        2. Plan optimal routes considering distance, time, and cost
        3. Calculate freight costs from multiple carriers
        4. Identify any customs, permits, or compliance requirements
        5. Account for insurance needs
        6. Provide delivery timeline estimates
        7. Consider any special handling during transport
        
        Focus on reliable, cost-effective delivery within timeline requirements.
        """,
        agent=logistics_planner_agent,
        expected_output="Comprehensive logistics plan with routing, costs, timelines, and compliance requirements"
    )
    
    quote_task = Task(
        description="""
        Consolidate all information into a professional quote:
        
        Using the shipment briefing, crating design, and logistics plan, create a comprehensive quote that includes:
        
        1. Executive summary of the shipment
        2. Detailed packaging solution and costs
        3. Transportation plan and freight costs
        4. Timeline and delivery schedule
        5. Insurance and compliance requirements
        6. Total cost breakdown
        7. Terms and conditions
        8. Next steps for approval
        
        Format as a professional, client-ready quote document.
        """,
        agent=quote_consolidator_agent,
        expected_output="Professional, comprehensive quote document ready for client presentation"
    )
    
    return [briefing_task, crating_task, logistics_task, quote_task]

if __name__ == "__main__":
    try:
        # Get shipment details from user
        shipment_details = get_shipment_details()
        
        # Create tasks with the shipment details
        tasks = create_tasks(shipment_details)
        
        # Create and execute the crew
        print("\n=== Starting AI Quote Generation ===")
        print("Our specialist agents are now working on your quote...\n")
        
        crew = Crew(
            agents=[sales_briefing_agent, crating_design_agent, logistics_planner_agent, quote_consolidator_agent],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Output the final quote
        print("\n" + "="*60)
        print("FINAL TRANSPAK QUOTE")
        print("="*60)
        print(result)
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nQuote generation cancelled by user.")
    except Exception as e:
        print(f"\nError generating quote: {str(e)}")
        print("Please check your API key and try again.")