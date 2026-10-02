import type { ToolCallRecord } from '../types'
import { Reveal } from './fx'

const TOOL_COLOR: Record<string, string> = {
  list_evidence: 'var(--mut)',
  read_evidence: 'var(--blue)',
  reconcile_debtors: 'var(--violet)',
  check_consistency: 'var(--teal)',
  calculate_drawing_power: 'var(--gold)',
}

export function ToolTrace({ trace }: { trace: ToolCallRecord[] }) {
  if (trace.length === 0) {
    return <div className="empty panel panel-pad">No investigation steps recorded.</div>
  }

  const counts = trace.reduce<Record<string, number>>((a, t) => ({ ...a, [t.tool]: (a[t.tool] ?? 0) + 1 }), {})

  return (
    <>
      <div className="trace-summary">
        {Object.entries(counts).map(([tool, n]) => (
          <span key={tool} className="trace-pill" style={{ ['--c' as string]: TOOL_COLOR[tool] ?? 'var(--mut)' }}>
            <i />
            {tool} <b className="num">×{n}</b>
          </span>
        ))}
      </div>
      <ol className="timeline">
        {trace.map((t, i) => (
          <Reveal i={i} key={t.step}>
            <li className="tl-step" style={{ ['--c' as string]: TOOL_COLOR[t.tool] ?? 'var(--mut)' }}>
              <span className="tl-node num">{t.step}</span>
              <div className="tl-body panel">
                <div className="tl-head">
                  <span className="tl-tool">{t.tool}</span>
                  <span className="tl-summary">{t.output_summary}</span>
                </div>
                {t.thought && <p className="tl-thought">{t.thought}</p>}
                <details className="quotes">
                  <summary>
                    <span className="label">Raw tool call</span>
                  </summary>
                  <pre className="raw">
                    {'input: '}
                    {JSON.stringify(t.tool_input, null, 2)}
                    {'\n\noutput: '}
                    {JSON.stringify(t.tool_output, null, 2)}
                  </pre>
                </details>
              </div>
            </li>
          </Reveal>
        ))}
      </ol>
    </>
  )
}
