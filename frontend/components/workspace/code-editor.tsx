"use client";

import Editor, { type Monaco, type OnMount } from "@monaco-editor/react";
import type { Position, editor } from "monaco-editor";
import { useCallback, useEffect, useRef, useState } from "react";

import { KEYBOARD_SHORTCUTS, SNIPPETS_BY_LANGUAGE } from "@/lib/editor-snippets";
import { cn } from "@/lib/utils";

/**
 * Emmet and the snippet providers attach to the Monaco *singleton*, not to an
 * editor instance, so doing this per mount would stack duplicate providers and
 * show every suggestion two or three times. The flag keeps it to once per page.
 */
let editorExtrasInstalled = false;

function installEditorExtras(monaco: Monaco) {
  if (editorExtrasInstalled) return;
  editorExtrasInstalled = true;

  // Emmet: `!` expands to a full document, `div.card>ul>li*3` to real markup,
  // `dfc` to a centred flex block. Loaded lazily because it is only useful once
  // an editor actually exists, and it should never block first paint.
  void import("emmet-monaco-es")
    .then(({ emmetHTML, emmetCSS, emmetJSX }) => {
      emmetHTML(monaco, ["html"]);
      emmetCSS(monaco, ["css", "scss", "less"]);
      emmetJSX(monaco, ["javascript", "typescript"]);
    })
    .catch(() => {
      // Emmet is a convenience. If the chunk fails to load the editor must keep
      // working, so this is deliberately swallowed rather than surfaced.
    });

  for (const [language, snippets] of Object.entries(SNIPPETS_BY_LANGUAGE)) {
    monaco.languages.registerCompletionItemProvider(language, {
      provideCompletionItems: (model: editor.ITextModel, position: Position) => {
        // Replace the partially typed word rather than inserting beside it,
        // otherwise typing `fo` and picking `fori` leaves `fofori`.
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };
        return {
          suggestions: snippets.map((snippet) => ({
            label: snippet.prefix,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: snippet.body,
            insertTextRules:
              monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: snippet.detail,
            documentation: { value: "```\n" + snippet.body + "\n```" },
            range,
          })),
        };
      },
    });
  }
}

export function CodeEditor({
  value,
  language,
  onChange,
  readOnly = false,
  className,
  path,
  onRun,
  onSubmit,
}: {
  value: string;
  language: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  className?: string;
  /** Bound to Cmd/Ctrl+Enter. Optional: callers without a Run action skip it. */
  onRun?: () => void;
  /** Bound to Cmd/Ctrl+S, which also stops the browser's own save dialog. */
  onSubmit?: () => void;
  /**
   * Unique identity of the buffer (usually "<owner>/<filename>"). Used to remount
   * the editor when the file changes: reusing one instance across files lets a
   * change event raised during the swap be attributed to the file we just left,
   * which silently copies the incoming text into the previous file.
   */
  path?: string;
}) {
  const [showShortcuts, setShowShortcuts] = useState(false);

  // Keybindings are registered once on mount, so reading the callbacks directly
  // would freeze the first render's closures and later fire a stale Run.
  const actionsRef = useRef({ onRun, onSubmit });
  useEffect(() => {
    actionsRef.current = { onRun, onSubmit };
  }, [onRun, onSubmit]);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    installEditorExtras(monaco);

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      actionsRef.current.onRun?.();
    });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      actionsRef.current.onSubmit?.();
    });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyK, () => {
      setShowShortcuts((open) => !open);
    });

    // Editor chrome matches the product surfaces exactly so the workspace reads
    // as one application rather than an embedded widget.
    monaco.editor.defineTheme("sprintforge", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment", foreground: "5b616b", fontStyle: "italic" },
        { token: "keyword", foreground: "c8fa4b" },
        { token: "string", foreground: "b8e08a" },
        { token: "number", foreground: "7cc4ff" },
        { token: "type", foreground: "dcfd8b" },
        { token: "tag", foreground: "c8fa4b" },
        { token: "attribute.name", foreground: "8a9099" },
      ],
      colors: {
        "editor.background": "#08080a",
        "editorGutter.background": "#08080a",
        "editor.lineHighlightBackground": "#101216",
        "editorLineNumber.foreground": "#3a3f47",
        "editorLineNumber.activeForeground": "#8a9099",
        "editor.selectionBackground": "#c8fa4b26",
        "editor.inactiveSelectionBackground": "#c8fa4b14",
        "editorCursor.foreground": "#c8fa4b",
        "editorIndentGuide.background1": "#16181d",
        "editorIndentGuide.activeBackground1": "#2c3138",
        "editorWidget.background": "#0d0e11",
        "editorWidget.border": "#1f2228",
        "editorSuggestWidget.selectedBackground": "#1b1e23",
        "scrollbarSlider.background": "#262a3199",
        "scrollbarSlider.hoverBackground": "#363c45cc",
      },
    });
    monaco.editor.setTheme("sprintforge");
  }, []);

  return (
    <div className={cn("relative h-full w-full overflow-hidden", className)}>
      {/*
       * `path` alone switches buffers: Monaco keeps one model per path and swaps
       * it, which is far cheaper than tearing the editor down. There is
       * deliberately no `key` here — remounting on every file tab click was
       * costing a full editor recreate. Safe attribution of change events is the
       * caller's job (it writes to the file named by a ref, not by a stale
       * render closure), and `defaultValue` keeps the editor uncontrolled so
       * typing never round-trips through React state.
       */}
      <Editor
        path={path}
        defaultValue={value}
        language={language}
        onMount={handleMount}
        onChange={(next) => onChange?.(next ?? "")}
        loading={
          <span className="p-4 font-mono text-[10px] uppercase tracking-[0.14em] text-faint">
            Mounting editor…
          </span>
        }
        options={{
          readOnly,
          fontSize: 12.5,
          lineHeight: 21,
          fontLigatures: true,
          fontFamily: "var(--font-mono), ui-monospace, monospace",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          padding: { top: 16, bottom: 16 },
          tabSize: 2,
          renderLineHighlight: "line",
          automaticLayout: true,
          cursorBlinking: "phase",
          cursorSmoothCaretAnimation: "on",
          guides: { indentation: true },
          scrollbar: { verticalScrollbarSize: 9, horizontalScrollbarSize: 9 },
          overviewRulerLanes: 0,
          renderWhitespace: "selection",
          // Suggestions have to be eager for snippets and Emmet to feel like
          // shortcuts rather than a menu you must remember to open.
          tabCompletion: "on",
          snippetSuggestions: "top",
          quickSuggestions: { other: true, comments: false, strings: false },
          suggestOnTriggerCharacters: true,
          wordBasedSuggestions: "currentDocument",
          acceptSuggestionOnEnter: "on",
          autoClosingBrackets: "languageDefined",
          autoClosingQuotes: "languageDefined",
          autoSurround: "languageDefined",
          formatOnPaste: true,
          bracketPairColorization: { enabled: true },
          matchBrackets: "always",
          linkedEditing: true,
          multiCursorModifier: "alt",
        }}
      />
      {showShortcuts ? <ShortcutSheet onClose={() => setShowShortcuts(false)} /> : null}
    </div>
  );
}

/** Cheat sheet toggled with Cmd/Ctrl+K, so shortcuts are discoverable in place. */
function ShortcutSheet({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="absolute inset-0 z-20 grid place-items-center bg-canvas/80 p-6 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded border border-line bg-surface p-5 shadow-panel"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-faint">
            editor shortcuts
          </p>
          <button
            onClick={onClose}
            className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint hover:text-accent"
          >
            esc
          </button>
        </div>
        <ul className="mt-4 divide-y divide-line">
          {KEYBOARD_SHORTCUTS.map((shortcut) => (
            <li key={shortcut.keys} className="flex items-center justify-between gap-4 py-1.5">
              <span className="text-[12px] text-muted">{shortcut.action}</span>
              <kbd className="whitespace-nowrap font-mono text-[10.5px] text-accent">
                {shortcut.keys}
              </kbd>
            </li>
          ))}
        </ul>
        <p className="mt-4 border-t border-line pt-3 text-[11px] leading-relaxed text-faint">
          Emmet is on for HTML and CSS. Type <span className="text-accent">!</span> then Tab for a
          full document, or <span className="text-accent">div.card&gt;ul&gt;li*3</span> then Tab for
          nested markup.
        </p>
      </div>
    </div>
  );
}

/** Editor tab strip. The dot marks which buffers the exercise lets you write. */
export function FileTabs({
  files,
  active,
  editable,
  onSelect,
}: {
  files: string[];
  active: string;
  editable: string[];
  onSelect: (file: string) => void;
}) {
  return (
    <div className="flex items-stretch overflow-x-auto border-b border-line bg-surface">
      {files.map((file) => {
        const isEditable = editable.includes(file);
        const isActive = active === file;
        return (
          <button
            key={file}
            onClick={() => onSelect(file)}
            aria-pressed={isActive}
            className={cn(
              "group relative flex items-center gap-2 whitespace-nowrap border-r border-line px-4 py-2.5 font-mono text-[11px] transition-colors duration-150",
              isActive
                ? "bg-canvas text-ink"
                : "text-faint hover:bg-elevated/60 hover:text-muted",
            )}
          >
            <span
              className={cn(
                "h-1 w-1 flex-none rounded-full",
                isEditable ? "bg-accent" : "bg-line-strong",
              )}
              title={isEditable ? "Editable in this exercise" : "Provided — read only"}
            />
            {file}
            {!isEditable ? (
              <span className="text-[8.5px] uppercase tracking-[0.1em] text-faint/70">ro</span>
            ) : null}
            {/* Active tab indicator sits on the strip's bottom edge. */}
            <span
              className={cn(
                "absolute inset-x-0 -bottom-px h-px bg-accent transition-opacity",
                isActive ? "opacity-100" : "opacity-0",
              )}
              aria-hidden
            />
          </button>
        );
      })}
    </div>
  );
}

export function PreviewFrame({
  html,
  /**
   * Whether this workspace has an entry document at all. A CSS- or JS-only
   * exercise has nothing to render, and saying so is better than pointing at a
   * Run button that cannot help.
   */
  previewable = true,
}: {
  html: string | null;
  previewable?: boolean;
}) {
  if (!html) {
    return (
      <div className="grid-bg-fine grid h-full place-items-center px-6 text-center">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-faint">
            {previewable ? "no render yet" : "no preview for this ticket"}
          </p>
          <p className="mt-2 max-w-[34ch] text-[12px] leading-relaxed text-muted">
            {previewable ? (
              <>
                Press <span className="text-accent">Run</span> to render your code.
              </>
            ) : (
              "This ticket ships no entry document, so there is nothing to render. Run checks grades it instead."
            )}
          </p>
        </div>
      </div>
    );
  }
  return (
    <iframe
      title="Live preview"
      srcDoc={html}
      sandbox="allow-scripts"
      className="h-full w-full border-0 bg-white"
    />
  );
}
