

;; railway mode for reading .rail files
(setq railway-font-lock-keywords
      (let* (
	     (x-keywords '("if" "else" "fi" "do" "yield" "undo" "loop"
			   "pool" "for" "rof" "try" "catch" "yrt" "in"))
            (x-types '("let" "unlet"))
            (x-constants '("main"))
            (x-events '("import" "global" "func" "return"))
            (x-functions '("print" "call" "uncall" "push" "pop" "swap"))

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
(defun remove-electric-indent-mode ()
  (electric-indent-local-mode -1))
(add-hook 'railway-mode-hook 'remove-electric-indent-mode)





;; ebnf mode by Jeramey Crawford, https://github.com/jeramey/ebnf-mode 
(define-generic-mode 'ebnf-mode
  '(("(*" . "*)"))
  '("=")
  '(("^[^ \t\n][^=]+" . font-lock-variable-name-face)
    ("['\"].*?['\"]" . font-lock-string-face)
    ("\\?.*\\?" . font-lock-negation-char-face)
    ("\*" . font-lock-type-face)
    ("\\[\\|\\]\\|{\\|}\\|(\\|)\\||\\|,\\|;" . font-lock-type-face)
    ("[^ \t\n]" . font-lock-function-name-face))
  '("\\.ebnf\\'")
  `(,(lambda () (setq mode-name "EBNF")))
  "Major mode for EBNF metasyntax text highlighting.")
