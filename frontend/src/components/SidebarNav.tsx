interface SidebarNavProps {
  items: { key: string; label: string }[]
  active: string
  onChange: (key: string) => void
}

export function SidebarNav({ items, active, onChange }: SidebarNavProps) {
  return (
    <nav className="rail-nav">
      {items.map((item) => (
        <button
          key={item.key}
          className={`rail-nav-item${item.key === active ? ' active' : ''}`}
          onClick={() => onChange(item.key)}
          type="button"
        >
          {item.label}
        </button>
      ))}
    </nav>
  )
}
