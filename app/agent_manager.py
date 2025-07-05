import uuid
import asyncio
import random
from typing import Dict, List
from datetime import datetime, timedelta
from app.models import Agent, Event, Analysis, AgentStatus, EventType
from app.database import VectorStore
from app.workflow import FraudWorkflow

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.analyses: List[Analysis] = []
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
        """Generate sample events for demonstration"""
        events = []
        
        # Generate 1-3 sample events
        for _ in range(random.randint(1, 3)):
            account_id = random.choice(agent.account_ids) if agent.account_ids else f"ACC{random.randint(100,999)}"
            
            event = Event(
                event_id=f"EVT{random.randint(10000,99999)}",
                timestamp=datetime.utcnow(),
                event_type=random.choice(list(EventType)),
                account_id=account_id,
                user_id=f"USER{random.randint(100,999)}",
                ip_address=f"192.168.1.{random.randint(1,254)}",
                device_id=f"DEV{random.randint(1000,9999)}",
                risk_score=random.random(),
                event_data={"amount": random.randint(10, 1000)},
                anomaly_flags=random.choice([[], ["unusual_time"], ["ip_mismatch"]])
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
            
            self.analyses.append(analysis)
            
            # Check if high risk
            if result["risk_score"] > 0.7:
                self.agents[agent_id].alerts_generated += 1
                print(f"🚨 HIGH RISK ALERT: {event.event_id} - Score: {result['risk_score']:.2f}")
            
            # Keep only recent analyses (last 100)
            if len(self.analyses) > 100:
                self.analyses = self.analyses[-100:]
                
        except Exception as e:
            print(f"Error processing event: {e}")
    
    def get_agents(self) -> List[Agent]:
        """Get all agents"""
        return list(self.agents.values())
    
    def get_agent(self, agent_id: str) -> Agent:
        """Get specific agent"""
        return self.agents.get(agent_id)
    
    def get_recent_analyses(self, limit: int = 20) -> List[Analysis]:
        """Get recent analyses"""
        return sorted(self.analyses, key=lambda x: x.timestamp, reverse=True)[:limit]
    
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