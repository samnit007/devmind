const TOOL_LABELS: Record<string, string> = {
  fetch_github_repo: '🔍 Reading GitHub repo',
  fetch_github_file: '📄 Reading file from GitHub',
  search_web: '🌐 Searching the web',
  read_file: '📂 Reading local file',
  list_files: '📁 Listing directory',
}

interface Props {
  name: string
  done: boolean
}

export default function ToolCallBadge({ name, done }: Props) {
  const label = TOOL_LABELS[name] ?? `🔧 ${name}`
  return (
    <div className={`inline-flex items-center gap-2 text-xs px-3 py-1 rounded-full font-mono my-1 ${
      done
        ? 'bg-green-900/40 text-green-400 border border-green-800'
        : 'bg-amber-900/40 text-amber-400 border border-amber-800 animate-pulse'
    }`}>
      {label}
      {!done && <span className="ml-1">…</span>}
      {done && <span className="ml-1">✓</span>}
    </div>
  )
}
