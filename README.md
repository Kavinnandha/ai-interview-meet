# AI Interview Meet

A complete video conferencing solution with AI-powered English teaching agent, built with LiveKit.

## 🏗️ Architecture

This project consists of three main components:

1. **livekit-server** - Real-time communication server
2. **livekit-web** - Next.js web interface for video conferencing
3. **ai-agent** - AI English teacher agent with voice and avatar support

## 📋 Prerequisites

- Docker and Docker Compose
- Google API Key (for AI agent speech/LLM capabilities)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Kavinnandha/ai-interview-meet.git
cd ai-interview-meet
```

### 2. Configure environment variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_actual_google_api_key
```

### 3. Start all services

```bash
docker-compose up -d
```

This will start:
- LiveKit server on ports 7880, 7881, 7882
- Web interface on http://localhost:3000
- AI agent (connects to LiveKit automatically)

### 4. Access the application

Open your browser and navigate to:
```
http://localhost:3000
```

## 🛠️ Development

### Building individual services

**LiveKit Server:**
```bash
cd livekit-server
docker build -t livekit-server .
docker run -p 7880:7880 -p 7881:7881 -p 7882:7882/udp livekit-server
```

**Web Interface:**
```bash
cd livekit-web
docker build -t livekit-web .
docker run -p 3000:3000 \
  -e LIVEKIT_URL=ws://livekit-server:7880 \
  -e LIVEKIT_API_KEY=devkey \
  -e LIVEKIT_API_SECRET=secret \
  livekit-web
```

**AI Agent:**
```bash
cd ai-agent
docker build -t ai-agent .
docker run \
  -e LIVEKIT_URL=ws://livekit-server:7880 \
  -e LIVEKIT_API_KEY=devkey \
  -e LIVEKIT_API_SECRET=secret \
  -e GOOGLE_API_KEY=your_key \
  ai-agent
```

## 📦 Project Structure

```
ai-interview-meet/
├── livekit-server/       # LiveKit server configuration
│   ├── Dockerfile
│   └── livekit.yaml
├── livekit-web/          # Next.js web application
│   ├── app/              # Next.js app directory
│   ├── lib/              # Utility libraries
│   ├── public/           # Static assets
│   ├── styles/           # CSS modules
│   └── Dockerfile
├── ai-agent/             # AI English teacher agent
│   ├── agent.py          # Main agent logic
│   ├── english_teacher_prompt.py
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml    # Orchestration configuration
```

## 🔧 Configuration

### LiveKit Server

The server is configured with development credentials in `livekit-server/livekit.yaml`:
- API Key: `devkey`
- API Secret: `secret`

**⚠️ Warning:** These are default credentials for local development only. Do not use in production!

### Environment Variables

All services can be configured via environment variables. See `.env.example` for available options.

Key variables:
- `GOOGLE_API_KEY` - Required for AI agent
- `LIVEKIT_API_KEY` - LiveKit API key (default: devkey)
- `LIVEKIT_API_SECRET` - LiveKit API secret (default: secret)
- `TAVUS_API_KEY`, `TAVUS_REPLICA_ID`, `TAVUS_PERSONA_ID` - Optional avatar configuration

## 🎯 Features

### Web Interface
- Real-time video conferencing
- Screen sharing
- Audio/video settings
- Recording capabilities
- E2EE (End-to-End Encryption) support

### AI English Teacher Agent
- Voice conversation with Google Realtime API
- Visual avatar support via Tavus
- Grammar correction and pronunciation help
- Multilingual understanding (especially for Tamil speakers)
- Friendly conversation practice

## 🐛 Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs -f

# Check specific service
docker-compose logs -f ai-agent
```

### Port conflicts
If ports 3000, 7880, 7881, or 7882 are already in use, modify the port mappings in `docker-compose.yml`.

### AI Agent not connecting
Ensure you've set a valid `GOOGLE_API_KEY` in your `.env` file.

## 🛑 Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📝 License

See LICENSE files in individual component directories.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.
