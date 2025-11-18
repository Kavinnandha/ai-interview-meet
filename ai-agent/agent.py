"""English Teacher Agent with Gemini API

An English teacher AI that helps Tamil speakers learn English using Google's Gemini API.

DEPENDENCIES INSTALLATION:
Before running this agent, install the required dependencies:
    pip install -r requirements.txt

FEATURES:
- Voice conversation with Google Gemini 2.0 Flash Live-001 (Free Tier - UNLIMITED requests!)
- English teaching with multilingual understanding
- Grammar correction and pronunciation help
- Friendly conversation practice
"""

import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import suppress
from typing import Optional

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('english_teacher_agent.log', mode='a')
    ]
)
logger = logging.getLogger("english-teacher-agent")
logger.setLevel(logging.INFO)

from dotenv import load_dotenv
from english_teacher_prompt import get_english_teaching_instruction

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, WorkerType, cli
from livekit.plugins import google
from livekit import rtc

# Global state for keeping the agent running
_shutdown_requested = False
_restart_count = 0
_max_restarts = 10

# Load environment variables
_ = load_dotenv(".env.local")
_ = load_dotenv(".env")

# Verify required environment variables
if not os.getenv('GOOGLE_API_KEY'):
    logger.error("GOOGLE_API_KEY not set in environment")
    logger.error("Please set your Google API key to use Gemini API")
    sys.exit(1)

if not os.getenv('LIVEKIT_URL'):
    logger.error("LIVEKIT_URL not set in environment")
    
if not os.getenv('LIVEKIT_API_KEY'):
    logger.error("LIVEKIT_API_KEY not set in environment")
    
if not os.getenv('LIVEKIT_API_SECRET'):
    logger.error("LIVEKIT_API_SECRET not set in environment")

# Verify environment variables are loaded
logger.info("Environment variables status:")
logger.info(f"  LIVEKIT_URL: {'OK' if os.getenv('LIVEKIT_URL') else 'MISSING'}")
logger.info(f"  LIVEKIT_API_KEY: {'OK' if os.getenv('LIVEKIT_API_KEY') else 'MISSING'}")
logger.info(f"  LIVEKIT_API_SECRET: {'OK' if os.getenv('LIVEKIT_API_SECRET') else 'MISSING'}")
logger.info(f"  GOOGLE_API_KEY: {'OK' if os.getenv('GOOGLE_API_KEY') else 'MISSING'}")

def create_gemini_session():
    """Create a session with Google's Gemini API (Free Tier - gemini-2.0-flash-live-001)."""
    try:
        # Use Gemini 2.0 Flash Live (Free Tier with UNLIMITED requests!)
        # Rate limits: Unlimited RPM, 1M TPM, Unlimited RPD
        # This is the Live API model specifically designed for real-time conversations
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-live-001",  # Live API model - UNLIMITED requests!
                voice="Kore",  # Available voices: Puck, Charon, Kore, Fenrir, Aoede
                temperature=0.8,
            ),
        )
        logger.info("[SUCCESS] Gemini 2.0 Flash Live session created (Free Tier - UNLIMITED requests)")
        return session
    except Exception as e:
        logger.error(f"Failed to create Gemini session: {e}")
        return None

async def entrypoint(ctx: JobContext) -> None:
    """Main agent entrypoint for English Teacher Agent.
    
    Creates an English teacher agent using Google Gemini API for Tamil speakers learning English.
    Includes automatic error recovery and keep-alive functionality.
    
    Args:
        ctx: JobContext containing room and session information
    """
    global _restart_count
    logger.info(f"Initializing English Teacher Agent with Gemini API... (Restart #{_restart_count})")
    
    session: Optional[AgentSession] = None
    
    try:
        # Create Gemini session
        session = create_gemini_session()
        
        if session is None:
            raise Exception("Failed to create Gemini session")
        
        # Start the agent session
        try:
            await session.start(
                agent=Agent(
                    instructions=get_english_teaching_instruction()
                ),
                room=ctx.room,
            )
            
            logger.info("[ACTIVE] English Teacher Agent with Gemini API is now active!")

            # Keep the session alive with periodic health checks
            await keep_session_alive(session, ctx.room)
            
        except Exception as e:
            logger.error(f"Failed to start agent session: {e}")
            raise
                
    except Exception as e:
        logger.error(f"Critical error in agent entrypoint: {e}")
        
        # Cleanup resources
        await cleanup_resources(session)
        
        # Implement graceful degradation
        if not _shutdown_requested and _restart_count < _max_restarts:
            _restart_count += 1
            logger.info(f"Attempting restart #{_restart_count} in 5 seconds...")
            await asyncio.sleep(5)
            # Re-raise to trigger restart mechanism
            raise
        else:
            logger.error("Maximum restart attempts reached or shutdown requested")
            raise


async def keep_session_alive(session: AgentSession, room) -> None:
    """Keep the session alive with periodic health checks."""
    logger.info("Starting session keep-alive monitoring...")
    
    while not _shutdown_requested:
        try:
            # Health check every 30 seconds
            await asyncio.sleep(30)
            
            # Check if room is still connected
            if room and hasattr(room, 'connection_state'):
                if room.connection_state == rtc.ConnectionState.CONN_DISCONNECTED:
                    logger.warning("Room disconnected, attempting to reconnect...")
                    break
            
            logger.debug("Session health check passed")
            
        except Exception as e:
            logger.error(f"Error during session keep-alive: {e}")
            break
    
    logger.info("Session keep-alive monitoring stopped")


async def cleanup_resources(session: Optional[AgentSession] = None) -> None:
    """Clean up resources gracefully."""
    logger.info("Cleaning up resources...")
    
    if session:
        try:
            with suppress(Exception):
                await session.aclose()
            logger.info("Agent session cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up session: {e}")


async def run_agent_with_auto_restart():
    """Run the agent with automatic restart capability."""
    global _restart_count, _shutdown_requested
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting English Teacher Agent with auto-restart capability...")
    
    while not _shutdown_requested and _restart_count < _max_restarts:
        try:
            # Start the LiveKit agent
            logger.info("[START] Starting LiveKit agent...")
            cli.run_app(WorkerOptions(
                entrypoint_fnc=entrypoint, 
                worker_type=WorkerType.ROOM
            ))
            
            # If we reach here, the agent stopped normally
            if not _shutdown_requested:
                logger.info("Agent stopped normally, restarting in 10 seconds...")
                await asyncio.sleep(10)
                _restart_count += 1
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            _shutdown_requested = True
            break
        except Exception as e:
            logger.error(f"Agent crashed with error: {e}")
            if _restart_count < _max_restarts:
                _restart_count += 1
                wait_time = min(60, 5 * _restart_count)  # Progressive backoff
                logger.info(f"Restarting in {wait_time} seconds... (attempt {_restart_count}/{_max_restarts})")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Maximum restart attempts reached, giving up")
                break
    
    logger.info("Agent shutdown complete")


def run_agent_for_render():
    """Run the agent specifically for Render deployment with proper port handling."""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import asyncio
    
    # Simple HTTP handler for Render health checks
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "healthy", "agent": "English Teacher Agent"}')
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"English Teacher Agent is running on Render")
        
        def log_message(self, format, *args):
            # Suppress logging
            return
    
    # Get port from Render environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting health check server on port {port}")
    
    # Start health check server in a separate thread
    def start_health_server():
        try:
            server = HTTPServer(('', port), HealthCheckHandler)
            logger.info(f"Health check server started on port {port}")
            server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
    
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Start the LiveKit agent (this will block)
    logger.info("[START] Starting LiveKit agent for Render deployment...")
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        worker_type=WorkerType.ROOM
    ))


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True


def run_detached_background():
    """Run the agent as a detached background process."""
    import subprocess
    import sys
    
    # Get current script path
    script_path = os.path.abspath(__file__)
    
    # Create command to run in background
    if sys.platform == "win32":
        # Windows: Use subprocess with CREATE_NEW_PROCESS_GROUP
        cmd = [sys.executable, script_path, "--background-worker"]
        
        # Start detached process
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            cwd=os.path.dirname(script_path)
        )
        
        print(f"🚀 Agent started as background process (PID: {process.pid})")
        print(f"📋 Process ID saved to: agent_pid.txt")
        print(f"📄 Logs available in: english_teacher_agent.log")
        print(f"🛑 To stop: python agent.py stop")
        
        # Save PID for later stopping
        with open("agent_pid.txt", "w") as f:
            f.write(str(process.pid))
            
        return process.pid
    else:
        # Unix-like systems
        cmd = [sys.executable, script_path, "--background-worker"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new session
        )
        
        print(f"🚀 Agent started as background process (PID: {process.pid})")
        print(f"📋 Process ID saved to: agent_pid.txt")
        print(f"📄 Logs available in: english_teacher_agent.log")
        print(f"🛑 To stop: python agent.py stop")
        
        # Save PID for later stopping
        with open("agent_pid.txt", "w") as f:
            f.write(str(process.pid))
            
        return process.pid


def stop_background_agent():
    """Stop the background agent process."""
    try:
        with open("agent_pid.txt", "r") as f:
            pid = int(f.read().strip())
        
        if sys.platform == "win32":
            # Windows
            os.system(f"taskkill /F /PID {pid}")
        else:
            # Unix-like systems
            os.kill(pid, signal.SIGTERM)
        
        print(f"🛑 Background agent (PID: {pid}) stopped successfully")
        
        # Remove PID file
        if os.path.exists("agent_pid.txt"):
            os.remove("agent_pid.txt")
            
    except FileNotFoundError:
        print("❌ No background agent PID file found. Agent may not be running.")
    except ProcessLookupError:
        print("❌ Background agent process not found. It may have already stopped.")
        # Clean up PID file
        if os.path.exists("agent_pid.txt"):
            os.remove("agent_pid.txt")
    except Exception as e:
        print(f"❌ Error stopping background agent: {e}")


def check_agent_status():
    """Check if the background agent is running."""
    try:
        with open("agent_pid.txt", "r") as f:
            pid = int(f.read().strip())
        
        if sys.platform == "win32":
            # Windows - check if process exists
            result = os.system(f"tasklist /FI \"PID eq {pid}\" 2>nul | find \"{pid}\" >nul")
            if result == 0:
                print(f"✅ Background agent is running (PID: {pid})")
                return True
            else:
                print(f"❌ Background agent (PID: {pid}) is not running")
                return False
        else:
            # Unix-like systems
            try:
                os.kill(pid, 0)  # Send signal 0 to check if process exists
                print(f"✅ Background agent is running (PID: {pid})")
                return True
            except ProcessLookupError:
                print(f"❌ Background agent (PID: {pid}) is not running")
                return False
                
    except FileNotFoundError:
        print("❌ No background agent PID file found. Agent is not running.")
        return False
    except Exception as e:
        print(f"❌ Error checking agent status: {e}")
        return False


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "console":
            logger.info("Starting in console mode...")
            # For console mode, run with fast mode if enabled
            if os.getenv("FAST_MODE") == "true":
                logger.info("Fast mode enabled - text-only responses")
            
            # Start the LiveKit agent normally for console mode
            cli.run_app(WorkerOptions(
                entrypoint_fnc=entrypoint, 
                worker_type=WorkerType.ROOM
            ))
            
        elif sys.argv[1] == "background":
            print("🚀 Starting agent in detached background mode...")
            print("This will survive IDE/terminal closure!")
            run_detached_background()
            
        elif sys.argv[1] == "connect":
            # Room connection mode for playground
            room_name = "english-teacher-demo"
            if len(sys.argv) > 2:
                room_name = sys.argv[2]
                
            logger.info(f"Starting room connection mode for room: {room_name}")
            
            if os.getenv("FAST_MODE") == "true":
                logger.info("Fast mode enabled - text-only responses")
            
            # Start the LiveKit agent in room connection mode
            cli.run_app(WorkerOptions(
                entrypoint_fnc=entrypoint, 
                worker_type=WorkerType.ROOM
            ))
            
        elif sys.argv[1] == "dev":
            # Development mode - same as connect but with specific room
            room_name = "english-teacher-demo"
            if len(sys.argv) > 2:
                room_name = sys.argv[2]
                
            logger.info(f"Starting development mode for room: {room_name}")
            
            if os.getenv("FAST_MODE") == "true":
                logger.info("Fast mode enabled - text-only responses")
            
            # Start the LiveKit agent in development mode
            cli.run_app(WorkerOptions(
                entrypoint_fnc=entrypoint, 
                worker_type=WorkerType.ROOM
            ))
            
        elif sys.argv[1] == "--background-worker":
            # This is the actual background worker process
            logger.info("Starting as background worker process...")
            try:
                asyncio.run(run_agent_with_auto_restart())
            except KeyboardInterrupt:
                logger.info("Background worker terminated by user")
            except Exception as e:
                logger.error(f"Fatal error in background worker: {e}")
                sys.exit(1)
                
        elif sys.argv[1] == "stop":
            stop_background_agent()
            
        elif sys.argv[1] == "status":
            check_agent_status()
            
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""English Teacher Agent - Usage:
            
🎯 CONSOLE MODE (Original):
    python agent.py console              # Interactive console mode
    $env:FAST_MODE="true"; python agent.py console  # Fast mode
    
🌐 PLAYGROUND CONNECTION:
    python agent.py dev                  # Connect to LiveKit Playground
    python agent.py connect [room_name] # Connect to specific room
    $env:FAST_MODE="true"; python agent.py dev  # Fast mode for playground
    
🔄 CONTINUOUS MODE (Foreground):
    python agent.py                      # Auto-restart, stops when terminal closes
    
🚀 BACKGROUND MODE (Detached):
    python agent.py background           # Runs independently, survives IDE closure
    python agent.py stop                 # Stop background agent
    python agent.py status               # Check if background agent is running
    
☁️  CLOUD DEPLOYMENT MODE:
    python agent.py cloud                # Runs in cloud mode for continuous operation
    python agent.py render               # Special mode for Render deployment
    
📚 HELP:
    python agent.py --help               # Show this help
            """)
        elif sys.argv[1] == "cloud":
            print("☁️  Starting in cloud deployment mode...")
            print("This mode is optimized for cloud hosting environments")
            # For cloud deployment, run with auto-restart capability
            try:
                asyncio.run(run_agent_with_auto_restart())
            except KeyboardInterrupt:
                print("Received keyboard interrupt, shutting down...")
            except Exception as e:
                print(f"Fatal error: {e}")
                sys.exit(1)
        elif sys.argv[1] == "render":
            print("☁️  Starting in Render deployment mode...")
            print("This mode is optimized for Render cloud hosting")
            # For Render deployment, run with auto-restart capability
            try:
                asyncio.run(run_agent_with_auto_restart())
            except KeyboardInterrupt:
                print("Received keyboard interrupt, shutting down...")
            except Exception as e:
                print(f"Fatal error: {e}")
                sys.exit(1)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use 'python agent.py --help' for usage information")
    else:
        # Default: Run with auto-restart capability (foreground)
        print("🔄 Starting in continuous mode (foreground)...")
        print("💡 Tip: Use 'python agent.py background' for detached mode that survives IDE closure")
        print("💡 Tip: Use 'python agent.py --help' for all options")
        
        # Auto-restart wrapper
        while True:
            try:
                print("Starting English Teacher Agent...")
                asyncio.run(run_agent_with_auto_restart())
                break  # If we reach here normally, exit
            except Exception as e:
                print(f"Bot crashed: {e}")
                print("Restarting in 5 seconds...")
                time.sleep(5)