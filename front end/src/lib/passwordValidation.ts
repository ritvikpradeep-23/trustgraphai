export function validatePasswordChange(current: string, next: string, confirmation: string): string | null {
  if (!current || current.length > 128) return "Enter your current password (at most 128 characters).";
  if (next.length < 15 || next.length > 128 || !next.trim()) return "Choose a non-blank passphrase of 15–128 characters.";
  if (next === current) return "Choose a different new passphrase.";
  if (next !== confirmation) return "The new passphrases do not match.";
  return null;
}
