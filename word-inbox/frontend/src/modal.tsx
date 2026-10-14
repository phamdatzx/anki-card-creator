/** A popup on the native <dialog>: Escape, focus trap and backdrop for free. */

import { useEffect, useRef } from "react";

export function Modal({
  title,
  onClose,
  children,
  footer,
  closeOnBackdrop = true,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
  /** Off for editors, so a stray tap doesn't drop unsaved changes. */
  closeOnBackdrop?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) {
      dialog.showModal();
    }
    // Stop the page behind from scrolling while the popup is open.
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
    };
  }, []);

  return (
    <dialog
      ref={ref}
      className="modal"
      aria-label={title}
      onCancel={(event) => {
        // Escape: let React unmount it instead of the browser closing it.
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        // A click on the backdrop lands on the <dialog> element itself.
        if (closeOnBackdrop && event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="modal-panel">
        <header className="modal-head">
          <h2>{title}</h2>
          <button type="button" className="ghost small" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="modal-body">{children}</div>
        {footer ? <footer className="modal-foot">{footer}</footer> : null}
      </div>
    </dialog>
  );
}
