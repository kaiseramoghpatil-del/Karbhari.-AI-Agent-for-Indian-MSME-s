import type { ToolCallRecord } from '../types'

export function ToolTrace({ trace }: { trace: ToolCallRecord[] }) {
  if (trace.length === 0) {
    return <div className="empty-state">No investigation steps recorded.</div>
  }

  return (
    <ol className="tool-trace">
      {trace.map((t) => (
        <li key={t.step} className="tool-trace-step">
          <div className="tool-trace-head">
            <span className="tool-trace-step-no">{t.step}</span>
            <span className="tool-trace-tool">{t.tool}</span>
          </div>
          {t.thought && <p className="tool-trace-thought">{t.thought}</p>}
          <p className="tool-trace-summary">{t.output_summary}</p>
          <details>
            <summary>Raw tool call</summary>
            <pre className="tool-trace-raw">
              input: {JSON.stringify(t.tool_input, null, 2)}
              {'\n\n'}output: {JSON.stringify(t.tool_output, null, 2)}
            </pre>
          </details>
        </li>
      ))}
    </ol>
  )
}
