interface TabsProps {
  tabs: { key: string; label: string }[]
  active: string
  onChange: (key: string) => void
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="tabs">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={`tab${tab.key === active ? ' active' : ''}`}
          onClick={() => onChange(tab.key)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
