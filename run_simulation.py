#!/usr/bin/env python3
\"\"\"
Simulation script for testing the AI Supervisor system
\"\"\"

import asyncio
import logging
from help_requests.service import HelpRequestService
from knowledge_base.service import KnowledgeBaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_simulation():
    \"\"\"Run a complete simulation of the system\"\"\"
    logger.info(\"Starting system simulation...\")
    
    help_service = HelpRequestService()
    kb_service = KnowledgeBaseService()
    
    test_questions = [
        \"Do you offer keratin treatments?\",
        \"What brand of hair color do you use?\",
        \"Do you have any discounts for students?\",
        \"Can I bring my own nail polish?\",
        \"Do you offer gift certificates?\",
        \"What's your cancellation policy?\",
        \"Do you work with curly hair?\",
        \"Are your products cruelty-free?\",
    ]
    
    logger.info(\"Simulating customer calls...\")
    
    for i, question in enumerate(test_questions, 1):
        logger.info(f\"Call {i}: {question}\")
        
        kb_answer = await kb_service.find_answer(question)
        if kb_answer:
            logger.info(f\"AI knew the answer: {kb_answer}\")
        else:
            logger.info(\"AI doesn't know - escalating to supervisor...\")
            
            help_request = await help_service.create_help_request(
                customer_phone=f\"+1555000{i:04d}\",
                question=question
            )
            
            logger.info(f\"Created help request: {help_request.id}\")
            
            await asyncio.sleep(2)
            
            answer = f\"This is a simulated answer for: {question}. We should add this to our services!\"
            resolved_request = await help_service.resolve_request(help_request.id, answer)
            
            logger.info(f\"Supervisor resolved request: {answer[:50]}...\")
    
    pending_requests = await help_service.get_pending_requests()
    resolved_requests = await help_service.get_resolved_requests()
    knowledge_entries = await kb_service.get_all_entries()
    
    logger.info(\"Simulation Complete!\")
    logger.info(f\"Pending requests: {len(pending_requests)}\")
    logger.info(f\"Resolved requests: {len(resolved_requests)}\")
    logger.info(f\"Knowledge base entries: {len(knowledge_entries)}\")
    
    logger.info(\"Visit http://localhost:5000 to see the supervisor dashboard\")

if __name__ == \"__main__\":
    asyncio.run(run_simulation())
