import { useState, useRef, useEffect } from 'react'
import MessageBubble, { ChatMessage, ToolCall } from './components/MessageBubble'
import { streamChat, Message } from './api/chat'

const SUGGESTIONS = [
  'Summarise my devmind repo: samnit007/devmind',
  'Search the web for LangGraph best practices 2026',
  'Read the README of samnit007/pr-reviewer-agent',
  'What is MCP (Model Context Protocol)?',
]

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text?: string) {
    const userText = (text ?? input).trim()
    if (!userText || loading) return

    setInput('')
    setError('')

    const userMsg: ChatMessage = { role: 'user', content: userText }
    const history: ChatMessage[] = [...messages, userMsg]
    setMessages(history)
    setLoading(true)

    const assistantMsg: ChatMessage = {
      role: 'assistant',
      content: '',
      toolCalls: [],
      streaming: true,
    }
    setMessages([...history, assistantMsg])

    const apiMessages: Message[] = history.map(m => ({ role: m.role, content: m.content }))

    try {
      for await (const event of streamChat(apiMessages)) {
        if (event.type === 'text') {
          setMessages(prev => {
            const updated = [...prev]
            const last = { ...updated[updated.length - 1] }
            last.content += event.delta
            updated[updated.length - 1] = last
            return updated
          })
        } else if (event.type === 'tool_start') {
          setMessages(prev => {
            const updated = [...prev]
            const last = { ...updated[updated.length - 1] }
            last.toolCalls = [...(last.toolCalls ?? []), { name: event.name, done: false }]
            updated[updated.length - 1] = last
            return updated
          })
        } else if (event.type === 'tool_done') {
          setMessages(prev => {
            const updated = [...prev]
            const last = { ...updated[updated.length - 1] }
            last.toolCalls = (last.toolCalls ?? []).map((tc: ToolCall) =>
              tc.name === event.name && !tc.done ? { ...tc, done: true } : tc
            )
            updated[updated.length - 1] = last
            return updated
          })
        } else if (event.type === 'done') {
          setMessages(prev => {
            const updated = [...prev]
            const last = { ...updated[updated.length - 1] }
            last.streaming = false
            updated[updated.length - 1] = last
            return updated
          })
        }
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
      setMessages(prev => {
        const updated = [...prev]
        const last = { ...updated[updated.length - 1] }
        last.streaming = false
        updated[updated.length - 1] = last
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">

      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-gray-800">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-sm font-bold">D</div>
        <div>
          <h1 className="font-semibold text-gray-100">DevMind</h1>
          <p className="text-xs text-gray-500">Claude · tool use · streaming · MCP</p>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center gap-6 text-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-300 mb-2">What can I help you build?</h2>
              <p className="text-sm text-gray-500">I can read GitHub repos, search the web, and reason about your code.</p>
            </div>
            <div className="grid grid-cols-1 gap-2 w-full max-w-md">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-left px-4 py-3 rounded-xl border border-gray-700 text-sm text-gray-400 hover:border-indigo-600 hover:text-gray-200 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => <MessageBubble key={i} message={m} />)}
        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-xl px-4 py-3 mb-4">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-800">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            disabled={loading}
            placeholder="Ask me anything about your code or repos…"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className="bg-indigo-600 text-white rounded-xl px-5 py-3 text-sm font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '…' : 'Send'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2 text-center">
          Tools: GitHub repos · web search · local files
        </p>
      </div>
    </div>
  )
}
