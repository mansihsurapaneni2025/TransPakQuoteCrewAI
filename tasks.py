from crewai import Task

class TransPakTasks:
    
    def gather_shipment_details_task(self, agent, shipment_info):
        """
        Task for Sales Briefing Agent to process and validate shipment information
        """
        return Task(
            description=f"""
            Analyze the following shipment information and identify any missing details 
            that would be critical for accurate quoting:
            
            Shipment Details:
            - Item Description: {shipment_info.get('item_description', 'Not provided')}
            - Dimensions (L x W x H): {shipment_info.get('dimensions', 'Not provided')}
            - Weight: {shipment_info.get('weight', 'Not provided')}
            - Origin: {shipment_info.get('origin', 'Not provided')}
            - Destination: {shipment_info.get('destination', 'Not provided')}
            - Fragility Level: {shipment_info.get('fragility', 'Not provided')}
            - Special Requirements: {shipment_info.get('special_requirements', 'None specified')}
            - Timeline: {shipment_info.get('timeline', 'Not provided')}
            
            Your task is to:
            1. Validate all provided information
            2. Identify any critical missing details
            3. Provide recommendations for information gathering
            4. Prepare a comprehensive briefing for the packaging and logistics teams
            """,
            agent=agent,
            expected_output="A structured analysis of the shipment requirements with validation status and recommendations"
        )
    
    def design_crating_solution_task(self, agent, shipment_briefing):
        """
        Task for Crating Design Agent to create packaging solution
        """
        return Task(
            description=f"""
            Based on the shipment briefing, design an optimal crating solution:
            
            Briefing Information: {shipment_briefing}
            
            Your task is to:
            1. Analyze the item's protection requirements
            2. Design appropriate crating/packaging solution
            3. Select optimal materials (wood, foam, steel, etc.)
            4. Calculate material costs and labor requirements
            5. Consider any special handling needs
            6. Provide detailed specifications and cost breakdown
            
            Consider factors like:
            - Item fragility and value
            - Environmental conditions during transport
            - Handling requirements
            - Cost optimization while maintaining protection
            """,
            agent=agent,
            expected_output="Detailed crating design with specifications, materials list, and cost breakdown"
        )
    
    def plan_logistics_task(self, agent, shipment_briefing, crating_design):
        """
        Task for Logistics Planner Agent to determine shipping strategy
        """
        return Task(
            description=f"""
            Plan the optimal logistics solution based on:
            
            Shipment Briefing: {shipment_briefing}
            Crating Design: {crating_design}
            
            Your task is to:
            1. Determine the best transportation mode (truck, rail, air, ocean)
            2. Plan optimal routes considering distance, time, and cost
            3. Calculate freight costs from multiple carriers
            4. Identify any customs, permits, or compliance requirements
            5. Account for insurance needs
            6. Provide delivery timeline estimates
            7. Consider any special handling during transport
            
            Factors to consider:
            - Total package dimensions and weight after crating
            - Destination accessibility
            - Time sensitivity
            - Cost optimization
            - Regulatory compliance
            """,
            agent=agent,
            expected_output="Comprehensive logistics plan with route options, cost breakdown, and timeline"
        )
    
    def consolidate_quote_task(self, agent, shipment_briefing, crating_design, logistics_plan):
        """
        Task for Quote Consolidator Agent to create final quote
        """
        return Task(
            description=f"""
            Create a comprehensive, professional quote by consolidating all information:
            
            Shipment Briefing: {shipment_briefing}
            Crating Design: {crating_design}
            Logistics Plan: {logistics_plan}
            
            Your task is to:
            1. Compile all cost components (materials, labor, freight, insurance)
            2. Apply TransPak's business rules and profit margins (15-25% markup)
            3. Create multiple service tier options (Economy, Standard, Premium)
            4. Include detailed line items and explanations
            5. Add terms and conditions
            6. Format as a professional quote document
            7. Include timeline and next steps
            
            Business Rules:
            - Standard markup: 20%
            - Economy option: 15% markup, longer timeline
            - Premium option: 25% markup, expedited service
            - Insurance: 1-3% of item value
            - Include contingency buffer: 5-10%
            """,
            agent=agent,
            expected_output="Professional quote document with multiple service options and detailed cost breakdown"
        )
