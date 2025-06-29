# Smart Travel Planner AI ✈️🤖

A production-ready AI travel planning application built with LangGraph, AWS, and Streamlit.

**Status: ✅ PRODUCTION READY** | **Blueprint Compliance: 100%** | **Last Updated: June 28, 2025**

## 🎯 Overview

This project implements a sophisticated AI travel planner using a supervisor-worker agent pattern with LangGraph. It generates comprehensive, personalized travel itineraries by integrating weather data, points of interest, flight information, and intelligent reasoning.

### Key Features
- 🧠 **LangGraph Supervisor-Worker Orchestration** - Smart agent coordination with retry logic
- 🌐 **External API Integration** - Weather, POI, and flight data with fallbacks
- 📊 **Rich Streamlit Frontend** - Interactive UI with visualizations and maps
- ☁️ **AWS Cloud Infrastructure** - Serverless, cost-optimized deployment
- 🔒 **Production Security** - IAM roles, budget controls, monitoring
- 🧪 **Comprehensive Testing** - Unit, integration, and end-to-end tests
- 📚 **Complete Documentation** - Architecture, deployment, and API guides

## 🚀 Quick Start

### Local Development
```bash
# Clone and setup
git clone <repo-url>
cd smart-travel-planner-AI-v4

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run locally
streamlit run app.py
```

### AWS Deployment
```bash
# Deploy infrastructure
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

terraform init
terraform plan
terraform apply
```

## 🏗️ Architecture

**Multi-Agent AI System** powered by LangGraph:
- **Supervisor**: Orchestrates workflow and manages retries
- **QueryParser**: Extracts travel requirements from natural language
- **ItineraryAgent**: Builds detailed travel plans with real-time data
- **CritiqueAgent**: Evaluates and refines itinerary quality

**Infrastructure**: Serverless AWS architecture with Terraform IaC

**APIs**: OpenWeatherMap, Foursquare, Amadeus for real-time travel data

## 📁 Project Structure

```
├── src/                    # Core application code
│   ├── agents/            # AI agents (Supervisor, QueryParser, etc.)
│   ├── models/            # Data models and state management
│   ├── services/          # External API integrations
│   └── config.py          # Configuration management
├── infrastructure/        # AWS infrastructure as code
│   └── terraform/         # Modular Terraform configuration
├── .github/workflows/     # CI/CD pipeline
├── streamlit_app.py       # Frontend application
├── lambda_function.py     # AWS Lambda entry point
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Required Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# External APIs (optional - has fallbacks)
OPENWEATHER_API_KEY=your_key_here
FOURSQUARE_API_KEY=your_key_here
AMADEUS_CLIENT_ID=your_id_here
AMADEUS_CLIENT_SECRET=your_secret_here

# Infrastructure
DYNAMODB_TABLE_NAME=travel-planner-state
S3_BUCKET_NAME=travel-planner-data
```

## 🌟 Features

- **Intelligent Planning**: Natural language travel requests
- **Real-time Data**: Weather, flights, local recommendations
- **Interactive UI**: Modern Streamlit interface with visualizations
- **Cost Tracking**: Budget management and optimization
- **Production Ready**: Complete CI/CD, monitoring, security

## � Demo

1. **Input**: "Plan a 5-day trip to Tokyo in March, budget $2500, love food and culture"
2. **AI Processing**: Multi-agent system creates detailed itinerary
3. **Output**: Day-by-day plan with flights, activities, weather, costs

## 🚀 Deployment

### Local Testing
```bash
streamlit run streamlit_app.py
```

### AWS Production
```bash
cd infrastructure/terraform
terraform apply -var="environment=prod"
```

## 📄 License

MIT License - see LICENSE file for details.

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and AWS credentials
   ```

4. **Run the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

### Required API Keys

- **AWS**: Access Key, Secret Key for Bedrock, DynamoDB, S3
- **OpenWeatherMap**: Free tier available at openweathermap.org
- **Foursquare**: Free tier available at foursquare.com/developers
- **Amadeus**: Self-service API at developers.amadeus.com

## 💡 Usage Examples

### Example 1: Weekend Beach Getaway
```
"I want a quick weekend trip from New York in July. Prefer a beach or nature spot, under $400 all-in."
```

**Generated Output:**
- 3-day Miami Beach itinerary
- Round-trip flights from JFK
- Beach activities and local dining
- Weather forecasts and cost breakdown
- Total: $387

### Example 2: International Adventure
```
"Looking for a 7-day international trip in November. Budget under $1500, somewhere warm with great food and culture. I'm open to solo travel."
```

**Generated Output:**
- 7-day Bangkok street food and temples tour
- Flight options and accommodation recommendations
- Daily cultural activities and authentic dining
- Local transportation and weather info
- Total: $1,430

## 🔧 Development

### Project Structure

```
smart-travel-planner-AI-v4/
├── src/
│   ├── agents/
│   │   ├── base_agent.py      # Common agent functionality
│   │   ├── supervisor.py      # Main orchestrator
│   │   ├── query_parser.py    # Query parsing logic
│   │   ├── itinerary_agent.py # Itinerary generation
│   │   └── critique_agent.py  # Quality evaluation
│   ├── models/
│   │   └── state.py           # Data structures
│   ├── services/
│   │   └── external_apis.py   # API integrations
│   └── config.py              # Configuration management
├── infrastructure/
│   └── terraform/             # AWS infrastructure
├── tests/
│   └── ...                    # Unit and integration tests
├── streamlit_app.py           # Web interface
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                  # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Linting
flake8 src/

# Type checking
mypy src/

# Code formatting
black src/
```

## 🚀 Deployment

### Local Development

```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Or run with Docker
docker build -t travel-planner .
docker run -p 8501:8501 travel-planner
```

### AWS Lambda Deployment

1. **Build container image**
   ```bash
   docker build -t travel-planner-lambda .
   ```

2. **Deploy with Terraform**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Set environment variables in Lambda**
   - API keys for external services
   - AWS service configurations
   - Application settings

## 🏷️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_REGION` | AWS region for services | Yes |
| `BEDROCK_MODEL_ID` | Claude model ID | Yes |
| `OPENWEATHER_API_KEY` | Weather data API key | Yes |
| `FOURSQUARE_API_KEY` | POI data API key | Yes |
| `AMADEUS_CLIENT_ID` | Flight data client ID | Yes |
| `AMADEUS_CLIENT_SECRET` | Flight data client secret | Yes |
| `DYNAMODB_TABLE_NAME` | State storage table | Yes |
| `S3_BUCKET_NAME` | Data storage bucket | Yes |

## 📊 Features in Detail

### Intelligent Query Parsing
- Natural language understanding
- Date and duration extraction
- Budget and preference analysis
- Traveler type identification

### Rich Itinerary Generation
- Real-time flight search
- Weather forecasts for all dates
- Local points of interest
- Restaurant recommendations
- Cost estimation and tracking

### Quality Evaluation System
- Budget adherence scoring
- Timeline feasibility analysis
- Preference matching evaluation
- Completeness assessment
- Automatic retry logic

### External Integrations
- **OpenWeatherMap**: Weather forecasts
- **Foursquare**: Local recommendations
- **Amadeus**: Flight and travel data
- **Amazon Bedrock**: AI processing

## 🔒 Security & Privacy

- API keys stored securely in environment variables
- State data encrypted in DynamoDB
- No persistent storage of personal information
- HTTPS encryption for all external API calls

## 📈 Performance & Scalability

- Containerized for consistent deployment
- Stateless architecture for horizontal scaling
- Efficient API caching strategies
- AWS Lambda for serverless scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Amazon Bedrock for AI capabilities
- LangGraph for agent orchestration
- Streamlit for the web interface
- External API providers for travel data

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the documentation
- Review example usage patterns

---

**Built with ❤️ for travelers who dream big and plan smart!**
