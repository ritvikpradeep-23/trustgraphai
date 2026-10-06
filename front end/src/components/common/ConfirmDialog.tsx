import { useEffect, useId, useRef } from "react";
import { AlertTriangle, X } from "lucide-react";

export function ConfirmDialog({ title, description, confirmLabel, busy = false, onClose, onConfirm }: {
  title: string; description: string; confirmLabel: string; busy?: boolean; onClose: () => void; onConfirm: () => void;
}) {
  const id = useId();
  const card = useRef<HTMLDivElement>(null);
  const close = useRef(onClose); close.current = onClose;
  const pending = useRef(busy); pending.current = busy;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    card.current?.querySelector<HTMLButtonElement>("[data-autofocus]")?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending.current) { event.preventDefault(); close.current(); }
      if (event.key === "Tab") {
        const buttons = card.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)");
        if (!buttons?.length) { event.preventDefault(); return; }
        const first = buttons[0], last = buttons[buttons.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener("keydown", keydown);
    return () => { document.body.style.overflow = overflow; document.removeEventListener("keydown", keydown); previous?.focus(); };
  }, []);
  return <div className="confirm-modal" onClick={event => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <div ref={card} className="confirm-card" role="dialog" aria-modal="true" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} aria-busy={busy} data-testid="settings-confirm-modal">
      <button type="button" className="confirm-close" aria-label="Close confirmation" disabled={busy} onClick={onClose} data-testid="settings-confirm-close"><X size={16} /></button>
      <span className="warning-icon"><AlertTriangle size={20} /></span>
      <h2 id={`${id}-title`}>{title}</h2><p id={`${id}-description`}>{description}</p>
      <div className="confirm-actions"><button type="button" className="button-secondary" data-autofocus disabled={busy} onClick={onClose} data-testid="settings-confirm-cancel">Cancel</button><button type="button" className="button-danger" disabled={busy} onClick={onConfirm} data-testid="settings-confirm-delete">{busy ? "Working…" : confirmLabel}</button></div>
    </div>
  </div>;
}
