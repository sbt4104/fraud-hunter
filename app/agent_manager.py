import uuid
import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models import Agent, Event, Analysis, AgentStatus, EventType
from app.database import VectorStore
from app.workflow import FraudWorkflow

class FraudAlert:
    """Enhanced alert model with detailed explanations"""
    def __init__(self, alert_id: str, event: Event, analysis: Analysis, agent_id: str):
        self.alert_id = alert_id
        self.timestamp = datetime.utcnow()
        self.event_id = event.event_id
        self.agent_id = agent_id
        self.account_id = event.account_id
        self.risk_score = analysis.risk_score
        self.severity = self._calculate_severity(analysis.risk_score)
        self.status = "NEW"
        
        # Detailed explanation data
        self.event_details = {
            "event_type": event.event_type,
            "account_id": event.account_id,
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "device_id": event.device_id,
            "timestamp": event.timestamp.isoformat(),
            "event_data": event.event_data,
            "anomaly_flags": event.anomaly_flags
        }
        
        self.analysis_details = {
            "fraud_indicators": analysis.fraud_indicators,
            "reasoning": analysis.reasoning,
            "recommended_actions": analysis.recommended_actions,
            "risk_breakdown": self._create_risk_breakdown(analysis),
            "similar_events_count": len(getattr(analysis, 'supporting_events', []))
        }
    
    def _calculate_severity(self, risk_score: float) -> str:
        if risk_score >= 0.9:
            return "CRITICAL"
        elif risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _create_risk_breakdown(self, analysis: Analysis) -> Dict[str, str]:
        """Create detailed risk breakdown explanation"""
        breakdown = {}
        
        # Analyze fraud indicators
        for indicator in analysis.fraud_indicators:
            if "unusual_time" in indicator.lower():
                breakdown["temporal_risk"] = "Event occurred outside normal business hours"
            elif "ip_mismatch" in indicator.lower():
                breakdown["location_risk"] = "IP address differs from historical login patterns"
            elif "rapid_succession" in indicator.lower():
                breakdown["behavioral_risk"] = "Multiple events in rapid succession detected"
            elif "amount" in indicator.lower():
                breakdown["transaction_risk"] = "Transaction amount outside normal range"
            elif "device" in indicator.lower():
                breakdown["device_risk"] = "Unrecognized or suspicious device"
        
        # Add general risk factors
        if analysis.risk_score > 0.8:
            breakdown["overall_assessment"] = "Multiple high-risk patterns detected simultaneously"
        elif analysis.risk_score > 0.6:
            breakdown["overall_assessment"] = "Significant suspicious activity patterns identified"
        else:
            breakdown["overall_assessment"] = "Some concerning patterns detected"
            
        return breakdown
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary for API responses"""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "account_id": self.account_id,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "status": self.status,
            "event_details": self.event_details,
            "analysis_details": self.analysis_details
        }

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.analyses: List[Analysis] = []
        self.active_alerts: List[FraudAlert] = []  # Enhanced alert storage
        self.vector_store = VectorStore()
        self.workflow = FraudWorkflow()
    
    def create_agent(self, name: str, account_ids: List[str] = None) -> str:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())
        agent = Agent(
            agent_id=agent_id,
            name=name,
            account_ids=account_ids or []
        )
        self.agents[agent_id] = agent
        return agent_id
    
    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        if agent.status == AgentStatus.RUNNING:
            return True
        
        agent.status = AgentStatus.RUNNING
        
        # Start agent task
        task = asyncio.create_task(self._agent_loop(agent_id))
        self.running_tasks[agent_id] = task
        
        return True
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.status = AgentStatus.STOPPED
        
        # Cancel task
        if agent_id in self.running_tasks:
            self.running_tasks[agent_id].cancel()
            del self.running_tasks[agent_id]
        
        return True
    
    async def _agent_loop(self, agent_id: str):
        """Main agent processing loop"""
        agent = self.agents[agent_id]
        
        try:
            while agent.status == AgentStatus.RUNNING:
                # Generate sample events (in real system, fetch from API)
                events = self._generate_sample_events(agent)
                
                for event in events:
                    if agent.status != AgentStatus.RUNNING:
                        break
                    
                    # Process event
                    await self._process_event(agent_id, event)
                    agent.events_processed += 1
                    agent.last_activity = datetime.utcnow()
                
                # Wait before next iteration
                await asyncio.sleep(10)  # 10 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Agent {agent_id} error: {e}")
            agent.status = AgentStatus.ERROR
    
    def _generate_sample_events(self, agent: Agent) -> List[Event]:
        """Generate events to showcase all fraud detection risk levels"""
        events = []
        
        # Generate 1-3 events with different risk profiles
        for _ in range(random.randint(1, 3)):
            account_id = random.choice(agent.account_ids) if agent.account_ids else f"ACC{random.randint(100,999)}"
            
            # Create events targeting different risk levels
            risk_target = random.choice(["low", "medium", "high", "critical"])
            
            if risk_target == "critical":
                # Events that should score 0.8-1.0 (critical fraud)
                event = Event(
                    event_id="EVT45789",
                    timestamp=datetime.utcnow().replace(hour=2, minute=47),  # 2:47 AM
                    event_type=EventType.TRANSACTION,
                    account_id="ACC001",
                    user_id="USER123",
                    ip_address="185.220.101.45",  # Known Tor exit node
                    device_id="UNKNOWN-7834",
                    event_data={
                        "amount": 23500,  # Large amount
                        "merchant": "BITCOIN-EXCHANGE-OFFSHORE",
                        "transaction_time_seconds": 3,  # Suspiciously fast
                        "previous_login": "2 minutes ago",
                        "account_age_days": 1847,  # Old account, sudden change
                        "typical_transaction_amount": 150  # Way above normal
                    }
                )
            elif risk_target == "high":
                # Events that should score 0.6-0.8 (high risk)
                event = Event(
                    event_id=f"EVT{random.randint(10000,99999)}",
                    timestamp=datetime.utcnow().replace(hour=random.choice([1, 2, 23]), minute=random.randint(0,59)),
                    event_type=random.choice([EventType.PASSWORD_RESET, EventType.TRANSACTION]),
                    account_id=account_id,
                    user_id=f"USER{random.randint(100,999)}",
                    ip_address=f"94.142.{random.randint(200,250)}.{random.randint(1,254)}",  # Eastern Europe
                    device_id=f"DEV{random.randint(1000,9999)}",
                    event_data={
                        "amount": random.randint(5000, 12000),
                        "merchant": "INTERNATIONAL-WIRE-TRANSFER",
                        "country": "Nigeria"
                    }
                )
            elif risk_target == "medium":
                # Events that should score 0.3-0.6 (medium risk)
                event = Event(
                    event_id=f"EVT{random.randint(10000,99999)}",
                    timestamp=datetime.utcnow().replace(hour=random.choice([7, 8, 18, 19]), minute=random.randint(0,59)),
                    event_type=EventType.TRANSACTION,
                    account_id=account_id,
                    user_id=f"USER{random.randint(100,999)}",
                    ip_address=f"203.0.113.{random.randint(1,254)}",  # Test IP range
                    device_id=f"DEV{random.randint(1000,9999)}",
                    event_data={
                        "amount": random.randint(1000, 3000),
                        "merchant": "PAYPAL-TRANSFER",
                        "location": "Different-State"
                    }
                )
            else:
                # Events that should score 0.0-0.3 (low risk/normal)
                event = Event(
                    event_id=f"EVT{random.randint(10000,99999)}",
                    timestamp=datetime.utcnow().replace(hour=random.randint(9, 17), minute=random.randint(0,59)),
                    event_type=random.choice([EventType.SIGN_IN, EventType.ACCOUNT_LOOKUP, EventType.TRANSACTION]),
                    account_id=account_id,
                    user_id=f"USER{random.randint(100,999)}",
                    ip_address=f"192.168.{random.randint(1,10)}.{random.randint(1,254)}",  # Corporate IP
                    device_id=f"TRUSTED-{random.randint(1000,9999)}",
                    event_data={
                        "amount": random.randint(10, 200),
                        "merchant": random.choice(["STARBUCKS", "SHELL-GAS", "GROCERY-STORE"]),
                        "card_present": True
                    }
                )
            
            events.append(event)
        
        return events
    
    async def _process_event(self, agent_id: str, event: Event):
        """Process a single event"""
        try:
            # Add to vector store
            await self.vector_store.add_event(event)
            
            # Search for similar events
            search_query = f"Event: {event.event_type} Account: {event.account_id}"
            similar_events = await self.vector_store.search_similar(search_query, limit=5)
            
            # Analyze with workflow
            result = await self.workflow.analyze_event(event, similar_events)
            
            # Create analysis record
            analysis = Analysis(
                analysis_id=str(uuid.uuid4()),
                agent_id=agent_id,
                event_id=event.event_id,
                timestamp=datetime.utcnow(),
                risk_score=result["risk_score"],
                fraud_indicators=result["fraud_indicators"],
                reasoning=result["reasoning"],
                recommended_actions=result["actions"]
            )
            
            # Add supporting events for context
            analysis.supporting_events = similar_events
            
            self.analyses.append(analysis)
            
            # Enhanced alert handling
            if result["risk_score"] > 0.7:
                await self._handle_high_risk_alert(agent_id, event, analysis)
            elif result["risk_score"] > 0.5:
                await self._handle_medium_risk_alert(agent_id, event, analysis)
            
            # Keep only recent analyses (last 100)
            if len(self.analyses) > 100:
                self.analyses = self.analyses[-100:]
                
        except Exception as e:
            print(f"Error processing event: {e}")
    
    async def _handle_high_risk_alert(self, agent_id: str, event: Event, analysis: Analysis):
        """Handle high-risk alerts with detailed tracking"""
        self.agents[agent_id].alerts_generated += 1
        
        # Create detailed alert
        alert = FraudAlert(
            alert_id=str(uuid.uuid4()),
            event=event,
            analysis=analysis,
            agent_id=agent_id
        )
        
        self.active_alerts.append(alert)
        
        # Enhanced logging
        print(f"🚨 HIGH RISK ALERT: {event.event_id} - Score: {analysis.risk_score:.2f}")
        print(f"   Account: {event.account_id} | IP: {event.ip_address}")
        print(f"   Indicators: {', '.join(analysis.fraud_indicators)}")
        print(f"   Reasoning: {analysis.reasoning[:100]}...")
        
        # Execute recommended actions
        await self._execute_recommended_actions(event, analysis)
        
        # Keep only recent alerts (last 50)
        if len(self.active_alerts) > 50:
            self.active_alerts = self.active_alerts[-50:]
    
    async def _handle_medium_risk_alert(self, agent_id: str, event: Event, analysis: Analysis):
        """Handle medium-risk events"""
        print(f"⚠️ MEDIUM RISK: {event.event_id} - Score: {analysis.risk_score:.2f}")
        
        # Create alert but with lower priority
        alert = FraudAlert(
            alert_id=str(uuid.uuid4()),
            event=event,
            analysis=analysis,
            agent_id=agent_id
        )
        
        self.active_alerts.append(alert)
    
    async def _execute_recommended_actions(self, event: Event, analysis: Analysis):
        """Execute recommended actions automatically"""
        for action in analysis.recommended_actions:
            try:
                if action == "immediate_block":
                    await self._block_account(event.account_id)
                elif action == "additional_verification":
                    await self._flag_for_verification(event.account_id)
                elif action == "preserve_evidence":
                    await self._preserve_event_evidence(event)
                elif action == "security_review":
                    await self._create_security_review(event, analysis)
                    
            except Exception as e:
                print(f"Failed to execute action {action}: {e}")
    
    async def _block_account(self, account_id: str):
        """Simulate account blocking"""
        print(f"🔒 ACTION: Blocking account {account_id}")
        # In real system: call account management API
    
    async def _flag_for_verification(self, account_id: str):
        """Simulate flagging for verification"""
        print(f"⚠️ ACTION: Flagging {account_id} for additional verification")
        # In real system: add to verification queue
    
    async def _preserve_event_evidence(self, event: Event):
        """Simulate evidence preservation"""
        print(f"📁 ACTION: Preserving evidence for event {event.event_id}")
        # In real system: backup to secure storage
    
    async def _create_security_review(self, event: Event, analysis: Analysis):
        """Simulate security review creation"""
        print(f"👮 ACTION: Creating security review for {event.account_id}")
        # In real system: create ticket in security system
    
    def get_agents(self) -> List[Agent]:
        """Get all agents"""
        return list(self.agents.values())
    
    def get_agent(self, agent_id: str) -> Agent:
        """Get specific agent"""
        return self.agents.get(agent_id)
    
    def get_recent_analyses(self, limit: int = 20) -> List[Analysis]:
        """Get recent analyses"""
        return sorted(self.analyses, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        """Get active alerts with details"""
        recent_alerts = sorted(self.active_alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [alert.to_dict() for alert in recent_alerts]
    
    def get_alert_details(self, alert_id: str) -> Optional[Dict]:
        """Get detailed alert information"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                return alert.to_dict()
        return None
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.status = "ACKNOWLEDGED"
                return True
        return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id not in self.agents:
            return False
        
        # Stop agent first
        asyncio.create_task(self.stop_agent(agent_id))
        
        # Remove from storage
        del self.agents[agent_id]
        return True

# Global instance
agent_manager = AgentManager()