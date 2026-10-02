import { Icon } from './Icon'
import { sfx } from '../lib/sound'

interface SidebarNavProps {
  items: { key: string; label: string; icon: string; badge?: number | string }[]
  active: string
  onChange: (key: string) => void
}

export function SidebarNav({ items, active, onChange }: SidebarNavProps) {
  return (
    <nav className="rail-nav">
      {items.map((item, i) => (
        <button
          key={item.key}
          className={`rail-nav-item${item.key === active ? ' active' : ''}`}
          onClick={() => item.key !== active && onChange(item.key)}
          onMouseEnter={() => sfx.tick()}
          type="button"
        >
          <span className="nav-idx num">0{i + 1}</span>
          <Icon name={item.icon} size={16} />
          <span className="nav-label">{item.label}</span>
          {item.badge !== undefined && item.badge !== 0 && <span className="nav-badge num">{item.badge}</span>}
        </button>
      ))}
    </nav>
  )
}
