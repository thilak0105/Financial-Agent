import { useState, useRef, useEffect } from "react"
import ReactMarkdown from "react-markdown"

// API base URL - uses proxy in development, env variable in production
const DEFAULT_API_BASE = "https://financial-agent-0bul.onrender.com"
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? DEFAULT_API_BASE : "")
const NORMALIZED_API_BASE = API_BASE.replace(/\/$/, "")
const API = (path) => `${NORMALIZED_API_BASE}/api${path}`

// ============ useSSE Hook (inline for simplicity) ============
function useChat() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello! I'm FinSight, your AI finance assistant. Ask me about any stock, news, or your portfolio!" }
  ])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (text) => {
    if (!text.trim() || isStreaming) return
    
    setMessages(prev => [...prev, { role: "user", content: text }])
    setIsStreaming(true)
    
    let fullResponse = ""
    setMessages(prev => [...prev, { role: "assistant", content: "", streaming: true }])
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 45000)

    try {
      const response = await fetch(API("/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: "default" }),
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`Chat request failed (${response.status})`)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      let buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        
        // Keep last incomplete line in buffer
        buffer = lines.pop()
        
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith("data: ")) {
            try {
              const data = JSON.parse(trimmed.slice(6))
              if (data.type === "text" && data.content) {
                fullResponse += data.content
                setMessages(prev => prev.map((m, i) => 
                  i === prev.length - 1 
                    ? { ...m, content: fullResponse } 
                    : m
                ))
              }
              if (data.type === "done") {
                setMessages(prev => prev.map((m, i) => 
                  i === prev.length - 1 
                    ? { ...m, streaming: false } 
                    : m
                ))
              }
              if (data.type === "error") {
                fullResponse = "Error: " + data.content
                setMessages(prev => prev.map((m, i) => 
                  i === prev.length - 1 
                    ? { ...m, content: fullResponse, streaming: false } 
                    : m
                ))
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      const errorText = e?.name === "AbortError"
        ? "Error: Request timed out. Please try again."
        : "Error: Could not connect to backend."
      setMessages(prev => prev.map((m, i) => 
        i === prev.length - 1 ? { ...m, content: errorText, streaming: false } : m
      ))
    } finally {
      clearTimeout(timeoutId)
      setIsStreaming(false)
    }
  }

  return { messages, isStreaming, sendMessage }
}

// ============ ChatInterface ============
function ChatInterface({ messages, isStreaming, sendMessage }) {
  const [input, setInput] = useState("")
  const bottomRef = useRef(null)
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const suggestions = [
    "Price of TCS.NS",
    "Analyse RELIANCE.NS", 
    "Show my portfolio",
    "AAPL news sentiment",
    "Buy 2 shares of INFY.NS"
  ]

  const handleSend = () => {
    sendMessage(input)
    setInput("")
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">⚡ FinSight</h1>
        <p className="text-xs text-gray-400">AI Finance Agent</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
              msg.role === "user" 
                ? "bg-blue-600 text-white rounded-br-sm" 
                : "bg-gray-700 text-gray-100 rounded-bl-sm"
            }`}>
              {msg.role === "assistant" ? (
                <div className="prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown
                    components={{
                      h3: ({node, ...props}) => (
                        <h3 className="text-sm font-bold text-white mt-2 mb-1" {...props} />
                      ),
                      h4: ({node, ...props}) => (
                        <h4 className="text-xs font-semibold text-gray-200 mt-1 mb-1" {...props} />
                      ),
                      strong: ({node, ...props}) => (
                        <strong className="text-blue-200 font-semibold" {...props} />
                      ),
                      em: ({node, ...props}) => (
                        <em className="text-gray-300" {...props} />
                      ),
                      p: ({node, ...props}) => (
                        <p className="text-gray-100 mb-1 leading-snug" {...props} />
                      ),
                      ul: ({node, ...props}) => (
                        <ul className="list-disc list-inside text-gray-100 mb-1 space-y-0.5" {...props} />
                      ),
                      li: ({node, ...props}) => (
                        <li className="ml-1" {...props} />
                      ),
                      hr: ({node, ...props}) => (
                        <hr className="border-gray-600 my-1" {...props} />
                      ),
                    }}
                  >
                    {msg.content || (msg.streaming ? "●●●" : "")}
                  </ReactMarkdown>
                </div>
              ) : (
                <div>
                  {msg.content || (msg.streaming ? <span className="animate-pulse">●●●</span> : "")}
                </div>
              )}
              {msg.streaming && msg.content && <span className="animate-pulse text-blue-300">▌</span>}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {suggestions.map(s => (
            <button key={s} onClick={() => { sendMessage(s) }}
              className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1 rounded-full transition-colors">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder="Ask about stocks, news, portfolio..."
            className="flex-1 bg-gray-700 text-white placeholder-gray-400 rounded-xl px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isStreaming}
          />
          <button onClick={handleSend} disabled={isStreaming}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors">
            {isStreaming ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  )
}

// ============ StockPanel ============
function StockPanel() {
  const [symbol, setSymbol] = useState("RELIANCE.NS")
  const [input, setInput] = useState("RELIANCE.NS")
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchStock = async (sym) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(API(`/stocks/${sym}`))
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || json.error || "Failed to fetch stock data")
      if (json.error) throw new Error(json.error)
      setData(json)
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  useEffect(() => { fetchStock(symbol) }, [symbol])

  const popular = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "TSLA", "GOOGL"]

  return (
    <div className="p-4 space-y-4">
      {/* Search */}
      <div className="flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === "Enter" && setSymbol(input)}
          placeholder="Enter symbol e.g. TCS.NS"
          className="flex-1 bg-gray-700 text-white placeholder-gray-500 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
        <button onClick={() => setSymbol(input)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">
          Search
        </button>
      </div>

      {/* Popular chips */}
      <div className="flex flex-wrap gap-2">
        {popular.map(s => (
          <button key={s} onClick={() => { setSymbol(s); setInput(s) }}
            className={`text-xs px-3 py-1 rounded-full transition-colors ${
              symbol === s ? "bg-blue-600 text-white" : "bg-gray-700 hover:bg-gray-600 text-gray-300"
            }`}>
            {s}
          </button>
        ))}
      </div>

      {/* Stock Card */}
      {loading && <div className="text-center text-gray-400 py-8">Loading stock data...</div>}
      {error && <div className="text-red-400 bg-red-900/20 rounded-lg p-3 text-sm">{error}</div>}
      {data && !loading && (
        <div className="bg-gray-800 rounded-xl p-4 space-y-4">
          {/* Price Header */}
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-bold text-white">{data.price_data?.symbol}</h2>
              <p className="text-3xl font-bold text-white mt-1">
                {data.price_data?.currency === "INR" ? "₹" : "$"}
                {data.price_data?.current_price?.toFixed(2)}
              </p>
              <p className={`text-sm mt-1 ${data.price_data?.change >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.price_data?.change >= 0 ? "▲" : "▼"} 
                {Math.abs(data.price_data?.change)?.toFixed(2)} ({data.price_data?.change_percent?.toFixed(2)}%)
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
              data.technical_data?.overall_signal === "bullish" ? "bg-green-500/20 text-green-400" :
              data.technical_data?.overall_signal === "bearish" ? "bg-red-500/20 text-red-400" :
              "bg-yellow-500/20 text-yellow-400"
            }`}>
              {data.technical_data?.overall_signal?.toUpperCase() || "NEUTRAL"}
            </span>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3">
            {[
              ["Volume", data.price_data?.volume?.toLocaleString()],
              ["52W High", `${data.price_data?.currency === "INR" ? "₹" : "$"}${data.price_data?.week_52_high?.toFixed(2)}`],
              ["52W Low", `${data.price_data?.currency === "INR" ? "₹" : "$"}${data.price_data?.week_52_low?.toFixed(2)}`],
              ["RSI (14)", data.technical_data?.RSI_14?.toFixed(1)],
              ["SMA 20", data.technical_data?.SMA_20?.toFixed(2)],
              ["SMA 50", data.technical_data?.SMA_50?.toFixed(2)],
            ].map(([label, value]) => (
              <div key={label} className="bg-gray-700/50 rounded-lg p-2">
                <p className="text-xs text-gray-400">{label}</p>
                <p className="text-sm font-medium text-white">{value || "—"}</p>
              </div>
            ))}
          </div>

          {/* Technical Summary */}
          {data.technical_data?.summary && (
            <p className="text-xs text-gray-400 bg-gray-700/30 rounded-lg p-3">
              📊 {data.technical_data.summary}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ============ NewsPanel ============
function NewsPanelTab() {
  const [company, setCompany] = useState("Reliance Industries")
  const [input, setInput] = useState("Reliance Industries")
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchNews = async (c) => {
    setLoading(true)
    try {
      const res = await fetch(API(`/news/${encodeURIComponent(c)}`))
      const json = await res.json()
      setData(json)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchNews(company) }, [company])

  const sentimentColor = (s) => ({
    "Positive": "bg-green-500/20 text-green-400",
    "Negative": "bg-red-500/20 text-red-400",
    "Neutral": "bg-gray-500/20 text-gray-400"
  })[s] || "bg-gray-500/20 text-gray-400"

  return (
    <div className="p-4 space-y-4">
      <div className="flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && setCompany(input)}
          placeholder="Company name e.g. TCS"
          className="flex-1 bg-gray-700 text-white placeholder-gray-500 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500" />
        <button onClick={() => setCompany(input)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">
          Search
        </button>
      </div>

      {loading && <div className="text-center text-gray-400 py-8">Analyzing news...</div>}
      
      {data && !loading && (
        <div className="space-y-3">
          {/* Overall sentiment card */}
          <div className={`rounded-xl p-4 ${
            data.overall_sentiment === "Positive" ? "bg-green-900/30 border border-green-700/30" :
            data.overall_sentiment === "Negative" ? "bg-red-900/30 border border-red-700/30" :
            "bg-gray-800 border border-gray-700"
          }`}>
            <div className="flex justify-between items-center">
              <span className="text-white font-medium">{data.company}</span>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${sentimentColor(data.overall_sentiment)}`}>
                {data.overall_sentiment}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-2">{data.summary}</p>
          </div>

          {/* Articles */}
          {data.articles?.map((a, i) => (
            <div key={i} className="bg-gray-800 rounded-xl p-3 space-y-1">
              <div className="flex justify-between items-start gap-2">
                <p className="text-sm text-white leading-snug line-clamp-2">{a.title}</p>
                <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs ${sentimentColor(a.sentiment)}`}>
                  {a.sentiment}
                </span>
              </div>
              <p className="text-xs text-gray-500">{a.source} • {a.reason}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============ PortfolioPanel ============
function PortfolioPanelTab() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tradeForm, setTradeForm] = useState({ symbol: "", action: "BUY", quantity: 1 })
  const [tradeMsg, setTradeMsg] = useState(null)

  const fetchPortfolio = async () => {
    setLoading(true)
    try {
      const res = await fetch(API('/portfolio'))
      const contentType = res.headers.get('content-type') || ''
      const raw = await res.text()
      const json = contentType.includes('application/json')
        ? JSON.parse(raw)
        : { detail: raw }
      if (!res.ok) throw new Error(json.detail || json.error || 'Failed to fetch portfolio')
      console.log('Portfolio API response:', json)
      setData(json)
    } catch(e) {
      console.error('Portfolio fetch error:', e)
    }
    setLoading(false)
}

  useEffect(() => { 
    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, 30000)
    return () => clearInterval(interval)
  }, [])

  const executeTrade = async () => {
    try {
      const res = await fetch(API("/trade"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tradeForm)
      })
      const json = await res.json()
      setTradeMsg(json.status === "success" ? 
        `✅ ${json.action} ${json.quantity} shares of ${json.symbol} @ ${json.price?.toFixed(2)}` :
        `❌ ${json.error || "Trade failed"}`)
      fetchPortfolio()
    } catch {
      setTradeMsg("❌ Trade failed")
    }
    setTimeout(() => setTradeMsg(null), 4000)
  }

  const PnlBadge = ({ value }) => (
    <span className={value >= 0 ? "text-green-400" : "text-red-400"}>
      {value >= 0 ? "+" : ""}{value?.toFixed(2)}
    </span>
  )

  return (
    <div className="p-4 space-y-4">
      {/* Quick Trade */}
      <div className="bg-gray-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-medium text-white">Quick Trade (Paper)</h3>
        <div className="flex gap-2">
          <input value={tradeForm.symbol} 
            onChange={e => setTradeForm(p => ({...p, symbol: e.target.value.toUpperCase()}))}
            placeholder="Symbol e.g. TCS.NS"
            className="flex-1 bg-gray-700 text-white placeholder-gray-500 rounded-lg px-3 py-2 text-sm outline-none" />
          <input type="number" value={tradeForm.quantity} min="1"
            onChange={e => setTradeForm(p => ({...p, quantity: parseInt(e.target.value)}))}
            className="w-20 bg-gray-700 text-white rounded-lg px-3 py-2 text-sm outline-none" />
        </div>
        <div className="flex gap-2">
          {["BUY", "SELL"].map(a => (
            <button key={a} onClick={() => setTradeForm(p => ({...p, action: a}))}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                tradeForm.action === a 
                  ? a === "BUY" ? "bg-green-600 text-white" : "bg-red-600 text-white"
                  : "bg-gray-700 text-gray-400"
              }`}>
              {a}
            </button>
          ))}
          <button onClick={executeTrade}
            className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg text-sm font-medium">
            Execute
          </button>
        </div>
        {tradeMsg && <p className="text-xs text-center py-1">{tradeMsg}</p>}
      </div>

      {loading && <div className="text-center text-gray-400 py-4">Loading portfolio...</div>}

      {data && !loading && (
        <div className="space-y-4">
          {/* India Portfolio */}
          <div className="bg-gray-800 rounded-xl p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-white">🇮🇳 India Portfolio</h3>
              <span className="text-xs text-gray-400">Virtual ₹1,00,000</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-gray-700/50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Cash Available</p>
                <p className="text-sm font-bold text-white">₹{Number(data.india?.balance ?? 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Holdings Value</p>
                <p className="text-sm font-bold text-white">₹{Number(data.india?.current_value_of_holdings ?? 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Total Portfolio</p>
                <p className="text-sm font-bold text-white">₹{Number(data.india?.total_portfolio_value ?? 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</p>
              </div>
              <div className="bg-gray-700/50 rounded-lg p-2">
                <p className="text-xs text-gray-400">Unrealized P&L</p>
                <p className="text-sm font-bold text-white">
                  <span className={Number(data.india?.unrealized_pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}>
                    {Number(data.india?.unrealized_pnl ?? 0) >= 0 ? "🟢 +" : "🔴 "}₹{Math.abs(Number(data.india?.unrealized_pnl ?? 0)).toFixed(2)}
                  </span>
                </p>
              </div>
            </div>
            {(data.india?.holdings ?? []).length > 0 ? (
              <div className="space-y-2">
                {data.india.holdings.map((h, i) => (
                  <div key={i} className="bg-gray-700/30 rounded-lg p-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-white">{h.symbol}</span>
                      <span className="text-xs text-gray-400">{h.quantity} shares</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-400">Avg. Buy Price</p>
                        <p className="text-white font-medium">₹{h.avg_buy_price?.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Current Price</p>
                        <p className="text-white font-medium">₹{h.current_price?.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">Total Value</p>
                        <p className="text-white font-medium">₹{h.current_value?.toLocaleString('en-IN')}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-gray-400">P&L</p>
                        <p className={`font-medium ${h.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {h.unrealized_pnl >= 0 ? "+" : ""}₹{h.unrealized_pnl?.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 text-center py-2">No holdings yet. Place a trade!</p>
            )}
          </div>

          {/* US Portfolio */}
          <div className="bg-gray-800 rounded-xl p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-white">🇺🇸 US Portfolio (Alpaca)</h3>
              <span className="text-xs text-gray-400">Paper Trading</span>
            </div>
            {data.us?.error ? (
              <div className="text-yellow-400 text-xs bg-yellow-900/20 rounded-lg p-3">
                ⚠️ US trading unavailable: Configure Alpaca API keys in backend/.env to enable US paper trading.
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="bg-gray-700/50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Cash</p>
                    <p className="text-sm font-bold text-white">${Number(data.us?.cash ?? 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-2">
                    <p className="text-xs text-gray-400">Portfolio Value</p>
                    <p className="text-sm font-bold text-white">${Number(data.us?.portfolio_value ?? 0).toFixed(2)}</p>
                  </div>
                </div>
                {(data.us?.holdings ?? []).length > 0 ? (
                  <div className="space-y-2">
                    {data.us.holdings.map((h, i) => (
                       <div key={i} className="grid grid-cols-4 items-center bg-gray-700/30 rounded-lg p-2 text-xs gap-2">
                        <div>
                          <p className="text-white font-medium">{h.symbol}</p>
                          <p className="text-gray-400">{h.quantity} shares</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Avg. Buy</p>
                          <p className="text-white">${h.avg_buy_price?.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Current Value</p>
                          <p className="text-white">${h.current_value?.toFixed(2)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-gray-400">P&L</p>
                          <p className={`font-medium ${h.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                            {h.unrealized_pnl >= 0 ? "+" : ""}${h.unrealized_pnl?.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                   <p className="text-xs text-gray-500 text-center py-2">No US holdings yet.</p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ============ Main App ============
export default function App() {
  const [activeTab, setActiveTab] = useState("stock")
  const { messages, isStreaming, sendMessage } = useChat()
  const tabs = ["stock", "news", "portfolio"]

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Left: Chat */}
      <div className="w-[38%] border-r border-gray-800 flex flex-col">
        <ChatInterface messages={messages} isStreaming={isStreaming} sendMessage={sendMessage} />
      </div>

      {/* Right: Dashboard */}
      <div className="w-[62%] flex flex-col">
        {/* Tabs */}
        <div className="flex border-b border-gray-800 bg-gray-900">
          {tabs.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-sm font-medium capitalize transition-colors ${
                activeTab === tab 
                  ? "text-blue-400 border-b-2 border-blue-400" 
                  : "text-gray-400 hover:text-gray-200"
              }`}>
              {tab === "stock" ? "📈 Stock" : tab === "news" ? "📰 News" : "💼 Portfolio"}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === "stock" && <StockPanel />}
          {activeTab === "news" && <NewsPanelTab />}
          {activeTab === "portfolio" && <PortfolioPanelTab />}
        </div>
      </div>
    </div>
  )
}
