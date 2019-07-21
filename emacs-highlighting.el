(setq railway-font-lock-keywords
      (let* (
	     (x-keywords '("if" "else" "fi" "do" "yield"
			   "undo" "loop" "for" "until"
			   "try" "catch" "yrt"))
            (x-types '("let" "unlet"))
            (x-constants '())
            (x-events '("func" "return" "undoreturn"))
            (x-functions '("print" "call" "uncall"))

            (x-keywords-regexp (regexp-opt x-keywords 'words))
            (x-types-regexp (regexp-opt x-types 'words))
            (x-constants-regexp (regexp-opt x-constants 'words))
            (x-events-regexp (regexp-opt x-events 'words))
            (x-functions-regexp (regexp-opt x-functions 'words)))

        `((,x-types-regexp . font-lock-type-face)
          (,x-constants-regexp . font-lock-constant-face)
          (,x-events-regexp . font-lock-builtin-face)
          (,x-functions-regexp . font-lock-function-name-face)
          (,x-keywords-regexp . font-lock-keyword-face)
          )))

(define-derived-mode railway-mode c-mode "railway mode"
  "Major mode for editing railway files"
  (setq font-lock-defaults '((railway-font-lock-keywords))))

(add-to-list 'auto-mode-alist '("\\.rail\\'" . railway-mode))
