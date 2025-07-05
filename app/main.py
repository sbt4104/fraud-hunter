import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.agent_manager import agent_manager

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
   # Startup
   print("🚀 Fraud Detection System starting...")
   demo_agent_id = agent_manager.create_agent("Demo Agent", ["ACC001", "ACC002", "ACC003"])
   print(f"Created demo agent: {demo_agent_id}")
   yield
   # Shutdown
   print("Shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(title="Fraud Detection System", lifespan=lifespan)

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================================
# WEB ROUTES (HTML Pages)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
   """Main dashboard"""
   agents = agent_manager.get_agents()
   analyses = agent_manager.get_recent_analyses(10)
   
   stats = {
       "total_agents": len(agents),
       "running_agents": len([a for a in agents if a.status == "running"]),
       "total_events": sum(a.events_processed for a in agents),
       "high_risk_alerts": len([a for a in analyses if a.risk_score > 0.7])
   }
   
   return templates.TemplateResponse("index.html", {
       "request": request,
       "agents": agents,
       "analyses": analyses,
       "stats": stats
   })

@app.post("/create_agent")
async def create_agent(name: str = Form(...), account_ids: str = Form("")):
   """Create a new agent (Form submission)"""
   account_list = [aid.strip() for aid in account_ids.split(",") if aid.strip()]
   agent_id = agent_manager.create_agent(name, account_list)
   return RedirectResponse(url="/", status_code=303)

@app.post("/start_agent/{agent_id}")
async def start_agent(agent_id: str):
   """Start an agent (Form submission)"""
   success = await agent_manager.start_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return RedirectResponse(url="/", status_code=303)

@app.post("/stop_agent/{agent_id}")
async def stop_agent(agent_id: str):
   """Stop an agent (Form submission)"""
   success = await agent_manager.stop_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return RedirectResponse(url="/", status_code=303)

@app.post("/delete_agent/{agent_id}")
async def delete_agent(agent_id: str):
   """Delete an agent (Form submission)"""
   success = agent_manager.delete_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return RedirectResponse(url="/", status_code=303)

# ============================================================================
# API ROUTES (JSON Endpoints for AJAX)
# ============================================================================

@app.get("/api/status")
async def api_status():
   """API status endpoint"""
   agents = agent_manager.get_agents()
   return {
       "status": "running",
       "agents": len(agents),
       "running_agents": len([a for a in agents if a.status == "running"]),
       "total_events": len(agent_manager.active_alerts),
   }

@app.get("/api/agents")
async def api_list_agents():
   """API endpoint for agents list"""
   agents = agent_manager.get_agents()
   return [agent.dict() for agent in agents]

@app.get("/api/analyses")
async def api_list_analyses():
   """API endpoint for recent analyses"""
   analyses = agent_manager.get_recent_analyses(20)
   return [analysis.dict() for analysis in analyses]

@app.post("/api/agents/{agent_id}/start")
async def api_start_agent(agent_id: str):
   """API endpoint to start agent"""
   success = await agent_manager.start_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return {"success": True, "message": "Agent started"}

@app.post("/api/agents/{agent_id}/stop")
async def api_stop_agent(agent_id: str):
   """API endpoint to stop agent"""
   success = await agent_manager.stop_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return {"success": True, "message": "Agent stopped"}

@app.delete("/api/agents/{agent_id}")
async def api_delete_agent(agent_id: str):
   """API endpoint to delete agent"""
   success = agent_manager.delete_agent(agent_id)
   if not success:
       raise HTTPException(status_code=404, detail="Agent not found")
   return {"success": True, "message": "Agent deleted"}

@app.post("/api/agents")
async def api_create_agent(agent_data: dict):
   """API endpoint to create agent"""
   name = agent_data.get("name")
   account_ids = agent_data.get("account_ids", [])
   
   if not name:
       raise HTTPException(status_code=400, detail="Name is required")
   
   agent_id = agent_manager.create_agent(name, account_ids)
   return {"success": True, "agent_id": agent_id, "message": "Agent created"}

@app.get("/api/analyses/{analysis_id}")
async def api_get_analysis(analysis_id: str):
   """API endpoint for specific analysis"""
   analyses = agent_manager.get_recent_analyses(1000)
   analysis = next((a for a in analyses if a.analysis_id == analysis_id), None)
   
   if not analysis:
       raise HTTPException(status_code=404, detail="Analysis not found")
   
   return analysis.dict()

@app.get("/api/alerts")
async def api_get_alerts():
    """Get active alerts with detailed explanations"""
    alerts = agent_manager.get_active_alerts(50)
    return alerts

@app.get("/api/alerts/{alert_id}")
async def api_get_alert_details(alert_id: str):
    """Get detailed alert information"""
    alert = agent_manager.get_alert_details(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@app.post("/api/alerts/{alert_id}/acknowledge")
async def api_acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    success = agent_manager.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "message": "Alert acknowledged"}

@app.get("/api/status")
async def api_status():
    """Enhanced API status endpoint"""
    agents = agent_manager.get_agents()
    alerts = agent_manager.get_active_alerts(100)
    
    return {
        "status": "running",
        "agents": len(agents),
        "running_agents": len([a for a in agents if a.status == "running"]),
        "total_events": sum(a.events_processed for a in agents),
        "high_risk_alerts": sum(a.alerts_generated for a in agents),
        "active_alerts": len([a for a in alerts if a["status"] == "NEW"]),
        "critical_alerts": len([a for a in alerts if a["severity"] == "CRITICAL"])
    }

if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)