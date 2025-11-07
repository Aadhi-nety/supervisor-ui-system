import asyncio
import logging
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero

from help_requests.service import HelpRequestService
from knowledge_base.service import KnowledgeBaseService
from .prompts import SALON_BASE_PROMPT, UNCERTAINTY_TRIGGERS
from config import Config

logger = logging.getLogger(__name__)

class LiveKitSalonAgent:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.help_service = HelpRequestService()
        
        # Initialize the voice agent with OpenAI (for STT/TTS) and Groq for LLM
        self.agent = VoicePipelineAgent(
            llm=openai.LLM(model="gpt-3.5-turbo"),  # Using OpenAI for compatibility
            stt=openai.STT(),
            tts=openai.TTS(),
            vad=silero.VAD.load(),
            prompt=SALON_BASE_PROMPT
        )
        
        self.current_customer_phone = None
        self.conversation_history = []
    
    async def handle_call(self, ctx: JobContext):
        """Handle incoming phone calls via LiveKit"""
        logger.info("📞 LiveKit: Incoming call received")
        
        try:
            await ctx.connect()
            
            # Simulate customer phone number
            self.current_customer_phone = "+15551234567"
            
            @ctx.room.on("participant_connected")
            def on_participant_connected(participant):
                if participant.identity == "caller":
                    logger.info(f"📞 LiveKit: Caller connected: {participant.identity}")
                    asyncio.create_task(self._start_conversation(ctx))
            
            # Monitor for transcription events to detect uncertainty
            @ctx.room.on("track_subscribed")
            def on_track_subscribed(track, publication, participant):
                if track.kind == "audio" and participant.identity == "caller":
                    logger.info("📞 LiveKit: Audio track subscribed")
            
            # Wait for call to end
            await asyncio.sleep(3600)  # 1 hour timeout
            
        except Exception as e:
            logger.error(f"📞 LiveKit: Error handling call: {e}")
        finally:
            logger.info("📞 LiveKit: Call ended")
            self.current_customer_phone = None
            self.conversation_history = []
    
    async def _start_conversation(self, ctx: JobContext):
        """Start conversation with caller"""
        try:
            await self.agent.start(ctx.room, AutoSubscribe.SUBSCRIBE_ALL)
            
            # Set up monitoring for AI responses
            self.agent.llm.chat_ctx.on("message_added", self._handle_ai_response)
            
            logger.info("🤖 LiveKit: AI Agent started and ready")
            
        except Exception as e:
            logger.error(f"🤖 LiveKit: Error starting conversation: {e}")
    
    async def _handle_ai_response(self, message: ChatMessage):
        """Monitor AI responses and detect when help is needed"""
        if message.role == "assistant":
            logger.info(f"🤖 AI Response: {message.content}")
            self.conversation_history.append(f"AI: {message.content}")
            
            # Check if AI is uncertain
            message_lower = message.content.lower()
            if any(trigger in message_lower for trigger in UNCERTAINTY_TRIGGERS):
                logger.info("🆘 LiveKit: AI uncertainty detected - escalating to supervisor")
                await self._escalate_to_supervisor(self._extract_question_from_context())
    
    def _extract_question_from_context(self) -> str:
        """Extract the customer's question from conversation context"""
        if len(self.conversation_history) >= 2:
            for msg in reversed(self.conversation_history):
                if msg.startswith("Customer:"):
                    return msg.replace("Customer:", "").strip()
        return "Unknown question from voice call"
    
    async def _escalate_to_supervisor(self, question: str):
        """Escalate unknown question to supervisor"""
        try:
            if not self.current_customer_phone:
                logger.error("📞 LiveKit: No current customer phone for escalation")
                return
            
            # Create help request
            help_request = await self.help_service.create_help_request(
                customer_phone=self.current_customer_phone,
                question=question,
                context="LiveKit Voice Call - AI couldn't answer"
            )
            
            # Notify supervisor
            self._notify_supervisor(help_request)
            
            logger.info(f"🆘 LiveKit: Help request created: {help_request.id}")
            
        except Exception as e:
            logger.error(f"📞 LiveKit: Error escalating to supervisor: {e}")
    
    def _notify_supervisor(self, help_request):
        """Simulate texting supervisor"""
        message = f"🆘 LIVEKIT CALL - HELP NEEDED\nQuestion: {help_request.question}\nCustomer: {help_request.customer_phone}\nRequest ID: {help_request.id}\n\nReply at: http://localhost:5000/request/{help_request.id}"
        print(f"\n{'='*60}")
        print("📱 SIMULATED SMS TO SUPERVISOR:")
        print(message)
        print(f"{'='*60}\n")
    
    async def handle_supervisor_response(self, request_id: str, answer: str):
        """Handle supervisor's response and follow up with customer"""
        try:
            help_request = await self.help_service.get_help_request(request_id)
            if help_request:
                await self.kb_service.add_entry(help_request.question, answer, "supervisor")
                
                # Simulate texting customer back
                self._notify_customer(help_request, answer)
                
                logger.info(f"✅ LiveKit: Processed supervisor response for request {request_id}")
            
        except Exception as e:
            logger.error(f"📞 LiveKit: Error handling supervisor response: {e}")
    
    def _notify_customer(self, help_request, answer: str):
        """Simulate texting customer back with the answer"""
        message = f"Hi! Following up on your question about '{help_request.question}'. Here's the answer: {answer}"
        print(f"\n{'='*60}")
        print("📱 SIMULATED SMS TO CUSTOMER:")
        print(f"To: {help_request.customer_phone}")
        print(f"Message: {message}")
        print(f"{'='*60}\n")


async def start_livekit_worker():
    """Start the LiveKit worker"""
    agent = LiveKitSalonAgent()
    
    # Define the worker
    async def worker(ctx: JobContext):
        await agent.handle_call(ctx)
    
    return worker

if __name__ == "__main__":
    # Start the LiveKit worker
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        worker = await start_livekit_worker()
        await cli.run_app(WorkerOptions(agent=worker))
    
    asyncio.run(main())