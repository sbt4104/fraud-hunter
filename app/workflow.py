import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from app.models import Event

class FraudWorkflow:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
    
    async def analyze_event(self, event: Event, similar_events: list) -> Dict[str, Any]:
        """Analyze event for fraud"""
        try:
            # Prepare context
            context = f"""
            Current Event:
            - Type: {event.event_type}
            - Account: {event.account_id}
            - IP: {event.ip_address}
            - Risk Score: {event.risk_score}
            
            Similar Events: {len(similar_events)} found
            """
            
            prompt = f"""
            You are a fraud detection expert. Analyze this event for fraud indicators.
            
            {context}
            
            Respond with JSON:
            {{
                "risk_score": 0.0-1.0,
                "fraud_indicators": ["list of indicators"],
                "reasoning": "explanation",
                "actions": ["recommended actions"]
            }}
            """
            
            response = await self.llm.ainvoke(prompt)
            
            try:
                result = json.loads(response.content)
                return result
            except:
                # Fallback if JSON parsing fails
                return {
                    "risk_score": event.risk_score or 0.5,
                    "fraud_indicators": ["analysis_incomplete"],
                    "reasoning": "LLM analysis failed, using fallback",
                    "actions": ["manual_review"]
                }
                
        except Exception as e:
            print(f"Workflow error: {e}")
            return {
                "risk_score": 0.1,
                "fraud_indicators": ["system_error"],
                "reasoning": f"Analysis failed: {e}",
                "actions": ["retry_analysis"]
            }