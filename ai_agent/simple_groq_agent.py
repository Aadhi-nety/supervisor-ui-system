import asyncio
import logging
import groq
from help_requests.service import HelpRequestService
from knowledge_base.service import KnowledgeBaseService
from ai_agent.prompts import SALON_BASE_PROMPT, UNCERTAINTY_TRIGGERS
from config import Config

logger = logging.getLogger(__name__)

class SimpleGroqAgent:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.help_service = HelpRequestService()
        self.client = groq.AsyncGroq(api_key=Config.GROQ_API_KEY)
        self.conversation_history = [
            {'role': 'system', 'content': SALON_BASE_PROMPT}
        ]
    
    async def process_message(self, user_message: str, customer_phone: str = '+15551234567') -> str:
        logger.info(f'Customer: {user_message}')
        
        # CREATE HELP REQUEST FOR EVERY QUESTION (MODIFIED)
        logger.info(f'Creating help request for all questions: {user_message}')
        await self._create_help_request(user_message, customer_phone)
        
        # Only use knowledge base for exact or very close matches
        kb_answer = await self.kb_service.find_answer(user_message)
        if kb_answer:
            # Only return KB answer if it's a good match
            if self._is_good_match(user_message, kb_answer):
                logger.info(f'Found good answer in knowledge base: {kb_answer}')
                return kb_answer
            else:
                logger.info('KB answer found but not a good match - letting AI handle it')
        
        self.conversation_history.append({'role': 'user', 'content': user_message})
        
        try:
            # Use current Groq models - try different ones if needed
            models_to_try = [
                'llama-3.1-8b-instant',  # Current fast model
                'llama-3.1-70b-versatile',  # More capable model
                'mixtral-8x7b-32768',  # Alternative model
            ]
            
            response = None
            last_error = None
            
            for model in models_to_try:
                try:
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=self.conversation_history,
                        temperature=0.7,
                        max_tokens=500,
                    )
                    break  # Success, exit loop
                except Exception as e:
                    last_error = e
                    logger.warning(f'Model {model} failed: {e}')
                    continue
            
            if not response:
                raise last_error
            
            ai_response = response.choices[0].message.content
            logger.info(f'AI: {ai_response}')
            
            self.conversation_history.append({'role': 'assistant', 'content': ai_response})
            
            # REMOVED THE UNCERTAINTY CHECK - CREATE REQUESTS FOR ALL QUESTIONS
            # if any(trigger in ai_response.lower() for trigger in UNCERTAINTY_TRIGGERS):
            #     logger.info('AI uncertainty detected - escalating to supervisor')
            #     await self._escalate_to_supervisor(user_message, customer_phone)
            #     return 'Let me check with my supervisor and get back to you.'
            
            return ai_response
            
        except Exception as e:
            logger.error(f'Error processing message with Groq: {e}')
            return 'I apologize, but I am having trouble processing your request. Please try again later.'
    
    async def _create_help_request(self, question: str, customer_phone: str):
        """Create help request for EVERY question"""
        try:
            help_request = await self.help_service.create_help_request(
                customer_phone=customer_phone,
                question=question,
                context='Automatic help request for all customer questions'
            )
            
            self._notify_supervisor(help_request)
            
            logger.info(f'Help request created for ALL questions: {help_request.id}')
            
        except Exception as e:
            logger.error(f'Error creating help request: {e}')
    
    def _is_good_match(self, question: str, answer: str) -> bool:
        # Only use KB for very specific, exact matches
        question_lower = question.lower()
        
        # List of questions that should definitely use KB
        exact_matches = [
            'what are your hours',
            'do you take walk ins', 
            'what services do you offer',
            'where are you located',
            'what is your phone number',
            'what is your address'
        ]
        
        return any(exact_q in question_lower for exact_q in exact_matches)
    
    async def _escalate_to_supervisor(self, question: str, customer_phone: str):
        try:
            help_request = await self.help_service.create_help_request(
                customer_phone=customer_phone,
                question=question,
                context='AI could not answer the question'
            )
            
            self._notify_supervisor(help_request)
            
            logger.info(f'Help request created: {help_request.id}')
            
        except Exception as e:
            logger.error(f'Error escalating to supervisor: {e}')
    
    def _notify_supervisor(self, help_request):
        message = f'HELP NEEDED\nQuestion: {help_request.question}\nCustomer: {help_request.customer_phone}\nRequest ID: {help_request.id}\n\nReply at: http://localhost:5000/request/{help_request.id}'
        print(f'\n{"="*60}')
        print('SIMULATED SMS TO SUPERVISOR:')
        print(message)
        print(f'{"="*60}\n')
    
    async def handle_supervisor_response(self, request_id: str, answer: str):
        try:
            help_request = await self.help_service.get_help_request(request_id)
            if help_request:
                await self.kb_service.add_entry(help_request.question, answer, 'supervisor')
                
                self._notify_customer(help_request, answer)
                
                logger.info(f'Processed supervisor response for request {request_id}')
            
        except Exception as e:
            logger.error(f'Error handling supervisor response: {e}')
    
    def _notify_customer(self, help_request, answer: str):
        message = f"Hi! Following up on your question about '{help_request.question}'. Here's the answer: {answer}"
        print(f'\n{"="*60}')
        print('SIMULATED SMS TO CUSTOMER:')
        print(f'To: {help_request.customer_phone}')
        print(f'Message: {message}')
        print(f'{"="*60}\n')

async def test_simple_agent():
    agent = SimpleGroqAgent()
    
    test_messages = [
        'What are your hours?',
        'Do you offer keratin treatments?',
        'How much for a haircut?',
        'What brand of hair color do you use?'
    ]
    
    for message in test_messages:
        print(f'\nTesting: {message}')
        response = await agent.process_message(message)
        print(f'Response: {response}')
        await asyncio.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_simple_agent())