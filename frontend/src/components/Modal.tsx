import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, X } from 'lucide-react';
import { PasswordField } from './forms';
import { Alert, Button, cx } from './ui';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md';
}

export const Modal: React.FC<ModalProps> = ({ open, onClose, title, description, icon, children, footer, size = 'sm' }) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const focusable = panelRef.current?.querySelector<HTMLElement>('input, select, textarea, button[data-autofocus]');
    (focusable || panelRef.current)?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeRef.current();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-4 backdrop-blur-sm animate-fade-in sm:items-center"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cx(
          'w-full overflow-hidden rounded-2xl bg-white shadow-card-lg outline-none animate-fade-up',
          size === 'sm' ? 'max-w-md' : 'max-w-lg'
        )}
      >
        <div className="flex items-start gap-3 px-6 pt-6">
          {icon && <span className="mt-0.5 shrink-0">{icon}</span>}
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-semibold">{title}</h2>
            {description && <div className="mt-1 text-sm leading-relaxed text-slate-600">{description}</div>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="-m-1 rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        {children && <div className="px-6 pt-5">{children}</div>}
        <div className="mt-6 flex flex-col-reverse gap-2 border-t border-slate-100 bg-slate-50/70 px-6 py-4 sm:flex-row sm:justify-end">
          {footer}
        </div>
      </div>
    </div>,
    document.body
  );
};

/* ------------------------------------------------------------------ ConfirmDialog */

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  message: React.ReactNode;
  confirmLabel: string;
  tone?: 'danger' | 'primary';
  requirePassword?: boolean;
  onConfirm: (password: string) => Promise<void> | void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  onClose,
  title,
  message,
  confirmLabel,
  tone = 'primary',
  requirePassword = false,
  onConfirm,
}) => {
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setPassword('');
      setError(null);
      setBusy(false);
    }
  }, [open]);

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (requirePassword && !password) {
      setError('Enter your password to confirm.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onConfirm(password);
      onClose();
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={busy ? () => undefined : onClose}
      title={title}
      description={message}
      icon={
        tone === 'danger' ? (
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-red-50 text-red-600">
            <AlertTriangle className="h-[18px] w-[18px]" aria-hidden />
          </span>
        ) : undefined
      }
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant={tone === 'danger' ? 'danger' : 'primary'} loading={busy} onClick={() => submit()} data-autofocus>
            {confirmLabel}
          </Button>
        </>
      }
    >
      {(requirePassword || error) && (
        <form onSubmit={submit} className="space-y-4">
          {requirePassword && (
            <PasswordField
              label="Your password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          )}
          {error && <Alert tone="error">{error}</Alert>}
        </form>
      )}
    </Modal>
  );
};
