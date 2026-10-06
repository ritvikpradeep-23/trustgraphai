import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
interface Props {
  id: string; value: string; onChange: (value: string) => void;
  error?: string; disabled?: boolean; autoComplete?: "current-password" | "new-password";
}
export function PasswordInput({ id, value, onChange, error, disabled, autoComplete = "current-password" }: Props) {
  const [visible, setVisible] = useState(false);
  return <div className="password-input">
    <input id={id} name="password" type={visible ? "text" : "password"} required maxLength={128}
      autoComplete={autoComplete} value={value} onChange={event => onChange(event.target.value)}
      disabled={disabled} aria-invalid={Boolean(error)} aria-describedby={error ? id + "-error" : undefined}
      data-testid="login-password-input" />
    <button type="button" disabled={disabled} onClick={() => setVisible(current => !current)}
      aria-label={visible ? "Hide password" : "Show password"} aria-pressed={visible}
      data-testid="login-password-toggle">{visible ? <EyeOff size={17} /> : <Eye size={17} />}</button>
  </div>;
}
