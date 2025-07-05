import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from app.models import Event

class FraudWorkflow:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
    
    async def analyze_event(self, event: Event, similar_events: list) -> Dict[str, Any]:
        """Analyze event for fraud using pure AI analysis"""
        try:
            # Enhanced context with all available event data
            context = self._build_analysis_context(event, similar_events)
            
            prompt = f"""
            You are an expert fraud detection analyst with deep experience in financial crime patterns. 
            Analyze this event for potential fraud indicators using all available data.
            
            {context}
            
            Provide a thorough analysis covering:
            1. **Behavioral Patterns**: Does this event match normal user behavior?
            2. **Temporal Analysis**: Is the timing suspicious (unusual hours, rapid succession)?
            3. **Geographic/IP Analysis**: Are there location inconsistencies?
            4. **Transaction Patterns**: Are amounts or frequencies unusual?
            5. **Device/Access Patterns**: New or suspicious devices/IPs?
            6. **Historical Context**: How does this compare to similar past events?
            
            Calculate a risk score from 0.0 to 1.0 where:
            - 0.0-0.3: Low risk (normal activity)
            - 0.3-0.6: Medium risk (some concerns)
            - 0.6-0.8: High risk (suspicious patterns)
            - 0.8-1.0: Critical risk (likely fraudulent)
            
            In your reasoning, explain your thought process step-by-step. Why did you assign this risk score? 
            What specific patterns concern you? How do the similar events influence your decision?
            
            Respond ONLY with valid JSON:
            {{
                "risk_score": 0.0-1.0,
                "fraud_indicators": ["specific indicators you identified"],
                "reasoning": "your detailed step-by-step analysis explaining exactly why you assigned this risk score and what patterns you identified",
                "actions": ["specific recommended actions based on your analysis"],
                "confidence": 0.0-1.0
            }}
            """
            
            response = await self.llm.ainvoke(prompt)
            
            try:
                result = json.loads(response.content)
                
                # ONLY validate data types and ranges - DON'T override reasoning
                result = self._validate_result_structure(result)
                
                return result
                
            except json.JSONDecodeError:
                # Only use fallback when LLM completely fails
                print("LLM response parsing failed, using rule-based analysis")
                return self._create_fallback_analysis(event, similar_events)
                
        except Exception as e:
            print(f"Workflow error: {e}")
            return self._create_error_analysis(event, str(e))
    
    def _build_analysis_context(self, event: Event, similar_events: list) -> str:
        """Build comprehensive context for fraud analysis"""
        
        # Current event details
        event_context = f"""
        CURRENT EVENT ANALYSIS:
        - Event ID: {event.event_id}
        - Type: {event.event_type}
        - Timestamp: {event.timestamp} ({event.timestamp.strftime('%A %H:%M')})
        - Account: {event.account_id}
        - User: {event.user_id}
        - IP Address: {event.ip_address}
        - Device: {event.device_id}
        - Source System: {event.source_system}
        """
        
        # Event-specific data
        if event.event_data:
            event_context += f"\n        - Event Data: {json.dumps(event.event_data)}"
        
        # Pre-existing anomaly flags from upstream systems
        if event.anomaly_flags:
            event_context += f"\n        - System Anomaly Flags: {', '.join(event.anomaly_flags)}"
        
        # Similar events context
        similar_context = f"""
        
        HISTORICAL CONTEXT:
        - Similar Events Found: {len(similar_events)}
        """
        
        if similar_events:
            similar_context += "\n        Recent Similar Events:"
            for i, similar_event in enumerate(similar_events[:5], 1):
                metadata = similar_event if isinstance(similar_event, dict) else getattr(similar_event, 'metadata', {})
                similar_context += f"""
            {i}. Event: {metadata.get('event_type', 'unknown')} | Account: {metadata.get('account_id', 'unknown')} 
               IP: {metadata.get('ip_address', 'unknown')} | Time: {metadata.get('timestamp', 'unknown')}"""
        
        return event_context + similar_context
    
    def _validate_result_structure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """ONLY validate structure and data types - don't override LLM reasoning"""
        
        # Ensure required fields exist with defaults
        result.setdefault("risk_score", 0.5)
        result.setdefault("fraud_indicators", [])
        result.setdefault("reasoning", "Analysis completed but reasoning not provided")
        result.setdefault("actions", ["manual_review"])
        result.setdefault("confidence", 0.5)
        
        # ONLY validate data types and ranges - don't change content
        try:
            result["risk_score"] = max(0.0, min(1.0, float(result.get("risk_score", 0.5))))
            result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
        except (ValueError, TypeError):
            result["risk_score"] = 0.5
            result["confidence"] = 0.5
        
        # Ensure lists are actually lists
        if not isinstance(result["fraud_indicators"], list):
            result["fraud_indicators"] = []
        if not isinstance(result["actions"], list):
            result["actions"] = ["manual_review"]
        
        # DO NOT modify reasoning - keep LLM's exact analysis
        
        return result
    
    def _create_fallback_analysis(self, event: Event, similar_events: list) -> Dict[str, Any]:
        """Create fallback analysis when LLM completely fails"""
        
        # Calculate basic risk score based on available data
        risk_score = 0.2  # Base risk
        fraud_indicators = []
        reasoning_parts = []
        
        # Check anomaly flags
        if event.anomaly_flags:
            risk_score += len(event.anomaly_flags) * 0.15
            fraud_indicators.extend(event.anomaly_flags)
            reasoning_parts.append(f"System flagged {len(event.anomaly_flags)} anomalies: {', '.join(event.anomaly_flags)}")
        
        # Check time
        hour = event.timestamp.hour
        if hour < 6 or hour > 22:
            risk_score += 0.2
            fraud_indicators.append("unusual_time")
            reasoning_parts.append(f"Event occurred at {hour}:00, which is outside normal business hours")
        
        # Check IP patterns
        if event.ip_address and ('203.0.113.' in event.ip_address or '198.51.100.' in event.ip_address):
            risk_score += 0.3
            fraud_indicators.append("suspicious_ip_range")
            reasoning_parts.append(f"IP address {event.ip_address} is from a suspicious range")
        
        # Check transaction amount
        amount = event.event_data.get("amount", 0) if event.event_data else 0
        if amount > 5000:
            risk_score += 0.2
            fraud_indicators.append("large_transaction_amount")
            reasoning_parts.append(f"Transaction amount of ${amount} exceeds normal thresholds")
        
        # Check similar events
        if len(similar_events) > 5:
            risk_score += 0.1
            fraud_indicators.append("frequent_similar_activity")
            reasoning_parts.append(f"Found {len(similar_events)} similar events suggesting potential pattern")
        
        risk_score = min(1.0, risk_score)
        
        # Create reasoning from rule-based analysis
        reasoning = "FALLBACK RULE-BASED ANALYSIS: " + ". ".join(reasoning_parts) if reasoning_parts else "FALLBACK ANALYSIS: Standard security review recommended due to LLM analysis failure."
        
        return {
            "risk_score": risk_score,
            "fraud_indicators": fraud_indicators,
            "reasoning": reasoning,  # Clear this is fallback, not LLM reasoning
            "actions": self._determine_actions_from_risk(risk_score),
            "confidence": 0.6
        }
    
    def _create_error_analysis(self, event: Event, error_msg: str) -> Dict[str, Any]:
        """Create analysis when system error occurs"""
        return {
            "risk_score": 0.5,
            "fraud_indicators": ["analysis_error"],
            "reasoning": f"SYSTEM ERROR: Analysis could not be completed due to technical error: {error_msg}. Manual review is required to assess this event properly.",
            "actions": ["manual_review", "retry_analysis"],
            "confidence": 0.1
        }
    
    def _determine_actions_from_risk(self, risk_score: float) -> List[str]:
        """Determine actions based on risk score"""
        if risk_score > 0.8:
            return ["immediate_block", "security_review", "preserve_evidence"]
        elif risk_score > 0.6:
            return ["additional_verification", "increased_monitoring"]
        elif risk_score > 0.4:
            return ["monitor_closely", "log_for_review"]
        else:
            return ["continue_normal_processing"]