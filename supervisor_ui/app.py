from flask import Flask, render_template, request, jsonify, redirect, url_for
import asyncio
import logging
import uuid
from datetime import datetime
from help_requests.service import HelpRequestService
from knowledge_base.service import KnowledgeBaseService
from ai_agent.simple_groq_agent import SimpleGroqAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask app instance
app = Flask(__name__)

# Initialize services
help_service = HelpRequestService()
kb_service = KnowledgeBaseService()
ai_agent = SimpleGroqAgent()

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/')
def dashboard():
    try:
        pending_requests = run_async(help_service.get_pending_requests())
        resolved_requests = run_async(help_service.get_resolved_requests())[:5]
        
        # Safely get knowledge entries
        try:
            knowledge_entries = run_async(kb_service.get_all_entries())[:5]
        except Exception as e:
            logger.warning(f"Could not load knowledge entries: {e}")
            knowledge_entries = []
        
        stats = {
            'pending': len(pending_requests),
            'resolved': len(resolved_requests),
            'knowledge_entries': len(knowledge_entries)
        }
        
        return render_template('dashboard.html', 
                             pending_requests=pending_requests,
                             resolved_requests=resolved_requests,
                             knowledge_entries=knowledge_entries,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e))

@app.route('/requests')
def all_requests():
    try:
        pending_requests = run_async(help_service.get_pending_requests())
        resolved_requests = run_async(help_service.get_resolved_requests())
        
        return render_template('all_requests.html', 
                             pending_requests=pending_requests,
                             resolved_requests=resolved_requests)
    except Exception as e:
        logger.error(f"Error loading requests: {e}")
        return render_template('error.html', error=str(e))

@app.route('/request/<request_id>')
def view_request(request_id):
    try:
        help_request = run_async(help_service.get_help_request(request_id))
        if not help_request:
            return render_template('error.html', error='Request not found'), 404
        
        return render_template('request_detail.html', request=help_request)
    except Exception as e:
        logger.error(f"Error loading request {request_id}: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/request/<request_id>/respond', methods=['POST'])
def respond_to_request(request_id):
    try:
        answer = request.form.get('answer')
        if not answer:
            return render_template('error.html', error='Answer required'), 400
        
        # Resolve the request
        help_request = run_async(help_service.resolve_request(request_id, answer))
        
        # Add to knowledge base
        run_async(kb_service.add_entry(help_request.question, answer, 'supervisor'))
        
        # Notify AI agent
        run_async(ai_agent.handle_supervisor_response(request_id, answer))
        
        return redirect(url_for('view_request', request_id=request_id))
    
    except Exception as e:
        logger.error(f"Error responding to request {request_id}: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/requests/<request_id>/resolve', methods=['POST'])
def resolve_request(request_id):
    try:
        answer = request.json.get('answer')
        if not answer:
            return jsonify({'error': 'Answer required'}), 400
        
        help_request = run_async(help_service.resolve_request(request_id, answer))
        
        run_async(kb_service.add_entry(help_request.question, answer, 'supervisor'))
        
        run_async(ai_agent.handle_supervisor_response(request_id, answer))
        
        return jsonify({
            'success': True, 
            'request': help_request.to_dict(),
            'message': 'Request resolved and customer notified'
        })
    
    except Exception as e:
        logger.error(f"Error resolving request {request_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/requests/<request_id>/unresolved', methods=['POST'])
def mark_unresolved(request_id):
    try:
        help_request = run_async(help_service.mark_request_unresolved(request_id))
        return jsonify({'success': True, 'request': help_request.to_dict()})
    
    except Exception as e:
        logger.error(f"Error marking request {request_id} as unresolved: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/knowledge')
def knowledge_base():
    try:
        entries = run_async(kb_service.get_all_entries())
        return render_template('knowledge_base.html', entries=entries)
    except Exception as e:
        logger.error(f"Error loading knowledge base: {e}")
        return render_template('knowledge_base.html', entries=[])

@app.route('/api/knowledge/<entry_id>/delete', methods=['POST'])
def delete_knowledge_entry(entry_id):
    try:
        success = run_async(kb_service.delete_entry(entry_id))
        if success:
            return jsonify({'success': True, 'message': 'Entry deleted'})
        else:
            return jsonify({'error': 'Entry not found'}), 404
    
    except Exception as e:
        logger.error(f"Error deleting knowledge entry {entry_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/simulate-call', methods=['POST'])
def simulate_call():
    try:
        question = request.json.get('question', 'Do you offer keratin treatments?')
        
        # FORCE CREATE HELP REQUEST FOR EVERY QUESTION
        logger.info(f"Creating help request for question: {question}")
        
        # Create help request directly
        help_request = run_async(help_service.create_help_request(
            customer_phone="+1 (555) SIMULATED",
            question=question
        ))
        
        # Get AI response (but still create the request)
        response = run_async(ai_agent.process_message(question))
        
        return jsonify({
            'success': True, 
            'message': f'Simulated call with question: {question}',
            'ai_response': response,
            'help_request_id': help_request.id,
            'note': 'Help request created for supervisor review'
        })
    
    except Exception as e:
        logger.error(f"Error simulating call: {e}")
        return jsonify({'error': str(e)}), 500

# NEW ROUTE: Create help request directly without AI
@app.route('/create-help-request', methods=['POST'])
def create_help_request():
    """Create a help request directly"""
    try:
        question = request.json.get('question')
        phone = request.json.get('phone', '+1 (555) UNKNOWN')
        
        if not question:
            return jsonify({'error': 'Question required'}), 400
        
        help_request = run_async(help_service.create_help_request(
            customer_phone=phone,
            question=question
        ))
        
        return jsonify({
            'success': True,
            'request_id': help_request.id,
            'question': question,
            'message': 'Help request created successfully'
        })
    
    except Exception as e:
        logger.error(f"Error creating help request: {e}")
        return jsonify({'error': str(e)}), 500

# DEBUG ROUTES - Add these for troubleshooting
@app.route('/debug-routes')
def debug_routes():
    """Debug page to see all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    
    html = "<h1>Available Routes:</h1><ul>"
    for route in sorted(routes, key=lambda x: x['path']):
        html += f"<li><strong>{route['path']}</strong> - {route['methods']}</li>"
    html += "</ul>"
    return html

@app.route('/debug-requests')
def debug_requests():
    """Debug page to see all available requests"""
    try:
        pending_requests = run_async(help_service.get_pending_requests())
        resolved_requests = run_async(help_service.get_resolved_requests())
        
        html = "<h1>Available Requests:</h1>"
        
        html += "<h2>Pending Requests:</h2><ul>"
        for req in pending_requests:
            html += f"<li><a href='/request/{req.id}'>{req.id[:8]} - {req.question[:50]}...</a></li>"
        html += "</ul>"
        
        html += "<h2>Resolved Requests:</h2><ul>"
        for req in resolved_requests[:10]:  # Show first 10
            html += f"<li><a href='/request/{req.id}'>{req.id[:8]} - {req.question[:50]}...</a></li>"
        html += "</ul>"
        
        return html
    except Exception as e:
        return f"Error loading requests: {str(e)}"

@app.route('/test-request')
def test_request():
    """Test if request detail template works with mock data"""
    from datetime import datetime
    
    class MockRequest:
        id = 'test-12345678'
        customer_phone = '+1 (555) 123-4567'
        question = 'This is a test question to check if the template works.'
        created_at = datetime.now()
        status = 'pending'
        supervisor_answer = None
        resolved_at = None
    
    return render_template('request_detail.html', request=MockRequest())

@app.route('/api/markdown', methods=['POST'])
def render_markdown():
    """API endpoint for markdown preview"""
    try:
        text = request.json.get('text', '')
        # Simple markdown to HTML conversion
        html = text.replace('\n', '<br>')
        return jsonify({'html': html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Supervisor UI on http://localhost:5000")
    logger.info("Using Groq AI Agent - ALL questions will create help requests")
    app.run(debug=True, port=5000, host='0.0.0.0')