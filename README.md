# 🚀 FinSight - AI-Powered Financial Assistant

An intelligent financial assistant powered by AI agents that provides real-time stock analysis, news sentiment, portfolio management, and trading capabilities for both US and Indian markets.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

---

## ✨ Features

- 📊 **Real-time Stock Analysis** - Get live stock prices, technical indicators, and historical data
- 📰 **News & Sentiment Analysis** - Track market news with AI-powered sentiment analysis
- 💼 **Portfolio Management** - Manage both US (Alpaca) and Indian market portfolios
- 🤖 **AI-Powered Chat** - Natural language interface using Gemini, GPT, and Groq
- 📈 **Trading Capabilities** - Execute trades with real-time market data
- 🎨 **Modern UI** - Beautiful, responsive interface built with React and Tailwind CSS

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│    - Modern UI with Tailwind CSS        │
│    - Real-time SSE for AI streaming     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Backend (FastAPI + Python)         │
│    - Orchestrator Agent                 │
│    - Stock Agent, News Agent            │
│    - Portfolio Agent                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        External APIs & Services         │
│  - yFinance, Alpaca, News API           │
│  - Gemini, OpenAI, Groq                 │
└─────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Markdown
- Server-Sent Events (SSE)

### Backend
- FastAPI
- Python 3.11
- yFinance
- Alpaca API
- Google Gemini AI
- OpenAI GPT
- Groq

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys (see `.env.example`)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/thilak0105/Financial-Agent.git
cd Financial-Agent/finsight
```

2. **Set up Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
uvicorn main:app --reload
```

3. **Set up Frontend**
```bash
cd frontend
npm install
npm run dev
```

4. **Open your browser**
```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
```

---

## 📦 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy:**
- **Backend**: Deploy to [Render](https://render.com) (free)
- **Frontend**: Deploy to [Vercel](https://vercel.com) (free)

---

## 🔑 Environment Variables

### Backend (.env)
```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
NEWS_API_KEY=your_news_key
FRONTEND_URL=https://your-vercel-app.vercel.app
```

### Frontend (.env)
```env
VITE_API_URL=https://your-backend.onrender.com
```

---

## 🎯 Usage Examples

**Stock Analysis:**
```
"What's the current price of Apple stock?"
"Show me technical indicators for TSLA"
```

**News & Sentiment:**
```
"What's the latest news about Microsoft?"
"Get market sentiment for the tech sector"
```

**Portfolio Management:**
```
"Show my US portfolio"
"What's my India portfolio worth?"
```

**Trading:**
```
"Buy 10 shares of AAPL"
"Sell 5 shares of GOOGL"
```

---

## 📁 Project Structure

```
finsight/
├── backend/
│   ├── agents/           # AI Agent implementations
│   │   ├── orchestrator.py
│   │   ├── stock_agent.py
│   │   ├── news_agent.py
│   │   └── portfolio_agent.py
│   ├── tools/            # API integration tools
│   │   ├── stock_tools.py
│   │   ├── news_tools.py
│   │   └── trading_tools.py
│   ├── data/             # Portfolio data
│   └── main.py           # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main React component
│   │   └── main.jsx
│   └── public/
├── DEPLOYMENT.md         # Deployment guide
└── README.md            # This file
```

---

## 🤖 AI Agents

### Orchestrator Agent
Routes user queries to specialized agents and coordinates responses.

### Stock Agent
Handles stock price queries, technical analysis, and market data.

### News Agent
Fetches and analyzes financial news with sentiment analysis.

### Portfolio Agent
Manages portfolio data and executes trades via Alpaca API.

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/health` | GET | API status |
| `/api/chat` | POST | Chat with AI agent (SSE) |
| `/api/stock-price` | GET | Get stock price |
| `/api/stock-info` | GET | Get stock information |
| `/api/technical-indicators` | GET | Get technical indicators |
| `/api/news` | GET | Get latest news |
| `/api/sentiment` | GET | Get news sentiment |
| `/api/portfolio` | GET | Get full portfolio |
| `/api/trade` | POST | Execute a trade |

---

## 📊 Features in Detail

### Real-time Chat with AI
- Streaming responses using Server-Sent Events
- Context-aware conversations
- Multi-turn dialogue support

### Stock Market Data
- Real-time prices from yFinance
- Technical indicators (RSI, MACD, Moving Averages)
- Historical data and charts

### News & Sentiment
- Latest financial news from multiple sources
- AI-powered sentiment analysis
- Market-specific news filtering

### Portfolio Management
- US market via Alpaca API
- Indian market via custom engine
- Real-time portfolio valuation

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [yFinance](https://github.com/ranaroussi/yfinance)
- [Alpaca](https://alpaca.markets/)
- [Google Gemini](https://ai.google.dev/)
- [OpenAI](https://openai.com/)
- [Groq](https://groq.com/)

---

## 📞 Contact

**Developer**: Thilak
**GitHub**: [@thilak0105](https://github.com/thilak0105)
**Repository**: [Financial-Agent](https://github.com/thilak0105/Financial-Agent)

---

Made with ❤️ and AI
