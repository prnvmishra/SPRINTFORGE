"""JavaScript-layer practice modules.

Kept separate from `practice_modules.py` so each layer's catalogue can grow
without turning one file into a thousand-line wall. Registered by
`practice_modules.py` via `extend`, which also enforces unique ids.

Design rules every module in this file follows:

* The HTML and CSS are given and locked; the learner writes only `script.js`.
* The *data* the page renders is owned by the grader, not by the learner's file.
  Each behaviour scenario injects a different dataset before running the
  learner's whole file (`wrap_as: "__userMain"`), so a hard-coded answer that
  matches one scenario fails the next one.
* Static AST checks never stand alone. Every requirement that describes visible
  behaviour is also proven by a behaviour assertion that inspects the shimmed
  DOM *after* the harness has drained the learner's pending async work, so a
  function that is declared but never called cannot pass.
* Error states are proven the way `ticket_templates.__expectErrorState` proves
  them: something must be written after the failure, the visible state must have
  changed, and it must read as an error rather than as a leftover spinner.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Shared page assets (given and locked in every module)
# ---------------------------------------------------------------------------

PRACTICE_CSS = """:root {
  --surface: #151823;
  --surface-2: #1e2330;
  --accent: #6366f1;
  --danger: #f87171;
  --text: #e5e7eb;
  --muted: #9ca3af;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  padding: 32px 16px;
  background-color: #0b0c10;
  color: var(--text);
  font-family: system-ui, -apple-system, sans-serif;
}

.panel {
  max-width: 560px;
  margin: 0 auto;
  padding: 24px;
  background-color: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

h1 {
  margin: 0 0 4px;
  font-size: 22px;
}

.subtitle {
  margin: 0 0 20px;
  color: var(--muted);
  font-size: 14px;
}

ul,
ol {
  margin: 0;
  padding: 0;
  list-style: none;
}

li {
  padding: 10px 12px;
  margin-bottom: 8px;
  background-color: var(--surface-2);
  border-radius: 10px;
}

.row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
}

button {
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  background-color: var(--accent);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  background-color: var(--surface-2);
  color: var(--text);
}

.field {
  margin-bottom: 14px;
}

.error,
[role="alert"] {
  color: var(--danger);
  font-size: 14px;
}

.success {
  color: #34d399;
  font-size: 14px;
}

.muted,
.loading {
  color: var(--muted);
}

.read {
  opacity: 0.55;
}

.hidden {
  display: none;
}
"""


def _page(title: str, body: str, data_file: bool = True) -> str:
    """The locked HTML shell. `script.js` is always loaded last."""
    data_tag = '    <script src="data.js"></script>\n' if data_file else ""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f"    <title>{title}</title>\n"
        '    <link rel="stylesheet" href="styles.css" />\n'
        "  </head>\n"
        "  <body>\n"
        f"{body}"
        f"{data_tag}"
        '    <script src="script.js"></script>\n'
        "  </body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# Behaviour harness support: a small DOM + event shim owned by the grader.
#
# It sits in the *prelude*, so it is installed before the learner's file runs.
# `__resetDom()` rebuilds the page from the module's own `__buildDom()` before
# each scenario, which is what makes one file runnable against many datasets.
# ---------------------------------------------------------------------------

DOM_SHIM = r"""
let __root = null;
let __writes = 0;
let __prevented = false;
// Request bookkeeping, so a loading indicator painted *before* the first await
// can never be mistaken for the success/error rendering that follows it.
let __requestStarted = false;
let __domAtRequest = '';
let __postRequestWrites = 0;

function __recordWrite() {
  __writes++;
  if (__requestStarted) __postRequestWrites++;
  __note();
}

function __norm(value) {
  return String(value === null || value === undefined ? '' : value).replace(/\s+/g, ' ').trim();
}

//: Markup assigned with innerHTML is parsed into real nodes, so a learner who
//: writes template strings is judged exactly like one who uses createElement.
function __parseHTML(html) {
  const VOID = { br: 1, hr: 1, img: 1, input: 1, meta: 1, link: 1, source: 1, area: 1, col: 1 };
  const nodes = [];
  const stack = [];
  const tokenRe =
    /<\/?\s*([a-zA-Z][\w-]*)((?:\s+[\w:.-]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>|([^<]+)/g;
  let match;
  while ((match = tokenRe.exec(html)) !== null) {
    if (match[4] !== undefined) {
      const text = match[4];
      if (!text.trim()) continue;
      const parent = stack[stack.length - 1];
      if (parent) {
        parent._text += text;
      } else {
        const wrapper = __makeElement('span');
        wrapper._text = text;
        nodes.push(wrapper);
      }
      continue;
    }
    const tag = String(match[1]).toLowerCase();
    if (match[0].charAt(1) === '/') {
      for (let i = stack.length - 1; i >= 0; i--) {
        if (String(stack[i].tagName).toLowerCase() === tag) {
          stack.length = i;
          break;
        }
      }
      continue;
    }
    const element = __makeElement(tag);
    const attrRe = /([\w:.-]+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s>]+))?/g;
    let attr;
    while ((attr = attrRe.exec(match[2] || '')) !== null) {
      element._attrs[String(attr[1]).toLowerCase()] = String(attr[2] || '').replace(
        /^["']|["']$/g,
        ''
      );
    }
    const parent = stack[stack.length - 1];
    if (parent) {
      element.parentNode = parent;
      parent.children.push(element);
    } else {
      nodes.push(element);
    }
    if (!VOID[tag] && !match[3]) stack.push(element);
  }
  return nodes;
}

function __setHTML(el, value) {
  const text = String(value);
  el.children = [];
  el._text = '';
  el._html = '';
  if (text.indexOf('<') !== -1) {
    __parseHTML(text).forEach((node) => {
      node.parentNode = el;
      el.children.push(node);
    });
  } else {
    el._html = text;
  }
}

function __matchesCompound(node, compound) {
  if (!node || !node._attrs) return false;
  // `:not(...)` is stripped and evaluated separately so it can be used freely.
  const negations = [];
  compound = String(compound).replace(/:not\(([^)]*)\)/g, (_m, inner) => {
    negations.push(inner.trim());
    return '';
  });
  compound = compound.replace(/:[a-z-]+(\([^)]*\))?/g, '');
  for (const negation of negations) {
    if (negation && __matchesCompound(node, negation)) return false;
  }
  if (!compound) return true;
  const re = /^([a-zA-Z][\w-]*|\*)?((?:[.#][\w-]+|\[[\w-]+(?:[~|^$*]?=["']?[^\]"']*["']?)?\])*)$/;
  const m = re.exec(compound);
  if (!m) return false;
  const tag = m[1];
  const rest = m[2] || '';
  if (!tag && !rest) return false;
  if (tag && tag !== '*' && String(node.tagName).toLowerCase() !== tag.toLowerCase()) return false;
  const tokens = rest.match(/[.#][\w-]+|\[[^\]]+\]/g) || [];
  for (const token of tokens) {
    if (token[0] === '.') {
      if (!node.classList.contains(token.slice(1))) return false;
    } else if (token[0] === '#') {
      if (node.id !== token.slice(1)) return false;
    } else {
      const inner = token.slice(1, -1);
      const eq = inner.indexOf('=');
      if (eq === -1) {
        if (node._attrs[inner.toLowerCase()] === undefined) return false;
      } else {
        const name = inner.slice(0, eq).replace(/[~|^$*]$/, '').toLowerCase();
        const wanted = inner.slice(eq + 1).replace(/^["']|["']$/g, '');
        const actual = node._attrs[name];
        if (actual === undefined || String(actual).indexOf(wanted) === -1) return false;
      }
    }
  }
  return true;
}

function __matchesSel(node, selector) {
  return String(selector)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .some((single) => {
      const parts = single.split(/\s+/).filter((p) => p && p !== '>');
      if (!parts.length) return false;
      if (!__matchesCompound(node, parts[parts.length - 1])) return false;
      let index = parts.length - 2;
      let ancestor = node.parentNode;
      while (index >= 0) {
        let matched = false;
        while (ancestor && ancestor._attrs) {
          const current = ancestor;
          ancestor = ancestor.parentNode;
          if (__matchesCompound(current, parts[index])) {
            matched = true;
            break;
          }
        }
        if (!matched) return false;
        index--;
      }
      return true;
    });
}

function __descendants(node) {
  const out = [];
  (node.children || []).forEach((child) => {
    out.push(child);
    __descendants(child).forEach((deep) => out.push(deep));
  });
  return out;
}

function __queryAll(node, selector) {
  return __descendants(node).filter((child) => __matchesSel(child, selector));
}

function __serialize(node, depth) {
  if (!node || !node._attrs || (depth || 0) > 8) return '';
  const tag = String(node.tagName || 'div').toLowerCase();
  const attrs = Object.keys(node._attrs)
    .map((k) => ' ' + k + '="' + node._attrs[k] + '"')
    .join('');
  const inner = node._html + __serializeChildren(node, (depth || 0) + 1) + node._text;
  return '<' + tag + attrs + '>' + inner + '</' + tag + '>';
}

function __serializeChildren(node, depth) {
  return (node.children || []).map((child) => __serialize(child, depth)).join('');
}

function __makeElement(tag) {
  const el = {
    tagName: String(tag || 'div').toUpperCase(),
    _attrs: {},
    _html: '',
    _text: '',
    _listeners: {},
    children: [],
    parentNode: null,
    style: {},
    value: '',
    checked: false,
    disabled: false,
  };
  el.appendChild = (child) => {
    if (child && child._attrs) {
      child.parentNode = el;
      el.children.push(child);
    } else {
      el._text += String(child);
    }
    __recordWrite();
    return child;
  };
  el.append = function () {
    Array.prototype.slice.call(arguments).forEach((kid) => {
      if (kid && kid._attrs) {
        kid.parentNode = el;
        el.children.push(kid);
      } else {
        el._text += String(kid);
      }
    });
    __recordWrite();
  };
  el.prepend = function () {
    Array.prototype.slice.call(arguments).forEach((kid) => {
      if (kid && kid._attrs) {
        kid.parentNode = el;
        el.children.unshift(kid);
      }
    });
    __recordWrite();
  };
  el.replaceChildren = function () {
    el.children = Array.prototype.slice.call(arguments).filter((k) => k && k._attrs);
    el.children.forEach((k) => {
      k.parentNode = el;
    });
    el._html = '';
    el._text = '';
    __recordWrite();
  };
  el.removeChild = (child) => {
    el.children = el.children.filter((c) => c !== child);
    __recordWrite();
    return child;
  };
  el.remove = () => {
    if (el.parentNode && el.parentNode.children) {
      el.parentNode.children = el.parentNode.children.filter((c) => c !== el);
    }
    __recordWrite();
  };
  el.insertAdjacentHTML = (_position, html) => {
    const text = String(html);
    if (text.indexOf('<') !== -1) {
      __parseHTML(text).forEach((node) => {
        node.parentNode = el;
        el.children.push(node);
      });
    } else {
      el._html += text;
    }
    __recordWrite();
  };
  el.insertAdjacentElement = (_position, child) => {
    child.parentNode = el;
    el.children.push(child);
    __recordWrite();
    return child;
  };
  el.setAttribute = (name, value) => {
    el._attrs[String(name).toLowerCase()] = String(value);
    __recordWrite();
  };
  el.getAttribute = (name) => {
    const value = el._attrs[String(name).toLowerCase()];
    return value === undefined ? null : value;
  };
  el.removeAttribute = (name) => {
    delete el._attrs[String(name).toLowerCase()];
    __recordWrite();
  };
  el.hasAttribute = (name) => el._attrs[String(name).toLowerCase()] !== undefined;
  el.addEventListener = (type, handler) => {
    (el._listeners[type] = el._listeners[type] || []).push(handler);
    __note();
  };
  el.removeEventListener = (type, handler) => {
    el._listeners[type] = (el._listeners[type] || []).filter((h) => h !== handler);
  };
  el.querySelector = (selector) => __queryAll(el, selector)[0] || null;
  el.querySelectorAll = (selector) => __queryAll(el, selector);
  el.getElementsByClassName = (name) => __queryAll(el, '.' + name);
  el.matches = (selector) => __matchesSel(el, selector);
  el.closest = (selector) => {
    let node = el;
    while (node && node._attrs) {
      if (__matchesSel(node, selector)) return node;
      node = node.parentNode;
    }
    return null;
  };
  el.contains = (other) => {
    let node = other;
    while (node) {
      if (node === el) return true;
      node = node.parentNode;
    }
    return false;
  };
  el.focus = () => {};
  el.blur = () => {};
  el.reset = () => {
    __queryAll(el, 'input').forEach((input) => {
      input.value = '';
    });
    __recordWrite();
  };
  const readClasses = () => String(el._attrs['class'] || '').split(/\s+/).filter(Boolean);
  const writeClasses = (list) => {
    el._attrs['class'] = list.join(' ');
    __recordWrite();
  };
  el.classList = {
    add: function () {
      const set = new Set(readClasses());
      Array.prototype.slice.call(arguments).forEach((c) => set.add(c));
      writeClasses(Array.from(set));
    },
    remove: function () {
      const set = new Set(readClasses());
      Array.prototype.slice.call(arguments).forEach((c) => set.delete(c));
      writeClasses(Array.from(set));
    },
    toggle: (c, force) => {
      const set = new Set(readClasses());
      const on = force === undefined ? !set.has(c) : Boolean(force);
      if (on) set.add(c);
      else set.delete(c);
      writeClasses(Array.from(set));
      return on;
    },
    contains: (c) => readClasses().indexOf(c) !== -1,
  };
  Object.defineProperty(el, 'className', {
    get: () => String(el._attrs['class'] || ''),
    set: (value) => {
      el._attrs['class'] = String(value);
      __recordWrite();
    },
  });
  Object.defineProperty(el, 'id', {
    get: () => String(el._attrs['id'] || ''),
    set: (value) => {
      el._attrs['id'] = String(value);
      __recordWrite();
    },
  });
  Object.defineProperty(el, 'dataset', {
    get: () => {
      const data = {};
      Object.keys(el._attrs).forEach((key) => {
        if (key.indexOf('data-') === 0) {
          const name = key.slice(5).replace(/-([a-z])/g, (_m, c) => c.toUpperCase());
          data[name] = el._attrs[key];
        }
      });
      return data;
    },
  });
  Object.defineProperty(el, 'innerHTML', {
    get: () => el._html + __serializeChildren(el, 0) + el._text,
    set: (value) => {
      __setHTML(el, value);
      __recordWrite();
    },
  });
  Object.defineProperty(el, 'outerHTML', {
    get: () => __serialize(el, 0),
  });
  Object.defineProperty(el, 'textContent', {
    get: () =>
      __norm((el._html + __serializeChildren(el, 0)).replace(/<[^>]*>/g, ' ') + ' ' + el._text),
    set: (value) => {
      el._text = String(value);
      el._html = '';
      el.children = [];
      __recordWrite();
    },
  });
  Object.defineProperty(el, 'innerText', {
    get: () => el.textContent,
    set: (value) => {
      el._text = String(value);
      el._html = '';
      el.children = [];
      __recordWrite();
    },
  });
  return el;
}

const __documentNode = {
  _listeners: {},
  addEventListener(type, handler) {
    (__documentNode._listeners[type] = __documentNode._listeners[type] || []).push(handler);
    __note();
  },
  removeEventListener() {},
  createElement: (tag) => __makeElement(tag),
  createTextNode: (text) => {
    const node = __makeElement('span');
    node._text = String(text);
    return node;
  },
  createDocumentFragment: () => __makeElement('div'),
  getElementById: (id) => {
    if (!__root) return null;
    if (__root.id === id) return __root;
    return __queryAll(__root, '#' + id)[0] || null;
  },
  querySelector: (selector) => {
    if (!__root) return null;
    if (__matchesSel(__root, selector)) return __root;
    return __queryAll(__root, selector)[0] || null;
  },
  querySelectorAll: (selector) => (__root ? __queryAll(__root, selector) : []),
  getElementsByClassName: (name) => (__root ? __queryAll(__root, '.' + name) : []),
};
Object.defineProperty(__documentNode, 'body', { get: () => __root });
Object.defineProperty(__documentNode, 'documentElement', { get: () => __root });
globalThis.document = __documentNode;
globalThis.window = globalThis;
globalThis.alert = () => {};
globalThis.localStorage = {
  _data: {},
  getItem(k) {
    const v = globalThis.localStorage._data[k];
    return v === undefined ? null : v;
  },
  setItem(k, v) {
    globalThis.localStorage._data[k] = String(v);
  },
  removeItem(k) {
    delete globalThis.localStorage._data[k];
  },
};

// ------------------------------------------------------------------ events

function __makeEvent(type, target, extra) {
  const event = {
    type: type,
    target: target,
    currentTarget: target,
    defaultPrevented: false,
    _stopped: false,
    preventDefault() {
      event.defaultPrevented = true;
      __prevented = true;
    },
    stopPropagation() {
      event._stopped = true;
    },
    stopImmediatePropagation() {
      event._stopped = true;
    },
  };
  Object.keys(extra || {}).forEach((key) => {
    event[key] = extra[key];
  });
  return event;
}

//: Dispatches `type` on `element` and bubbles it up to document, exactly like
//: a browser, so event delegation is genuinely exercised.
function __fire(element, type, extra) {
  if (!element) {
    return 'the grader could not find the element it needed to click — the page markup it relies on is missing';
  }
  const event = __makeEvent(type, element, extra);
  let node = element;
  while (node) {
    event.currentTarget = node;
    const handlers = ((node._listeners || {})[type] || []).slice();
    for (const handler of handlers) {
      try {
        __track(typeof handler === 'function' ? handler.call(node, event) : handler.handleEvent(event));
      } catch (e) {
        __recordError(e);
      }
    }
    if (event._stopped) break;
    node = node.parentNode || (node === __root ? __documentNode : null);
    if (node === __documentNode && element === __documentNode) break;
  }
  return true;
}

function __setValue(selector, value) {
  const element = __el(selector);
  if (!element) return 'the input ' + selector + ' is missing from the page';
  element.value = String(value);
  return true;
}

// ------------------------------------------------------- assertion helpers

function __resetDom() {
  __root = __buildDom();
  __documentNode._listeners = {};
  __writes = 0;
  __prevented = false;
  __requestStarted = false;
  __domAtRequest = '';
  __postRequestWrites = 0;
  __resetErrors();
}

function __el(selector) {
  return __documentNode.querySelector(selector);
}

function __all() {
  for (let i = 0; i < arguments.length; i++) {
    const value = arguments[i];
    if (value === true) continue;
    if (typeof value === 'string') return value;
    return 'the expected behaviour was not observed';
  }
  return true;
}

function __errorSuffix() {
  if (!__runtimeErrors.length) return '';
  return ' (your code threw ' + __runtimeErrors.join('; ') + ')';
}

//: The single most common false pass: the right function is declared and never
//: invoked. Nothing in the page changed, so say precisely that.
function __ranAtAll() {
  if (__writes === 0) {
    return (
      'your code never changed the page — declaring the function is not enough, ' +
      'it has to be called' +
      __errorSuffix()
    );
  }
  if (__runtimeErrors.length) {
    return 'your code threw while running: ' + __runtimeErrors.join('; ');
  }
  return true;
}

function __noThrow() {
  if (__runtimeErrors.length) {
    return 'your code threw instead of handling the situation: ' + __runtimeErrors.join('; ');
  }
  return true;
}

function __expectText(selector, expected) {
  const element = __el(selector);
  if (!element) {
    return 'no element matches ' + selector + ' — either the page was never updated or you removed markup the page needs';
  }
  const actual = __norm(element.textContent);
  if (actual.indexOf(String(expected)) === -1) {
    return selector + ' shows "' + (actual || '(empty)') + '" but it must contain "' + expected + '"' + __errorSuffix();
  }
  return true;
}

function __expectNoText(selector, forbidden) {
  const element = __el(selector);
  if (!element) return 'no element matches ' + selector;
  const actual = __norm(element.textContent);
  if (actual.indexOf(String(forbidden)) !== -1) {
    return selector + ' still shows "' + forbidden + '", which must not be there once the page is up to date';
  }
  return true;
}

function __expectNonEmpty(selector) {
  const element = __el(selector);
  if (!element) return 'no element matches ' + selector;
  if (!__norm(element.textContent)) {
    return selector + ' is empty, so the user is told nothing' + __errorSuffix();
  }
  return true;
}

function __expectEmpty(selector) {
  const element = __el(selector);
  if (!element) return 'no element matches ' + selector;
  const actual = __norm(element.textContent);
  if (actual) {
    return selector + ' should be empty here but shows "' + actual + '"';
  }
  return true;
}

function __countIn(selector, needle) {
  const element = __el(selector);
  if (!element) return -1;
  const html = element.innerHTML;
  let count = 0;
  let index = html.indexOf(needle);
  while (index !== -1) {
    count++;
    index = html.indexOf(needle, index + needle.length);
  }
  return count;
}

async function __settle() {
  const bound = await __drain();
  if (bound === 'timeout') {
    return 'your asynchronous work never settled — the grader stopped waiting';
  }
  if (bound === 'rounds') {
    return 'your code kept scheduling asynchronous work and never settled';
  }
  return true;
}

// ------------------------------------------------- loading / error evidence

const __LOADING_RE = /\b(loading|spinner|skeleton|fetching)\b|please\s+wait/i;
const __ERROR_HOOK_RE =
  /(class|id|role|data-[\w-]*)\s*=\s*["']?[^"'>]*\b(error|errors|alert|danger|fail|failed|failure|warning|problem)\b/i;
const __FAILURE_WORDS_RE =
  /\b(error|failed|failure|unable|cannot|can't|couldn't|could\s+not|went\s+wrong|try\s+again|retry|problem|oops|sorry|unavailable|denied|timed\s+out|timeout|refused|offline|down)\b/i;

function __regionText(selector) {
  const element = __el(selector);
  if (!element) return '';
  return [
    element.innerHTML,
    element.textContent,
    Object.keys(element._attrs || {})
      .map((k) => k + '="' + element._attrs[k] + '"')
      .join(' '),
  ].join(' ');
}

//: Same standard as `ticket_templates.__expectErrorState`: writes after the
//: failure, a changed visible state, and something genuinely error-shaped. A
//: leftover spinner or an empty region is never an error state.
function __expectErrorState(selector) {
  if (__postRequestWrites === 0) {
    return (
      'nothing was written to the page after the request failed — the failure path ' +
      'never rendered an error state (console.error is not a UI)' +
      __errorSuffix()
    );
  }
  const text = __regionText(selector).trim();
  if (!text) {
    return 'the page is empty after the failure, so the user is told nothing' + __errorSuffix();
  }
  if (text === __domAtRequest.trim()) {
    return 'the page still shows exactly what it showed before the request' + __errorSuffix();
  }
  if (__LOADING_RE.test(text) && !__ERROR_HOOK_RE.test(text) && !__FAILURE_WORDS_RE.test(text)) {
    return 'the page still shows the loading state instead of an error state' + __errorSuffix();
  }
  if (!__ERROR_HOOK_RE.test(text) && !__FAILURE_WORDS_RE.test(text)) {
    return (
      'the page changed but shows nothing error-shaped — render a visible message ' +
      '(or an element with an error/alert class or role)' +
      __errorSuffix()
    );
  }
  return true;
}

function __expectLoadingWasShown() {
  if (!__requestStarted) {
    return 'the request was never made, so the page never loaded anything' + __errorSuffix();
  }
  if (!__LOADING_RE.test(__domAtRequest)) {
    return (
      'nothing on the page said it was loading when the request started — render the ' +
      'loading state *before* you await' +
      __errorSuffix()
    );
  }
  return true;
}

function __expectLoadingCleared(selector) {
  const text = __regionText(selector);
  if (__LOADING_RE.test(text)) {
    return 'the loading state is still on the page after the request settled' + __errorSuffix();
  }
  return true;
}
"""


def _prelude(module_specific: str) -> str:
    return DOM_SHIM + module_specific


SYNTAX_CHECK_HINT = "The file must parse before any behaviour can be verified."


def _syntax_check(file: str = "script.js") -> dict[str, Any]:
    return {
        "id": "syntax",
        "requirement_index": None,
        "precondition": True,
        "type": "js_syntax",
        "file": file,
        "label": f"{file} is valid JavaScript",
        "concept": "syntax",
        "hint": SYNTAX_CHECK_HINT,
    }


def _no_dead_code_check() -> dict[str, Any]:
    return {
        "id": "no_dead_code",
        "requirement_index": None,
        "type": "js_no_unreachable",
        "file": "script.js",
        "label": "No unreachable code after a return or throw",
        "concept": "control flow",
        "hint": "Statements written after an unconditional return never run — move them above it.",
    }


# ---------------------------------------------------------------------------
# 1. Variables, types and coercion — order summary
# ---------------------------------------------------------------------------

ORDER_SUMMARY_HTML = _page(
    "Order Summary",
    """    <main class="panel">
      <h1>Order summary</h1>
      <p class="subtitle">Basket totals for the current customer.</p>
      <p id="itemCount" class="muted">—</p>
      <ul id="lineItems"></ul>
      <div id="totals">
        <div class="row"><span>Subtotal</span><span id="subtotal">—</span></div>
        <div class="row"><span>Shipping</span><span id="shipping">—</span></div>
        <div class="row"><strong>Total</strong><strong id="total">—</strong></div>
      </div>
      <p id="emptyNote" class="muted"></p>
    </main>
""",
)

ORDER_SUMMARY_DATA = """// Given and locked. The basket arrives from the checkout API, where every
// numeric field is a *string* — that is exactly how the real endpoint behaves.
const ORDER = {
  shipping: "4.99",
  items: [
    { name: "Enamel mug", price: "12.50", quantity: "2" },
    { name: "Sticker pack", price: "3.25", quantity: "4" },
  ],
};
"""

ORDER_SUMMARY_STARTER = """// The JavaScript layer was removed. ORDER comes from data.js (locked).
// Every price and quantity in ORDER is a STRING. Convert before you calculate.

function toNumber(value) {
  // TODO: return `value` as a number, and 0 when it is empty/not numeric.
}

function formatMoney(amount) {
  // TODO: return the amount with exactly two decimals, e.g. 12.5 -> "12.50".
}

function renderOrderSummary(order) {
  // TODO
  // 1. total quantity  -> #itemCount, as "N items"
  // 2. subtotal        -> #subtotal  (sum of price * quantity)
  // 3. shipping        -> #shipping
  // 4. subtotal + shipping -> #total
  // 5. with no items: put a message in #emptyNote and add the "hidden"
  //    class to #totals; with items, #emptyNote must stay empty.
}

// TODO: call renderOrderSummary(ORDER) so the page renders on load.
"""

ORDER_SUMMARY_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const count = __makeElement('p');
  count.setAttribute('id', 'itemCount');
  count._text = '—';
  const items = __makeElement('ul');
  items.setAttribute('id', 'lineItems');
  const totals = __makeElement('div');
  totals.setAttribute('id', 'totals');
  ['subtotal', 'shipping', 'total'].forEach((id) => {
    const row = __makeElement('div');
    row.setAttribute('class', 'row');
    const value = __makeElement('span');
    value.setAttribute('id', id);
    value._text = '—';
    row.children.push(value);
    value.parentNode = row;
    totals.children.push(row);
    row.parentNode = totals;
  });
  const note = __makeElement('p');
  note.setAttribute('id', 'emptyNote');
  [count, items, totals, note].forEach((child) => {
    child.parentNode = root;
    root.children.push(child);
  });
  return root;
}

function __setup(order) {
  globalThis.ORDER = order;
  __resetDom();
}

//: The grader computes the truth itself, so the answer is never in the module.
function __expected(order) {
  const items = order.items || [];
  const quantity = items.reduce((n, i) => n + Number(i.quantity), 0);
  const subtotal = items.reduce((s, i) => s + Number(i.price) * Number(i.quantity), 0);
  return {
    quantity: String(quantity),
    subtotal: subtotal.toFixed(2),
    shipping: Number(order.shipping || 0).toFixed(2),
    total: (subtotal + Number(order.shipping || 0)).toFixed(2),
  };
}
"""

ORDER_SUMMARY_MODULE: dict[str, Any] = {
    "id": "js-order-summary-types",
    "title": "Order Summary — Numbers, Strings and Coercion",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_basics",
    "technology": "JavaScript",
    "difficulty": 2,
    "estimated_minutes": 25,
    "summary": "The checkout API sends every price as a string. The page renders em dashes because the JavaScript layer is missing — make the totals correct.",
    "problem_statement": (
        "The order summary page is fully built and styled, and `data.js` provides an `ORDER` "
        "object straight from the checkout API. Every price and quantity in it is a **string**, "
        "which is why naive arithmetic produces \"12.503.25\" instead of a total.\n\n"
        "Write `script.js` so the page shows the item count, subtotal, shipping and total, "
        "formatted to exactly two decimals — and so an empty basket shows a message instead of "
        "meaningless zeros."
    ),
    "constraints": [
        "index.html, styles.css and data.js are locked — only script.js may change.",
        "Do not hard-code any total: the grader renders your file against several different baskets.",
        "Money must always show exactly two decimals (12.5 renders as \"12.50\").",
        "Use the existing element ids; do not add or rename markup.",
    ],
    "requirements": [
        "Convert the string prices and quantities to numbers before doing any arithmetic",
        "Render the total quantity of items into #itemCount",
        "Render the subtotal (price × quantity, summed) into #subtotal with two decimals",
        "Render the shipping cost into #shipping and subtotal + shipping into #total",
        "With an empty basket, write a message into #emptyNote and add the \"hidden\" class to #totals",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": ORDER_SUMMARY_HTML,
        "styles.css": PRACTICE_CSS,
        "data.js": ORDER_SUMMARY_DATA,
        "script.js": ORDER_SUMMARY_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "converts_numbers",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(Number\(|parseFloat\(|parseInt\(|\+\s*(?:item|line|order|value|price|quantity|qty)\b)",
            "label": "Converts the string fields to numbers explicitly",
            "concept": "type coercion",
            "hint": "Number(value) or parseFloat(value) turns \"12.50\" into 12.5; \"a\" + \"b\" concatenates instead of adding.",
        },
        {
            "id": "to_number_real",
            "requirement_index": 0,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "toNumber",
            "label": "toNumber has a real implementation",
            "concept": "type coercion",
            "hint": "The stub returns nothing. Convert the value and guard against an empty or non-numeric string.",
        },
        {
            "id": "format_real",
            "requirement_index": 2,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "formatMoney",
            "label": "formatMoney has a real implementation",
            "concept": "numbers",
            "hint": "toFixed(2) formats a number to two decimals — but it only exists on numbers, not strings.",
        },
        {
            "id": "render_real",
            "requirement_index": 1,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "renderOrderSummary",
            "label": "renderOrderSummary has a real implementation",
            "concept": "DOM updates",
            "hint": "The body is still a comment. Read the totals you calculated into the page's elements.",
        },
        {
            "id": "writes_dom",
            "requirement_index": 3,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(textContent|innerText|innerHTML)\s*=",
            "label": "Writes the values back into the page",
            "concept": "DOM updates",
            "hint": "Assign to element.textContent — calculating the number is only half the job.",
        },
        {
            "id": "empty_state",
            "requirement_index": 4,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(classList\.(add|toggle)\(\s*[\"']hidden[\"']|className\s*=\s*[\"'][^\"']*hidden)",
            "label": "Hides #totals with the \"hidden\" class when the basket is empty",
            "concept": "conditionals",
            "hint": "The stylesheet already defines .hidden — add that class rather than inventing a new style.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(ORDER_SUMMARY_PRELUDE),
        "assertions": [
            {
                "id": "renders_totals",
                "requirement_indexes": [1, 2, 3],
                "label": "renders the item count, subtotal, shipping and total for the given basket",
                "concept": "DOM updates",
                "hint": "Read ORDER, calculate, then write each value into its element with textContent.",
                "expression": (
                    "const order = { shipping: '4.99', items: ["
                    " { name: 'Enamel mug', price: '12.50', quantity: '2' },"
                    " { name: 'Sticker pack', price: '3.25', quantity: '4' } ] };"
                    " __setup(order); await __userMain(); const e = __expected(order);"
                    " return __all(__ranAtAll(), __expectText('#itemCount', e.quantity),"
                    " __expectText('#subtotal', e.subtotal), __expectText('#shipping', e.shipping),"
                    " __expectText('#total', e.total));"
                ),
            },
            {
                "id": "no_string_concatenation",
                "requirement_index": 0,
                "label": "adds the prices numerically instead of concatenating the strings",
                "concept": "type coercion",
                "hint": "\"10.00\" + \"5.50\" is \"10.005.50\". Convert both sides to numbers first.",
                "expression": (
                    "const order = { shipping: '0', items: ["
                    " { name: 'A', price: '10.00', quantity: '1' },"
                    " { name: 'B', price: '5.50', quantity: '1' } ] };"
                    " __setup(order); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#subtotal', '15.50'),"
                    " __expectNoText('#subtotal', '10.005.50'), __expectText('#total', '15.50'));"
                ),
            },
            {
                "id": "empty_basket",
                "requirement_index": 4,
                "label": "an empty basket shows a message and hides the totals block",
                "concept": "conditionals",
                "hint": "With no items there is nothing to total: write a note into #emptyNote and add \"hidden\" to #totals.",
                "expression": (
                    "__setup({ shipping: '0', items: [] }); await __userMain();"
                    " const ran = __ranAtAll(); if (ran !== true) return ran;"
                    " const totals = __el('#totals');"
                    " if (!totals) return 'the #totals block is gone from the page';"
                    " if (!totals.classList.contains('hidden'))"
                    "   return 'the basket is empty but #totals is still visible — add the \"hidden\" class';"
                    " return __all(__ranAtAll(), __expectNonEmpty('#emptyNote'));"
                ),
            },
            {
                "id": "quantities_multiply",
                "requirement_indexes": [1, 2],
                "hidden": True,
                "label": "multiplies price by quantity rather than summing the prices",
                "concept": "numbers",
                "hint": "Three of an item costs three times as much: price * quantity per line.",
                "expression": (
                    "const order = { shipping: '2.00', items: ["
                    " { name: 'Pin', price: '4.00', quantity: '3' } ] };"
                    " __setup(order); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#itemCount', '3'),"
                    " __expectText('#subtotal', '12.00'), __expectText('#total', '14.00'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 2. Functions, scope and closures — independent counter widgets
# ---------------------------------------------------------------------------

COUNTERS_HTML = _page(
    "Seat Counters",
    """    <main class="panel">
      <h1>Seat counters</h1>
      <p class="subtitle">Each screen counts its own seats, in its own step.</p>
      <section class="counter" id="counter-stalls" data-step="2">
        <h2>Stalls</h2>
        <span data-role="value">0</span>
        <button type="button" data-role="increment">Add seats</button>
        <button type="button" data-role="reset">Reset</button>
      </section>
      <section class="counter" id="counter-balcony" data-step="5">
        <h2>Balcony</h2>
        <span data-role="value">0</span>
        <button type="button" data-role="increment">Add seats</button>
        <button type="button" data-role="reset">Reset</button>
      </section>
    </main>
""",
    data_file=False,
)

COUNTERS_STARTER = """// The JavaScript layer was removed.
// Every .counter section on the page must work on its own, with its own count.
// The step to add per click is on the section as data-step.

function createCounter(section) {
  // TODO
  // 1. keep this section's count in a variable declared INSIDE this function
  // 2. read the step from section.dataset.step (it is a string)
  // 3. return an object of functions that change *this* section's count
  //    and write it into that section's [data-role="value"] element
}

// TODO: find every .counter section and wire it up with createCounter,
// attaching click listeners to its increment and reset buttons.
"""

COUNTERS_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  (globalThis.__COUNTERS || []).forEach((spec) => {
    const section = __makeElement('section');
    section.setAttribute('class', 'counter');
    section.setAttribute('id', spec.id);
    section.setAttribute('data-step', spec.step);
    const value = __makeElement('span');
    value.setAttribute('data-role', 'value');
    value._text = '0';
    const increment = __makeElement('button');
    increment.setAttribute('data-role', 'increment');
    increment._text = 'Add seats';
    const reset = __makeElement('button');
    reset.setAttribute('data-role', 'reset');
    reset._text = 'Reset';
    [value, increment, reset].forEach((child) => {
      child.parentNode = section;
      section.children.push(child);
    });
    section.parentNode = root;
    root.children.push(section);
  });
  return root;
}

function __setup(counters) {
  globalThis.__COUNTERS = counters;
  __resetDom();
}

function __value(id) {
  const element = __el('#' + id + ' [data-role="value"]');
  if (!element) return null;
  return __norm(element.textContent);
}

function __clickIn(id, role) {
  return __fire(__el('#' + id + ' [data-role="' + role + '"]'), 'click');
}

function __expectValue(id, expected) {
  const actual = __value(id);
  if (actual === null) return 'the value element inside #' + id + ' disappeared from the page';
  if (actual.indexOf(String(expected)) === -1) {
    return '#' + id + ' shows "' + (actual || '(empty)') + '" but should show ' + expected + __errorSuffix();
  }
  return true;
}

const __TWO_COUNTERS = [
  { id: 'counter-stalls', step: '2' },
  { id: 'counter-balcony', step: '5' },
];
"""

COUNTERS_MODULE: dict[str, Any] = {
    "id": "js-seat-counters-closures",
    "title": "Seat Counters — Functions, Scope and Closures",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_functions",
    "technology": "JavaScript",
    "difficulty": 4,
    "estimated_minutes": 30,
    "summary": "Two counter widgets share one page. Write a factory function so each keeps its own private count — a shared global will be caught.",
    "problem_statement": (
        "The page renders several `.counter` sections. Each has its own step (`data-step`), its "
        "own value element and its own buttons, and each must count independently: adding seats "
        "in the stalls must not move the balcony.\n\n"
        "Write a `createCounter(section)` factory that keeps the count in a variable inside "
        "itself — a closure — and returns the functions that change it. Then wire up every "
        "`.counter` on the page. The grader runs your file against pages with different numbers "
        "of counters and different steps."
    ),
    "constraints": [
        "index.html and styles.css are locked — only script.js may change.",
        "One shared count variable for all widgets will fail: each widget owns its own state.",
        "The step must come from the section's data-step attribute, not from a literal in your code.",
        "Use addEventListener; inline onclick attributes are not available (the HTML is locked).",
    ],
    "requirements": [
        "Write a createCounter(section) factory that holds that section's count in a variable inside itself",
        "Read the step for each widget from its data-step attribute and convert it to a number",
        "Return functions from the factory that increment and reset only that section's count",
        "Wire up every .counter section on the page (there may be more than two)",
        "Write each new count into that section's [data-role=\"value\"] element",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": COUNTERS_HTML,
        "styles.css": PRACTICE_CSS,
        "script.js": COUNTERS_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "factory_exists",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(function\s+createCounter\s*\(|createCounter\s*=\s*(function|\())",
            "label": "Declares a createCounter factory",
            "concept": "functions",
            "hint": "Keep the name createCounter — the requirements and the grader both refer to it.",
        },
        {
            "id": "factory_real",
            "requirement_index": 0,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "createCounter",
            "label": "createCounter has a real implementation",
            "concept": "closures",
            "hint": "Declare the count inside createCounter, then return functions that close over it.",
        },
        {
            "id": "reads_step",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(dataset\.step|getAttribute\(\s*[\"']data-step[\"']\s*\))",
            "label": "Reads the step from the data-step attribute",
            "concept": "dataset",
            "hint": "section.dataset.step gives you the string \"2\" — convert it before adding.",
        },
        {
            "id": "wires_every_counter",
            "requirement_index": 3,
            "type": "js_calls",
            "file": "script.js",
            "callee": "querySelectorAll",
            "label": "Selects every .counter with querySelectorAll",
            "concept": "querySelector",
            "hint": "querySelector finds one section only; the page can have any number of counters.",
        },
        {
            "id": "listens",
            "requirement_index": 2,
            "type": "js_calls",
            "file": "script.js",
            "callee": "addEventListener",
            "min_count": 1,
            "label": "Genuinely calls addEventListener",
            "concept": "event listeners",
            "hint": "A handler that is never registered never runs.",
        },
        {
            "id": "no_shared_global_count",
            "requirement_index": 0,
            "type": "not_regex",
            "file": "script.js",
            "pattern": r"(?m)^(let|var)\s+(count|total|seats|value)\s*=",
            "label": "No single top-level count variable shared by every widget",
            "concept": "scope",
            "hint": "A count declared at the top level is shared by all widgets — declare it inside the factory.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(COUNTERS_PRELUDE),
        "assertions": [
            {
                "id": "increments_by_step",
                "requirement_indexes": [1, 4],
                "label": "each widget adds its own data-step on every click",
                "concept": "closures",
                "hint": "Two clicks on a step-2 widget shows 4; the balcony's step is different on purpose.",
                "expression": (
                    "__setup(__TWO_COUNTERS); await __userMain();"
                    " const fired = __all(__clickIn('counter-stalls', 'increment'),"
                    " __clickIn('counter-stalls', 'increment'));"
                    " if (fired !== true) return fired;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectValue('counter-stalls', '4'));"
                ),
            },
            {
                "id": "widgets_are_independent",
                "requirement_indexes": [0, 3],
                "label": "clicking one widget never changes the other",
                "concept": "closures",
                "hint": "If both widgets move together, they are sharing one variable — move it inside the factory.",
                "expression": (
                    "__setup(__TWO_COUNTERS); await __userMain();"
                    " const fired = __all(__clickIn('counter-stalls', 'increment'),"
                    " __clickIn('counter-balcony', 'increment'));"
                    " if (fired !== true) return fired;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectValue('counter-stalls', '2'),"
                    " __expectValue('counter-balcony', '5'));"
                ),
            },
            {
                "id": "reset_is_local",
                "requirement_index": 2,
                "label": "reset zeroes only the widget whose button was clicked",
                "concept": "scope",
                "hint": "Reset must set this section's own count back to 0 and repaint only this section.",
                "expression": (
                    "__setup(__TWO_COUNTERS); await __userMain();"
                    " const fired = __all(__clickIn('counter-stalls', 'increment'),"
                    " __clickIn('counter-balcony', 'increment'),"
                    " __clickIn('counter-balcony', 'increment'),"
                    " __clickIn('counter-stalls', 'reset'));"
                    " if (fired !== true) return fired;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectValue('counter-stalls', '0'),"
                    " __expectValue('counter-balcony', '10'));"
                ),
            },
            {
                "id": "works_for_three_widgets",
                "requirement_indexes": [1, 3],
                "hidden": True,
                "label": "works on a page with three counters and different steps",
                "concept": "functions",
                "hint": "Loop over every .counter the page contains and read each one's own step.",
                "expression": (
                    "__setup([{ id: 'counter-a', step: '3' }, { id: 'counter-b', step: '7' },"
                    " { id: 'counter-c', step: '1' }]); await __userMain();"
                    " const fired = __all(__clickIn('counter-a', 'increment'),"
                    " __clickIn('counter-c', 'increment'), __clickIn('counter-c', 'increment'));"
                    " if (fired !== true) return fired;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectValue('counter-a', '3'),"
                    " __expectValue('counter-b', '0'), __expectValue('counter-c', '2'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 3. Array methods doing real work — inventory report
# ---------------------------------------------------------------------------

INVENTORY_HTML = _page(
    "Inventory Report",
    """    <main class="panel">
      <h1>Inventory report</h1>
      <p class="subtitle">Everything currently on the shelves.</p>
      <ul id="productList">
        <li class="muted">Loading products…</li>
      </ul>
      <div class="row"><span>Stock value</span><span id="stockValue">—</span></div>
      <div class="row"><span>Out of stock</span><span id="outOfStock">—</span></div>
    </main>
""",
)

INVENTORY_DATA = """// Given and locked. The warehouse feed for today.
const PRODUCTS = [
  { name: "Espresso beans", price: 8.5, stock: 12 },
  { name: "Cold brew kit", price: 24, stock: 0 },
  { name: "Paper filters", price: 3.2, stock: 40 },
  { name: "Travel mug", price: 15, stock: 0 },
];
"""

INVENTORY_STARTER = """// The JavaScript layer was removed. PRODUCTS comes from data.js (locked).
// Build the report with array methods — filter, map and reduce.

function inStock(products) {
  // TODO: return only the products whose stock is greater than 0 (use filter).
}

function stockValue(products) {
  // TODO: return the total value of the stock, price * stock summed (use reduce).
}

function renderInventory(products) {
  // TODO
  // 1. replace everything inside #productList with one <li class="product">
  //    per in-stock product, showing its name and price (use map)
  // 2. write the total stock value into #stockValue with two decimals
  // 3. write how many products are out of stock into #outOfStock
}

// TODO: call renderInventory(PRODUCTS) so the report renders on load.
"""

INVENTORY_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const list = __makeElement('ul');
  list.setAttribute('id', 'productList');
  const placeholder = __makeElement('li');
  placeholder.setAttribute('class', 'muted');
  placeholder._text = 'Loading products…';
  placeholder.parentNode = list;
  list.children.push(placeholder);
  const value = __makeElement('span');
  value.setAttribute('id', 'stockValue');
  value._text = '—';
  const out = __makeElement('span');
  out.setAttribute('id', 'outOfStock');
  out._text = '—';
  [list, value, out].forEach((child) => {
    child.parentNode = root;
    root.children.push(child);
  });
  return root;
}

function __setup(products) {
  globalThis.PRODUCTS = products;
  __resetDom();
}

function __expected(products) {
  const kept = products.filter((p) => p.stock > 0);
  return {
    names: kept.map((p) => p.name),
    missing: products.filter((p) => p.stock <= 0).map((p) => p.name),
    value: products.reduce((sum, p) => sum + p.price * p.stock, 0).toFixed(2),
    outOfStock: String(products.filter((p) => p.stock <= 0).length),
  };
}

function __expectListNames(expected, forbidden) {
  const list = __el('#productList');
  if (!list) return 'the #productList element is gone from the page';
  const html = list.innerHTML;
  for (const name of expected) {
    if (html.indexOf(name) === -1) {
      return '"' + name + '" is in stock but was not rendered into #productList' + __errorSuffix();
    }
  }
  for (const name of forbidden) {
    if (html.indexOf(name) !== -1) {
      return '"' + name + '" has no stock and must be filtered out, but it was rendered';
    }
  }
  if (__LOADING_RE.test(html)) {
    return 'the "Loading products…" placeholder is still in #productList — replace it with your rows';
  }
  return true;
}
"""

INVENTORY_MODULE: dict[str, Any] = {
    "id": "js-inventory-report-arrays",
    "title": "Inventory Report — filter, map and reduce",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_functions",
    "technology": "JavaScript",
    "difficulty": 3,
    "estimated_minutes": 30,
    "summary": "Turn a warehouse feed into a report: filter out what is unavailable, map the rest to rows, reduce the stock to a total.",
    "problem_statement": (
        "`data.js` provides `PRODUCTS`, today's warehouse feed. The page is built and styled but "
        "still shows the \"Loading products…\" placeholder because the JavaScript layer is "
        "missing.\n\n"
        "Render one `<li class=\"product\">` per **in-stock** product, show the total value of all "
        "stock on hand, and show how many products are out of stock. The grader runs your file "
        "against several different feeds, so every number has to be derived from the data."
    ),
    "constraints": [
        "index.html, styles.css and data.js are locked — only script.js may change.",
        "Use filter, map and reduce for the work they are for; do not hand-roll them with index loops.",
        "The placeholder <li> must be gone once your rows are rendered.",
        "Stock value renders with exactly two decimals.",
    ],
    "requirements": [
        "Use filter to keep only the products with stock greater than 0",
        "Use map to build one <li class=\"product\"> per in-stock product, showing its name and price",
        "Replace the contents of #productList with those rows (the placeholder must go)",
        "Use reduce to total price × stock across all products and render it in #stockValue with two decimals",
        "Render how many products are out of stock into #outOfStock",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": INVENTORY_HTML,
        "styles.css": PRACTICE_CSS,
        "data.js": INVENTORY_DATA,
        "script.js": INVENTORY_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "uses_filter",
            "requirement_index": 0,
            "type": "js_calls",
            "file": "script.js",
            "callee": ".filter",
            "label": "Genuinely calls .filter",
            "concept": "array methods",
            "hint": "filter returns a new array of the items whose callback returned true.",
        },
        {
            "id": "uses_map",
            "requirement_index": 1,
            "type": "js_calls",
            "file": "script.js",
            "callee": ".map",
            "label": "Genuinely calls .map",
            "concept": "array methods",
            "hint": "map turns each product into its markup; join(\"\") glues the pieces together.",
        },
        {
            "id": "uses_reduce",
            "requirement_index": 3,
            "type": "js_calls",
            "file": "script.js",
            "callee": ".reduce",
            "label": "Genuinely calls .reduce",
            "concept": "array methods",
            "hint": "reduce carries a running total: (sum, product) => sum + product.price * product.stock.",
        },
        {
            "id": "in_stock_real",
            "requirement_index": 0,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "inStock",
            "label": "inStock has a real implementation",
            "concept": "array methods",
            "hint": "Return the filtered array — the stub currently returns nothing.",
        },
        {
            "id": "stock_value_real",
            "requirement_index": 3,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "stockValue",
            "label": "stockValue has a real implementation",
            "concept": "array methods",
            "hint": "Sum price * stock over every product and return the number.",
        },
        {
            "id": "render_real",
            "requirement_index": 2,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "renderInventory",
            "label": "renderInventory has a real implementation",
            "concept": "DOM updates",
            "hint": "Write the rows and both totals into the page from inside this function.",
        },
        {
            "id": "product_class",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"[\"'`][^\"'`]*\bproduct\b|classList\.add\(\s*[\"']product[\"']",
            "label": "Rows carry the \"product\" class",
            "concept": "DOM updates",
            "hint": "The stylesheet and the grader both look for <li class=\"product\">.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(INVENTORY_PRELUDE),
        "assertions": [
            {
                "id": "renders_only_in_stock",
                "requirement_indexes": [0, 1, 2],
                "label": "renders a row per in-stock product and drops the out-of-stock ones",
                "concept": "array methods",
                "hint": "Filter first, then map the survivors into rows and replace the list's contents.",
                "expression": (
                    "const products = ["
                    " { name: 'Espresso beans', price: 8.5, stock: 12 },"
                    " { name: 'Cold brew kit', price: 24, stock: 0 },"
                    " { name: 'Paper filters', price: 3.2, stock: 40 } ];"
                    " __setup(products); await __userMain(); const e = __expected(products);"
                    " return __all(__ranAtAll(), __expectListNames(e.names, e.missing));"
                ),
            },
            {
                "id": "totals_the_stock_value",
                "requirement_indexes": [3, 4],
                "label": "totals the stock value and counts the out-of-stock products",
                "concept": "reduce",
                "hint": "The stock value covers every product's price × stock; the count is how many have none left.",
                "expression": (
                    "const products = ["
                    " { name: 'Espresso beans', price: 8.5, stock: 12 },"
                    " { name: 'Cold brew kit', price: 24, stock: 0 },"
                    " { name: 'Paper filters', price: 3.2, stock: 40 },"
                    " { name: 'Travel mug', price: 15, stock: 0 } ];"
                    " __setup(products); await __userMain(); const e = __expected(products);"
                    " return __all(__ranAtAll(), __expectText('#stockValue', e.value),"
                    " __expectText('#outOfStock', e.outOfStock));"
                ),
            },
            {
                "id": "another_feed",
                "requirement_indexes": [2, 3],
                "hidden": True,
                "label": "produces the right report for a different feed",
                "concept": "array methods",
                "hint": "Every number must come from the data, never from a literal you typed.",
                "expression": (
                    "const products = ["
                    " { name: 'Grinder', price: 45.5, stock: 2 },"
                    " { name: 'Scale', price: 30, stock: 1 } ];"
                    " __setup(products); await __userMain(); const e = __expected(products);"
                    " return __all(__ranAtAll(), __expectListNames(e.names, e.missing),"
                    " __expectText('#stockValue', e.value), __expectText('#outOfStock', '0'));"
                ),
            },
            {
                "id": "empty_feed_is_survivable",
                "requirement_index": 4,
                "hidden": True,
                "label": "an empty feed renders a zero report instead of crashing",
                "concept": "array methods",
                "hint": "reduce needs an initial value when the array can be empty.",
                "expression": (
                    "__setup([]); await __userMain();"
                    " return __all(__noThrow(), __expectText('#stockValue', '0.00'),"
                    " __expectText('#outOfStock', '0'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 4. Objects, destructuring and spread — settings panel
# ---------------------------------------------------------------------------

SETTINGS_HTML = _page(
    "Account Settings",
    """    <main class="panel">
      <h1>Account settings</h1>
      <p class="subtitle">Your preferences, on top of the workspace defaults.</p>
      <div class="row"><span>Theme</span><span id="theme">—</span></div>
      <div class="row"><span>Font size</span><span id="fontSize">—</span></div>
      <div class="row"><span>Notifications</span><span id="notifications">—</span></div>
      <div class="row"><span>Language</span><span id="language">—</span></div>
    </main>
""",
)

SETTINGS_DATA = """// Given and locked. DEFAULT_SETTINGS is shared by every user on the workspace,
// so it must never be modified. USER_SETTINGS holds only what this user changed.
const DEFAULT_SETTINGS = {
  theme: "dark",
  fontSize: "medium",
  notifications: "on",
  language: "en",
};

const USER_SETTINGS = {
  fontSize: "large",
  notifications: "off",
};
"""

SETTINGS_STARTER = """// The JavaScript layer was removed.
// DEFAULT_SETTINGS and USER_SETTINGS come from data.js (locked).
// DEFAULT_SETTINGS is shared across the whole workspace: never modify it.

function mergeSettings(defaults, overrides) {
  // TODO: return a NEW object: the defaults, with the overrides applied on top.
}

function renderSettings(settings) {
  // TODO
  // 1. destructure theme, fontSize, notifications and language out of `settings`
  // 2. write each one into the element with the matching id
}

// TODO: merge the two objects and render the result on load.
"""

SETTINGS_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  ['theme', 'fontSize', 'notifications', 'language'].forEach((id) => {
    const row = __makeElement('div');
    row.setAttribute('class', 'row');
    const value = __makeElement('span');
    value.setAttribute('id', id);
    value._text = '—';
    value.parentNode = row;
    row.children.push(value);
    row.parentNode = root;
    root.children.push(row);
  });
  return root;
}

let __defaultsSnapshot = '';

function __setup(defaults, overrides) {
  globalThis.DEFAULT_SETTINGS = defaults;
  globalThis.USER_SETTINGS = overrides;
  __defaultsSnapshot = JSON.stringify(defaults);
  __resetDom();
}

function __expected(defaults, overrides) {
  return Object.assign({}, defaults, overrides);
}

//: Proves the merge produced a new object instead of writing into the shared
//: defaults — the exact bug `Object.assign(defaults, overrides)` introduces.
function __expectDefaultsUntouched() {
  const now = JSON.stringify(globalThis.DEFAULT_SETTINGS);
  if (now !== __defaultsSnapshot) {
    return (
      'DEFAULT_SETTINGS was modified (it is now ' +
      now +
      ' instead of ' +
      __defaultsSnapshot +
      ') — the shared defaults must be copied, not written into'
    );
  }
  return true;
}
"""

SETTINGS_MODULE: dict[str, Any] = {
    "id": "js-settings-merge-objects",
    "title": "Account Settings — Objects, Destructuring and Spread",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_basics",
    "technology": "JavaScript",
    "difficulty": 3,
    "estimated_minutes": 25,
    "summary": "Layer a user's overrides on top of the workspace defaults and render the result — without mutating the shared defaults object.",
    "problem_statement": (
        "`data.js` gives you `DEFAULT_SETTINGS` (shared by every user on the workspace) and "
        "`USER_SETTINGS` (only the keys this user changed). The settings panel currently shows em "
        "dashes.\n\n"
        "Merge the two — overrides winning, missing keys falling back to the default — and render "
        "each value into its row. `DEFAULT_SETTINGS` is shared state: if your merge writes into "
        "it, the next user inherits this user's preferences, and the grader checks for exactly "
        "that."
    ),
    "constraints": [
        "index.html, styles.css and data.js are locked — only script.js may change.",
        "DEFAULT_SETTINGS must hold the same values after your code runs as before it.",
        "Build the merged object with the spread syntax; do not assign key by key.",
        "Read the values out of the merged object with destructuring.",
    ],
    "requirements": [
        "Write mergeSettings(defaults, overrides) that returns a new object using the spread syntax",
        "Keys the user did not override keep their default value",
        "Read theme, fontSize, notifications and language out of the merged object with destructuring",
        "Render each value into the element whose id matches its key",
        "Leave DEFAULT_SETTINGS unmodified — never mutate the shared defaults",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": SETTINGS_HTML,
        "styles.css": PRACTICE_CSS,
        "data.js": SETTINGS_DATA,
        "script.js": SETTINGS_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "uses_spread",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"\{\s*\.\.\.",
            "label": "Builds the merged object with the spread syntax",
            "concept": "spread",
            "hint": "{ ...defaults, ...overrides } copies both into a brand-new object.",
        },
        {
            "id": "merge_real",
            "requirement_index": 0,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "mergeSettings",
            "label": "mergeSettings has a real implementation",
            "concept": "objects",
            "hint": "Return the merged object — the stub returns nothing at all.",
        },
        {
            "id": "destructures",
            "requirement_index": 2,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(const|let)\s*\{[^}]*\}\s*=",
            "label": "Reads the values with object destructuring",
            "concept": "destructuring",
            "hint": "const { theme, fontSize, notifications, language } = settings;",
        },
        {
            "id": "render_real",
            "requirement_index": 3,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "renderSettings",
            "label": "renderSettings has a real implementation",
            "concept": "DOM updates",
            "hint": "Write each destructured value into its row inside this function.",
        },
        {
            "id": "writes_dom",
            "requirement_index": 3,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(textContent|innerText|innerHTML)\s*=",
            "label": "Writes the merged values into the page",
            "concept": "DOM updates",
            "hint": "Assign to textContent on each row's span.",
        },
        {
            "id": "no_default_mutation",
            "requirement_index": 4,
            "type": "not_regex",
            "file": "script.js",
            "pattern": r"(DEFAULT_SETTINGS\s*\[?\.?\w*\s*=[^=]|Object\.assign\(\s*DEFAULT_SETTINGS|Object\.assign\(\s*defaults\b)",
            "label": "Never assigns into the shared defaults",
            "concept": "immutability",
            "hint": "Object.assign(defaults, overrides) writes into its first argument — pass {} first, or use spread.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(SETTINGS_PRELUDE),
        "assertions": [
            {
                "id": "overrides_win",
                "requirement_indexes": [0, 3],
                "label": "the user's overrides are what gets rendered",
                "concept": "objects",
                "hint": "The overrides go last in the spread so they win over the defaults.",
                "expression": (
                    "const defaults = { theme: 'dark', fontSize: 'medium', notifications: 'on', language: 'en' };"
                    " const overrides = { fontSize: 'large', notifications: 'off' };"
                    " __setup(defaults, overrides); await __userMain();"
                    " const e = __expected(defaults, overrides);"
                    " return __all(__ranAtAll(), __expectText('#fontSize', e.fontSize),"
                    " __expectText('#notifications', e.notifications));"
                ),
            },
            {
                "id": "defaults_fill_the_gaps",
                "requirement_indexes": [1, 2],
                "label": "keys the user never set fall back to the default",
                "concept": "destructuring",
                "hint": "A key missing from the overrides must still render its default value, not \"undefined\".",
                "expression": (
                    "const defaults = { theme: 'dark', fontSize: 'medium', notifications: 'on', language: 'en' };"
                    " const overrides = { fontSize: 'large' };"
                    " __setup(defaults, overrides); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#theme', 'dark'),"
                    " __expectText('#language', 'en'), __expectNoText('#theme', 'undefined'));"
                ),
            },
            {
                "id": "defaults_not_mutated",
                "requirement_index": 4,
                "label": "DEFAULT_SETTINGS still holds its original values afterwards",
                "concept": "immutability",
                "hint": "Copy the defaults into a new object; never write the overrides into them.",
                "expression": (
                    "const defaults = { theme: 'dark', fontSize: 'medium', notifications: 'on', language: 'en' };"
                    " const overrides = { theme: 'light', fontSize: 'small' };"
                    " __setup(defaults, overrides); await __userMain();"
                    " return __all(__ranAtAll(), __expectDefaultsUntouched(),"
                    " __expectText('#theme', 'light'));"
                ),
            },
            {
                "id": "another_user",
                "requirement_indexes": [1, 3],
                "hidden": True,
                "label": "renders a different user's overrides correctly",
                "concept": "objects",
                "hint": "Nothing may be hard-coded: read every value out of the merged object.",
                "expression": (
                    "const defaults = { theme: 'dark', fontSize: 'medium', notifications: 'on', language: 'en' };"
                    " const overrides = { language: 'fr', theme: 'light' };"
                    " __setup(defaults, overrides); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#language', 'fr'),"
                    " __expectText('#theme', 'light'), __expectText('#fontSize', 'medium'),"
                    " __expectText('#notifications', 'on'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 5. DOM selection and mutation — task board
# ---------------------------------------------------------------------------

TASKBOARD_HTML = _page(
    "Sprint Board",
    """    <main class="panel">
      <h1>Sprint board</h1>
      <p class="subtitle">What the team is working on right now.</p>
      <p id="taskCount" class="muted">—</p>
      <ul id="taskList">
        <li class="muted">Loading tasks…</li>
      </ul>
      <p id="emptyState" class="muted"></p>
    </main>
""",
)

TASKBOARD_DATA = """// Given and locked. The board's tasks for this sprint.
const TASKS = [
  { title: "Wire up the checkout button", status: "done" },
  { title: "Write the pricing tests", status: "doing" },
  { title: "Fix the mobile nav", status: "todo" },
];
"""

TASKBOARD_STARTER = """// The JavaScript layer was removed. TASKS comes from data.js (locked).

function renderTasks(tasks) {
  // TODO
  // 1. select #taskList and replace its contents (the placeholder must go)
  // 2. add one <li> per task, with class "task" plus the task's status as a
  //    second class, and the task's title as its text
  // 3. write "N tasks" into #taskCount
  // 4. with no tasks: write a message into #emptyState; otherwise leave it empty
}

// TODO: call renderTasks(TASKS) so the board renders on load.
"""

TASKBOARD_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const count = __makeElement('p');
  count.setAttribute('id', 'taskCount');
  count._text = '—';
  const list = __makeElement('ul');
  list.setAttribute('id', 'taskList');
  const placeholder = __makeElement('li');
  placeholder.setAttribute('class', 'muted');
  placeholder._text = 'Loading tasks…';
  placeholder.parentNode = list;
  list.children.push(placeholder);
  const empty = __makeElement('p');
  empty.setAttribute('id', 'emptyState');
  [count, list, empty].forEach((child) => {
    child.parentNode = root;
    root.children.push(child);
  });
  return root;
}

function __setup(tasks) {
  globalThis.TASKS = tasks;
  __resetDom();
}

function __expectTasksRendered(tasks) {
  const list = __el('#taskList');
  if (!list) return 'the #taskList element is gone from the page';
  const html = list.innerHTML;
  if (__LOADING_RE.test(html)) {
    return 'the "Loading tasks…" placeholder is still inside #taskList — replace the list contents';
  }
  for (const task of tasks) {
    if (html.indexOf(task.title) === -1) {
      return '"' + task.title + '" was never rendered into #taskList' + __errorSuffix();
    }
    if (html.indexOf(task.status) === -1) {
      return 'the task status "' + task.status + '" is not in the markup — each row needs its status as a class';
    }
  }
  const rows = __countIn('#taskList', 'task');
  if (rows < tasks.length) {
    return 'expected ' + tasks.length + ' rows with the "task" class but found ' + rows;
  }
  return true;
}
"""

TASKBOARD_MODULE: dict[str, Any] = {
    "id": "js-taskboard-dom-render",
    "title": "Sprint Board — DOM Selection and Mutation",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_dom",
    "technology": "JavaScript",
    "difficulty": 3,
    "estimated_minutes": 25,
    "summary": "The board is stuck on \"Loading tasks…\". Select the list, build a row per task and keep the header count and empty state honest.",
    "problem_statement": (
        "The sprint board's markup and styling are done, and `data.js` provides `TASKS`. Nothing "
        "renders because `script.js` is empty, so the page still shows its placeholder row.\n\n"
        "Replace the contents of `#taskList` with one row per task — carrying both the `task` "
        "class and the task's status as a class so the stylesheet can colour it — keep "
        "`#taskCount` in sync, and show a message in `#emptyState` when the sprint has no tasks "
        "at all. The grader renders your file against several different boards."
    ),
    "constraints": [
        "index.html, styles.css and data.js are locked — only script.js may change.",
        "The \"Loading tasks…\" placeholder must not survive your render.",
        "Rows must carry the task class plus the task's own status as a class.",
        "Do not use document.write.",
    ],
    "requirements": [
        "Select #taskList from the DOM and replace its contents with your own rows",
        "Render one row per task, carrying the \"task\" class and the task's status as a class",
        "Show each task's title as the row's text",
        "Write the number of tasks into #taskCount",
        "With no tasks, write a message into #emptyState (and leave it empty otherwise)",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": TASKBOARD_HTML,
        "styles.css": PRACTICE_CSS,
        "data.js": TASKBOARD_DATA,
        "script.js": TASKBOARD_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "selects_list",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(getElementById\(\s*[\"']taskList[\"']\s*\)|querySelector\(\s*[\"']#taskList[\"']\s*\))",
            "label": "Selects #taskList from the DOM",
            "concept": "querySelector",
            "hint": "document.getElementById(\"taskList\") or document.querySelector(\"#taskList\").",
        },
        {
            "id": "render_real",
            "requirement_index": 1,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "renderTasks",
            "label": "renderTasks has a real implementation",
            "concept": "DOM updates",
            "hint": "The body is still comments — build the rows and write them into the list.",
        },
        {
            "id": "iterates",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(\.map\(|\.forEach\(|for\s*\(|for\s+(const|let)\s+\w+\s+of)",
            "label": "Iterates over the tasks",
            "concept": "iteration",
            "hint": "One row per task means looping (or mapping) over the array.",
        },
        {
            "id": "inserts",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(innerHTML\s*=|appendChild\(|append\(|replaceChildren\(|insertAdjacentHTML\()",
            "label": "Inserts the rows into the list",
            "concept": "DOM updates",
            "hint": "Building elements is not enough — put them into #taskList.",
        },
        {
            "id": "status_class",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(class(Name|List)|class=)",
            "label": "Gives each row its classes",
            "concept": "classList",
            "hint": "Each row needs class=\"task <status>\" so the stylesheet can colour it.",
        },
        {
            "id": "count",
            "requirement_index": 3,
            "type": "regex",
            "file": "script.js",
            "pattern": r"\.length",
            "label": "Derives the count from the data",
            "concept": "DOM updates",
            "hint": "tasks.length is the count — never type the number yourself.",
        },
        {
            "id": "no_document_write",
            "requirement_index": 0,
            "type": "not_regex",
            "file": "script.js",
            "pattern": r"document\.write",
            "label": "Does not use document.write",
            "concept": "DOM updates",
            "hint": "document.write blows away the whole page after load.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(TASKBOARD_PRELUDE),
        "assertions": [
            {
                "id": "renders_rows",
                "requirement_indexes": [0, 1, 2],
                "label": "renders one classed row per task and clears the placeholder",
                "concept": "DOM updates",
                "hint": "Replace the list's contents, then add a row per task with its title and status.",
                "expression": (
                    "const tasks = ["
                    " { title: 'Wire up the checkout button', status: 'done' },"
                    " { title: 'Write the pricing tests', status: 'doing' },"
                    " { title: 'Fix the mobile nav', status: 'todo' } ];"
                    " __setup(tasks); await __userMain();"
                    " return __all(__ranAtAll(), __expectTasksRendered(tasks));"
                ),
            },
            {
                "id": "count_matches",
                "requirement_index": 3,
                "label": "#taskCount reports how many tasks were rendered",
                "concept": "DOM updates",
                "hint": "Derive the number from the array's length so it stays right for any board.",
                "expression": (
                    "const tasks = ["
                    " { title: 'Ship the invoice PDF', status: 'doing' },"
                    " { title: 'Add the audit log', status: 'todo' } ];"
                    " __setup(tasks); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#taskCount', '2'),"
                    " __expectTasksRendered(tasks), __expectEmpty('#emptyState'));"
                ),
            },
            {
                "id": "empty_board",
                "requirement_index": 4,
                "label": "an empty board shows the empty state and no rows",
                "concept": "conditionals",
                "hint": "With no tasks there is nothing to list: tell the user so in #emptyState.",
                "expression": (
                    "__setup([]); await __userMain();"
                    " const list = __el('#taskList');"
                    " if (!list) return 'the #taskList element is gone from the page';"
                    " if (__LOADING_RE.test(list.innerHTML))"
                    "   return 'the loading placeholder is still there even though the board is empty';"
                    " return __all(__ranAtAll(), __expectNonEmpty('#emptyState'),"
                    " __expectText('#taskCount', '0'));"
                ),
            },
            {
                "id": "different_board",
                "requirement_indexes": [1, 3],
                "hidden": True,
                "label": "renders a completely different board correctly",
                "concept": "DOM updates",
                "hint": "Everything on screen must be derived from the data you were given.",
                "expression": (
                    "const tasks = ["
                    " { title: 'Rotate the API keys', status: 'todo' },"
                    " { title: 'Delete the dead feature flag', status: 'done' },"
                    " { title: 'Backfill the search index', status: 'doing' },"
                    " { title: 'Trim the bundle', status: 'todo' } ];"
                    " __setup(tasks); await __userMain();"
                    " return __all(__ranAtAll(), __expectTasksRendered(tasks),"
                    " __expectText('#taskCount', '4'), __expectEmpty('#emptyState'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 6. Event handling and delegation — inbox
# ---------------------------------------------------------------------------

INBOX_HTML = _page(
    "Inbox",
    """    <main class="panel">
      <h1>Inbox</h1>
      <p class="subtitle">Click a message to mark it read.</p>
      <p id="unreadCount" class="muted">—</p>
      <ul id="messageList"></ul>
    </main>
""",
)

INBOX_DATA = """// Given and locked. More messages arrive while the page is open, so the list
// grows after your code has already run.
const MESSAGES = [
  { id: "m1", subject: "Standup moved to 09:30" },
  { id: "m2", subject: "Invoice #4021 approved" },
  { id: "m3", subject: "New comment on PR 88" },
];
"""

INBOX_STARTER = """// The JavaScript layer was removed. MESSAGES comes from data.js (locked).
// Messages can arrive AFTER your code has run, and they must work too — so
// attach ONE listener to the list and let the clicks bubble up to it.

function renderMessages(messages) {
  // TODO: render one <li class="message" data-id="..."> per message into
  // #messageList, showing its subject.
}

function updateUnreadCount() {
  // TODO: write how many messages are still unread into #unreadCount.
}

// TODO
// 1. render the messages
// 2. attach a single click listener to #messageList
// 3. in the handler, find the clicked message with event.target.closest(...),
//    add the "read" class to it and refresh the unread count
"""

INBOX_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const count = __makeElement('p');
  count.setAttribute('id', 'unreadCount');
  count._text = '—';
  const list = __makeElement('ul');
  list.setAttribute('id', 'messageList');
  [count, list].forEach((child) => {
    child.parentNode = root;
    root.children.push(child);
  });
  return root;
}

function __setup(messages) {
  globalThis.MESSAGES = messages;
  __resetDom();
}

function __messageEl(id) {
  return __el('.message[data-id="' + id + '"]') || __el('[data-id="' + id + '"]');
}

function __clickMessage(id) {
  const element = __messageEl(id);
  if (!element) {
    return (
      'no element with data-id="' + id + '" is in the list — each message needs ' +
      'class="message" and its data-id so a delegated click can identify it'
    );
  }
  return __fire(element, 'click', {});
}

function __expectRead(id, shouldBeRead) {
  const element = __messageEl(id);
  if (!element) return 'message ' + id + ' is missing from the list';
  const isRead = element.classList.contains('read');
  if (shouldBeRead && !isRead) {
    return 'message ' + id + ' was clicked but never got the "read" class' + __errorSuffix();
  }
  if (!shouldBeRead && isRead) {
    return 'message ' + id + ' was never clicked but is marked read — only the clicked message changes';
  }
  return true;
}

//: A per-message listener cannot handle a message the harness appends later, so
//: this is what separates real delegation from a forEach over the rows.
function __appendLateMessage(id, subject) {
  const list = __el('#messageList');
  if (!list) return 'the #messageList element is gone from the page';
  const item = __makeElement('li');
  item.setAttribute('class', 'message');
  item.setAttribute('data-id', id);
  item._text = subject;
  item.parentNode = list;
  list.children.push(item);
  return true;
}

function __expectSingleContainerListener() {
  const list = __el('#messageList');
  if (!list) return 'the #messageList element is gone from the page';
  const onContainer = ((list._listeners || {}).click || []).length;
  const onRows = __el('#messageList')
    ? __documentNode.querySelectorAll('#messageList .message').reduce(
        (n, row) => n + (((row._listeners || {}).click || []).length),
        0
      )
    : 0;
  if (onRows > 0) {
    return (
      'you attached ' + onRows + ' click listener(s) to the individual messages — delegate ' +
      'from the #messageList container instead so later messages work too'
    );
  }
  if (onContainer === 0) {
    return 'nothing listens for clicks on #messageList, so clicking a message does nothing';
  }
  if (onContainer > 1) {
    return 'there are ' + onContainer + ' click listeners on #messageList — one is enough';
  }
  return true;
}
"""

INBOX_MODULE: dict[str, Any] = {
    "id": "js-inbox-event-delegation",
    "title": "Inbox — Event Handling and Delegation",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_dom",
    "technology": "JavaScript",
    "difficulty": 5,
    "estimated_minutes": 35,
    "summary": "Mark messages read on click with a single delegated listener — messages that arrive after your code has run must work too.",
    "problem_statement": (
        "The inbox renders a list of messages and clicking one should mark it read and update the "
        "unread counter. New messages arrive while the page is open and are appended to "
        "`#messageList` by other code, **after** your script has already run.\n\n"
        "That rules out attaching a listener to each row: attach exactly one listener to the "
        "container, find the clicked message from `event.target`, and mark only that message. The "
        "grader appends a message after your file runs and clicks it."
    ),
    "constraints": [
        "index.html, styles.css and data.js are locked — only script.js may change.",
        "Exactly one click listener, on the #messageList container. Per-row listeners fail.",
        "Each row must carry class \"message\" and its data-id.",
        "Clicking a message must not change any other message.",
    ],
    "requirements": [
        "Render one <li class=\"message\" data-id=\"…\"> per message into #messageList, showing its subject",
        "Attach a single click listener to the #messageList container rather than to each message",
        "In the handler, find the clicked message from event.target with closest()",
        "Add the \"read\" class to the clicked message only",
        "Keep #unreadCount showing how many messages are still unread",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": INBOX_HTML,
        "styles.css": PRACTICE_CSS,
        "data.js": INBOX_DATA,
        "script.js": INBOX_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "listener",
            "requirement_index": 1,
            "type": "js_calls",
            "file": "script.js",
            "callee": "addEventListener",
            "min_count": 1,
            "label": "Genuinely calls addEventListener",
            "concept": "event listeners",
            "hint": "The word in a comment does not count — register the handler.",
        },
        {
            "id": "click_type",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"addEventListener\(\s*[\"']click[\"']",
            "label": "Listens for the click event",
            "concept": "event listeners",
            "hint": "addEventListener(\"click\", handler) on the container element.",
        },
        {
            "id": "no_per_row_listeners",
            "requirement_index": 1,
            "type": "not_regex",
            "file": "script.js",
            "pattern": r"(forEach|map)\s*\(([^)]|\n){0,200}?addEventListener",
            "label": "Does not attach a listener inside a loop over the messages",
            "concept": "event delegation",
            "hint": "Looping over the rows to add listeners misses every message added later.",
        },
        {
            "id": "uses_closest",
            "requirement_index": 2,
            "type": "js_calls",
            "file": "script.js",
            "callee": "closest",
            "label": "Finds the clicked message with closest()",
            "concept": "event delegation",
            "hint": "event.target may be a child element — event.target.closest(\".message\") walks up to the row.",
        },
        {
            "id": "marks_read",
            "requirement_index": 3,
            "type": "regex",
            "file": "script.js",
            "pattern": r"classList\.(add|toggle)\(\s*[\"']read[\"']",
            "label": "Adds the \"read\" class to the clicked message",
            "concept": "classList",
            "hint": "The stylesheet already fades .read rows — add that exact class.",
        },
        {
            "id": "data_id",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"data-id",
            "label": "Rows carry their data-id",
            "concept": "dataset",
            "hint": "Render data-id=\"...\" on each row so the handler can tell which message was clicked.",
        },
        {
            "id": "unread_count_real",
            "requirement_index": 4,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "updateUnreadCount",
            "label": "updateUnreadCount has a real implementation",
            "concept": "DOM updates",
            "hint": "Count the rows that are not .read and write that number into #unreadCount.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(INBOX_PRELUDE),
        "assertions": [
            {
                "id": "renders_messages",
                "requirement_indexes": [0, 4],
                "label": "renders every message with its subject and shows the unread count",
                "concept": "DOM updates",
                "hint": "Render the rows first — the click handling has nothing to work on otherwise.",
                "expression": (
                    "const messages = [{ id: 'm1', subject: 'Standup moved to 09:30' },"
                    " { id: 'm2', subject: 'Invoice #4021 approved' }];"
                    " __setup(messages); await __userMain();"
                    " return __all(__ranAtAll(), __expectText('#messageList', 'Standup moved to 09:30'),"
                    " __expectText('#messageList', 'Invoice #4021 approved'),"
                    " __expectText('#unreadCount', '2'));"
                ),
            },
            {
                "id": "click_marks_only_that_message",
                "requirement_indexes": [2, 3, 4],
                "label": "clicking one message marks only it read and updates the count",
                "concept": "event handling",
                "hint": "Use closest() to get the clicked row, then add the class to that row alone.",
                "expression": (
                    "const messages = [{ id: 'm1', subject: 'Standup moved to 09:30' },"
                    " { id: 'm2', subject: 'Invoice #4021 approved' },"
                    " { id: 'm3', subject: 'New comment on PR 88' }];"
                    " __setup(messages); await __userMain();"
                    " const clicked = __clickMessage('m2'); if (clicked !== true) return clicked;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectRead('m2', true), __expectRead('m1', false),"
                    " __expectRead('m3', false), __expectText('#unreadCount', '2'));"
                ),
            },
            {
                "id": "delegation_covers_later_messages",
                "requirement_index": 1,
                "label": "a message appended after your code ran is still clickable",
                "concept": "event delegation",
                "hint": "One listener on the container handles rows that did not exist when it was attached.",
                "expression": (
                    "const messages = [{ id: 'm1', subject: 'Standup moved to 09:30' }];"
                    " __setup(messages); await __userMain();"
                    " const added = __appendLateMessage('late-1', 'Deploy finished');"
                    " if (added !== true) return added;"
                    " const clicked = __clickMessage('late-1'); if (clicked !== true) return clicked;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectRead('late-1', true));"
                ),
            },
            {
                "id": "one_listener_on_the_container",
                "requirement_index": 1,
                "label": "exactly one click listener, and it is on the container",
                "concept": "event delegation",
                "hint": "Attach to #messageList once, outside any loop over the messages.",
                "expression": (
                    "const messages = [{ id: 'm1', subject: 'A' }, { id: 'm2', subject: 'B' }];"
                    " __setup(messages); await __userMain();"
                    " return __all(__ranAtAll(), __expectSingleContainerListener());"
                ),
            },
            {
                "id": "clicking_twice_is_idempotent",
                "requirement_index": 4,
                "hidden": True,
                "label": "clicking the same message twice does not double-count",
                "concept": "event handling",
                "hint": "Derive the unread count from the rows that are not .read rather than decrementing a number.",
                "expression": (
                    "const messages = [{ id: 'm1', subject: 'A' }, { id: 'm2', subject: 'B' },"
                    " { id: 'm3', subject: 'C' }];"
                    " __setup(messages); await __userMain();"
                    " const first = __clickMessage('m1'); if (first !== true) return first;"
                    " const second = __clickMessage('m1'); if (second !== true) return second;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectRead('m1', true),"
                    " __expectText('#unreadCount', '2'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 7. Forms and input validation — signup
# ---------------------------------------------------------------------------

SIGNUP_HTML = _page(
    "Create Account",
    """    <main class="panel">
      <h1>Create account</h1>
      <p class="subtitle">Validation happens in the browser before anything is sent.</p>
      <form id="signupForm">
        <div class="field">
          <label for="email">Email</label>
          <input id="email" name="email" type="text" />
          <p id="emailError" class="error"></p>
        </div>
        <div class="field">
          <label for="password">Password</label>
          <input id="password" name="password" type="password" />
          <p id="passwordError" class="error"></p>
        </div>
        <button id="submitBtn" type="submit">Create account</button>
        <p id="formSuccess" class="success"></p>
      </form>
    </main>
""",
    data_file=False,
)

SIGNUP_STARTER = """// The JavaScript layer was removed.
// The form must be validated in the browser: nothing is submitted to a server.

function validate(email, password) {
  // TODO: return the problems you found, e.g. { email: "...", password: "..." }
  // Rules: the email must not be blank once trimmed and must contain "@";
  //        the password must be at least 8 characters long.
}

// TODO
// 1. listen for the form's "submit" event
// 2. stop the browser from submitting it
// 3. show each problem in #emailError / #passwordError
// 4. when everything is valid, clear both error messages and show a
//    confirmation in #formSuccess
"""

SIGNUP_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const form = __makeElement('form');
  form.setAttribute('id', 'signupForm');
  const build = (tag, attrs) => {
    const node = __makeElement(tag);
    Object.keys(attrs).forEach((key) => node.setAttribute(key, attrs[key]));
    return node;
  };
  const children = [
    build('input', { id: 'email', name: 'email', type: 'text' }),
    build('p', { id: 'emailError', class: 'error' }),
    build('input', { id: 'password', name: 'password', type: 'password' }),
    build('p', { id: 'passwordError', class: 'error' }),
    build('button', { id: 'submitBtn', type: 'submit' }),
    build('p', { id: 'formSuccess', class: 'success' }),
  ];
  children.forEach((child) => {
    child.parentNode = form;
    form.children.push(child);
  });
  form.parentNode = root;
  root.children.push(form);
  return root;
}

function __setup() {
  __resetDom();
}

//: Fills the inputs and submits the form the way a browser would, then reports
//: whether the default navigation was prevented.
function __submit(email, password) {
  const filled = __all(__setValue('#email', email), __setValue('#password', password));
  if (filled !== true) return filled;
  const form = __el('#signupForm');
  if (!form) return 'the #signupForm element is gone from the page';
  __prevented = false;
  return __fire(form, 'submit', {});
}

function __expectPrevented() {
  if (!__prevented) {
    return (
      'the submit event was never prevented, so the browser would reload the page and ' +
      'throw away your validation — call event.preventDefault()'
    );
  }
  return true;
}
"""

SIGNUP_MODULE: dict[str, Any] = {
    "id": "js-signup-form-validation",
    "title": "Create Account — Forms and Input Validation",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_dom",
    "technology": "JavaScript",
    "difficulty": 4,
    "estimated_minutes": 30,
    "summary": "Validate the signup form in the browser: block the submit, explain each problem next to its field, and only then confirm success.",
    "problem_statement": (
        "The signup form is built and styled, with an empty error paragraph under each field and "
        "an empty `#formSuccess` line. Right now submitting it reloads the page and nothing is "
        "checked.\n\n"
        "Handle the form's `submit` event: stop the browser from submitting, validate the email "
        "(non-blank once trimmed, and containing `@`) and the password (at least 8 characters), "
        "put a message in the matching error paragraph for each problem, and show a confirmation "
        "in `#formSuccess` only when both fields are valid."
    ),
    "constraints": [
        "index.html and styles.css are locked — only script.js may change.",
        "Handle the form's submit event, not the button's click, and prevent the default.",
        "A whitespace-only email counts as blank (trim before you test it).",
        "#formSuccess must stay empty while anything is invalid.",
    ],
    "requirements": [
        "Listen for the form's submit event and call event.preventDefault()",
        "Reject an email that is blank once trimmed, or that has no \"@\", with a message in #emailError",
        "Reject a password shorter than 8 characters with a message in #passwordError",
        "When both fields are valid, clear both error messages and show a confirmation in #formSuccess",
        "Never show the confirmation while a field is still invalid",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": SIGNUP_HTML,
        "styles.css": PRACTICE_CSS,
        "script.js": SIGNUP_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "submit_listener",
            "requirement_index": 0,
            "type": "regex",
            "file": "script.js",
            "pattern": r"addEventListener\(\s*[\"']submit[\"']",
            "label": "Listens for the form's submit event",
            "concept": "form events",
            "hint": "Listening for the button's click misses Enter-key submissions.",
        },
        {
            "id": "prevent_default",
            "requirement_index": 0,
            "type": "js_calls",
            "file": "script.js",
            "callee": "preventDefault",
            "label": "Genuinely calls preventDefault()",
            "concept": "form events",
            "hint": "Without it the browser submits the form and reloads the page.",
        },
        {
            "id": "trims_email",
            "requirement_index": 1,
            "type": "js_calls",
            "file": "script.js",
            "callee": ".trim",
            "label": "Trims the email before validating it",
            "concept": "validation",
            "hint": "\"   \" is not a valid email, but it is not an empty string either.",
        },
        {
            "id": "checks_at_sign",
            "requirement_index": 1,
            "type": "regex",
            "file": "script.js",
            "pattern": r"[\"']@[\"']|includes\(\s*[\"']@|indexOf\(\s*[\"']@|/[^/\n]*@[^/\n]*/",
            "label": "Checks the email contains \"@\"",
            "concept": "validation",
            "hint": "includes(\"@\") is enough here — no need for a full email regex.",
        },
        {
            "id": "password_length",
            "requirement_index": 2,
            "type": "regex",
            "file": "script.js",
            "pattern": r"length\s*(<|>=|<=|>)\s*(8|7)",
            "label": "Enforces the minimum password length",
            "concept": "validation",
            "hint": "password.length < 8 is the rule the requirements state.",
        },
        {
            "id": "validate_real",
            "requirement_index": 1,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "validate",
            "label": "validate has a real implementation",
            "concept": "validation",
            "hint": "Return what is wrong so the handler can render it — the stub returns nothing.",
        },
        {
            "id": "writes_messages",
            "requirement_index": 3,
            "type": "regex",
            "file": "script.js",
            "pattern": r"(textContent|innerText|innerHTML)\s*=",
            "label": "Writes the messages into the page",
            "concept": "DOM updates",
            "hint": "The error paragraphs already exist — fill and clear their text.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(SIGNUP_PRELUDE),
        "assertions": [
            {
                "id": "blocks_the_browser_submit",
                "requirement_index": 0,
                "label": "the submit event is prevented so the page never reloads",
                "concept": "form events",
                "hint": "Call event.preventDefault() first thing in the submit handler.",
                "expression": (
                    "__setup(); await __userMain();"
                    " const submitted = __submit('someone@example.com', 'longenough1');"
                    " if (submitted !== true) return submitted;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectPrevented());"
                ),
            },
            {
                "id": "rejects_bad_email",
                "requirement_indexes": [1, 4],
                "label": "a blank or @-less email is rejected and no success is shown",
                "concept": "validation",
                "hint": "Trim the value, then check it is non-empty and contains \"@\".",
                "expression": (
                    "__setup(); await __userMain();"
                    " let submitted = __submit('   ', 'longenough1');"
                    " if (submitted !== true) return submitted;"
                    " let settled = await __settle(); if (settled !== true) return settled;"
                    " const blank = __all(__ranAtAll(), __expectPrevented(),"
                    " __expectNonEmpty('#emailError'), __expectEmpty('#formSuccess'));"
                    " if (blank !== true) return 'with a whitespace-only email: ' + blank;"
                    " __setup(); await __userMain();"
                    " submitted = __submit('nope-at-example.com', 'longenough1');"
                    " if (submitted !== true) return submitted;"
                    " settled = await __settle(); if (settled !== true) return settled;"
                    " const noAt = __all(__expectNonEmpty('#emailError'), __expectEmpty('#formSuccess'));"
                    " if (noAt !== true) return 'with an email that has no @: ' + noAt;"
                    " return true;"
                ),
            },
            {
                "id": "rejects_short_password",
                "requirement_indexes": [2, 4],
                "label": "a password shorter than 8 characters is rejected and no success is shown",
                "concept": "validation",
                "hint": "Report the password problem in #passwordError, and keep #formSuccess empty.",
                "expression": (
                    "__setup(); await __userMain();"
                    " const submitted = __submit('someone@example.com', 'short');"
                    " if (submitted !== true) return submitted;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectPrevented(),"
                    " __expectNonEmpty('#passwordError'), __expectEmpty('#formSuccess'));"
                ),
            },
            {
                "id": "accepts_valid_input",
                "requirement_index": 3,
                "label": "valid input clears the errors and shows the confirmation",
                "concept": "validation",
                "hint": "On the happy path both error paragraphs must be emptied, not left as they were.",
                "expression": (
                    "__setup(); await __userMain();"
                    " let submitted = __submit('a@b.com', 'short');"
                    " if (submitted !== true) return submitted;"
                    " let settled = await __settle(); if (settled !== true) return settled;"
                    " submitted = __submit('someone@example.com', 'longenough1');"
                    " if (submitted !== true) return submitted;"
                    " settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectNonEmpty('#formSuccess'),"
                    " __expectEmpty('#emailError'), __expectEmpty('#passwordError'));"
                ),
            },
            {
                "id": "both_problems_reported",
                "requirement_indexes": [1, 2],
                "hidden": True,
                "label": "both fields are reported when both are wrong",
                "concept": "validation",
                "hint": "Validate every field on each submit rather than returning after the first problem.",
                "expression": (
                    "__setup(); await __userMain();"
                    " const submitted = __submit('', 'abc');"
                    " if (submitted !== true) return submitted;"
                    " const settled = await __settle(); if (settled !== true) return settled;"
                    " return __all(__ranAtAll(), __expectNonEmpty('#emailError'),"
                    " __expectNonEmpty('#passwordError'), __expectEmpty('#formSuccess'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 8. Promises and async/await — forecast panel
# ---------------------------------------------------------------------------

FORECAST_HTML = _page(
    "Weekly Forecast",
    """    <main class="panel">
      <h1>Weekly forecast</h1>
      <p class="subtitle">Straight from the weather service.</p>
      <div id="forecast"></div>
    </main>
""",
    data_file=False,
)

FORECAST_API = """// Given and locked. The weather service client.
// loadForecast() returns a Promise that resolves — after a real network delay —
// to an array of { day, high, low } objects.
async function loadForecast() {
  const response = await fetch("/api/forecast");
  return response.json();
}
"""

FORECAST_STARTER = """// The JavaScript layer was removed.
// loadForecast() is provided by api.js (locked). It returns a Promise, and the
// network is slow: the panel must never look empty while you wait.

async function showForecast() {
  // TODO
  // 1. put a loading message into #forecast BEFORE you await anything
  // 2. await loadForecast()
  // 3. replace the loading message with one row per day, showing the day
  //    name and its high and low
}

// TODO: call showForecast() so the forecast loads as soon as the page opens.
"""

FORECAST_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const panel = __makeElement('div');
  panel.setAttribute('id', 'forecast');
  panel.parentNode = root;
  root.children.push(panel);
  return root;
}

let __scenario = () => {
  throw new Error('no scenario configured');
};
let __days = [];

//: The grader owns the request, so the learner cannot substitute a
//: pre-resolved promise and skip the asynchronous path. The DOM is snapshotted
//: the moment the request starts, which is what lets the loading state be told
//: apart from the rendered result.
globalThis.loadForecast = async () => {
  __note();
  __requestStarted = true;
  __postRequestWrites = 0;
  __domAtRequest = __regionText('#forecast');
  return __scenario();
};
globalThis.fetchForecast = globalThis.loadForecast;
globalThis.getForecast = globalThis.loadForecast;

function __setup(days, scenario) {
  __days = days;
  __resetDom();
  __scenario = scenario || (async () => {
    await new Promise((resolve) => globalThis.setTimeout(resolve, 5));
    return __days;
  });
}

function __expectDaysRendered() {
  const panel = __el('#forecast');
  if (!panel) return 'the #forecast element is gone from the page';
  if (__postRequestWrites === 0) {
    return (
      'nothing was written to the page after the forecast resolved — the data arrived ' +
      'and was never rendered' +
      __errorSuffix()
    );
  }
  const html = panel.innerHTML + ' ' + panel.textContent;
  for (const day of __days) {
    if (html.indexOf(day.day) === -1) {
      return '"' + day.day + '" is in the forecast but was never rendered' + __errorSuffix();
    }
    if (html.indexOf(String(day.high)) === -1 || html.indexOf(String(day.low)) === -1) {
      return (
        'the high/low for ' + day.day + ' (' + day.high + '/' + day.low + ') is missing ' +
        'from the page' + __errorSuffix()
      );
    }
  }
  return true;
}

const __WEEK = [
  { day: 'Monday', high: 21, low: 12 },
  { day: 'Tuesday', high: 19, low: 11 },
  { day: 'Wednesday', high: 24, low: 14 },
];
"""

FORECAST_MODULE: dict[str, Any] = {
    "id": "js-forecast-async-await",
    "title": "Weekly Forecast — Promises and async/await",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_async",
    "technology": "JavaScript",
    "difficulty": 5,
    "estimated_minutes": 30,
    "summary": "Await a slow weather service and render the result, with a loading state that appears before the request and is gone after it.",
    "problem_statement": (
        "`api.js` gives you `loadForecast()`, which returns a Promise that resolves to an array of "
        "`{ day, high, low }` objects after a real network delay. The `#forecast` panel is empty "
        "and stays empty.\n\n"
        "Write an async function that shows a loading message **before** it awaits, awaits the "
        "forecast, and then replaces the loading message with a row per day. Call it on load. The "
        "grader controls the request and runs your file against different forecasts, including a "
        "slow one."
    ),
    "constraints": [
        "index.html, styles.css and api.js are locked — only script.js may change.",
        "Use async/await rather than nested .then() callbacks.",
        "The loading message must be on the page before the await, and gone once the data is rendered.",
        "Do not fabricate the data: everything rendered comes from what loadForecast() resolved to.",
    ],
    "requirements": [
        "Declare an async function that awaits loadForecast()",
        "Show a loading message inside #forecast before the request starts",
        "Replace the loading message once the forecast resolves — it must not survive",
        "Render each day's name with its high and low from the resolved data",
        "Call the function on load so the forecast appears without any user interaction",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": FORECAST_HTML,
        "styles.css": PRACTICE_CSS,
        "api.js": FORECAST_API,
        "script.js": FORECAST_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "async_fn",
            "requirement_index": 0,
            "type": "js_async_function",
            "file": "script.js",
            "label": "Declares an async function that awaits its request",
            "concept": "async/await",
            "hint": "An async function that never awaits is just a function returning a promise.",
        },
        {
            "id": "calls_loader",
            "requirement_index": 0,
            "type": "js_calls",
            "file": "script.js",
            "callee": "loadForecast",
            "label": "Genuinely calls loadForecast()",
            "concept": "promises",
            "hint": "Mentioning it in a comment does not call it.",
        },
        {
            "id": "loading_sequence",
            "requirement_indexes": [1, 2],
            "type": "js_loading_sequence",
            "file": "script.js",
            "label": "A loading state is written before the request and replaced after it",
            "concept": "loading/error states",
            "hint": "Write the loading markup into #forecast before the await, then overwrite the same element afterwards.",
        },
        {
            "id": "show_real",
            "requirement_index": 3,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "showForecast",
            "label": "showForecast has a real implementation",
            "concept": "async/await",
            "hint": "The body is comments only — await the data and render it.",
        },
        {
            "id": "no_callback_nesting",
            "requirement_index": 0,
            "type": "not_regex",
            "file": "script.js",
            "pattern": r"\.then\([\s\S]{0,120}\.then\(",
            "label": "Avoids chained .then() callbacks",
            "concept": "async/await",
            "hint": "await reads top-to-bottom; that is the point of this exercise.",
        },
        {
            "id": "invoked",
            "requirement_index": 4,
            "type": "regex",
            "file": "script.js",
            "pattern": r"^\s*(await\s+)?showForecast\s*\(|\bshowForecast\s*\(\s*\)\s*;",
            "label": "Calls showForecast() so the page loads itself",
            "concept": "async/await",
            "hint": "A function that is only declared never runs.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(FORECAST_PRELUDE),
        "assertions": [
            {
                "id": "renders_after_await",
                "requirement_indexes": [0, 3, 4],
                "label": "renders every day once the awaited forecast resolves",
                "concept": "async/await",
                "hint": "Render inside the async function after the await, not before it.",
                "expression": (
                    "__setup(__WEEK); await __userMain();"
                    " return __all(__ranAtAll(), __expectDaysRendered());"
                ),
            },
            {
                "id": "loading_before_request",
                "requirement_index": 1,
                "label": "a loading message is on the page when the request starts",
                "concept": "loading/error states",
                "hint": "Write the loading state into #forecast on the line before the await.",
                "expression": (
                    "__setup(__WEEK); await __userMain();"
                    " return __all(__ranAtAll(), __expectLoadingWasShown());"
                ),
            },
            {
                "id": "loading_cleared_after",
                "requirement_index": 2,
                "label": "the loading message is gone once the forecast is rendered",
                "concept": "loading/error states",
                "hint": "Overwrite the loading markup with the rendered rows rather than appending after it.",
                "expression": (
                    "__setup(__WEEK); await __userMain();"
                    " return __all(__ranAtAll(), __expectLoadingCleared('#forecast'),"
                    " __expectDaysRendered());"
                ),
            },
            {
                "id": "waits_for_a_slow_response",
                "requirement_indexes": [0, 3],
                "hidden": True,
                "label": "a slower response is still awaited and rendered, not raced",
                "concept": "promises",
                "hint": "Render only after the promise resolves — code after the await runs when the data is really there.",
                "expression": (
                    "const days = [{ day: 'Friday', high: 30, low: 18 },"
                    " { day: 'Saturday', high: 27, low: 16 }];"
                    " __setup(days, async () => {"
                    "   await new Promise((resolve) => globalThis.setTimeout(resolve, 40));"
                    "   return days; });"
                    " await __userMain();"
                    " return __all(__ranAtAll(), __expectDaysRendered(),"
                    " __expectLoadingCleared('#forecast'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 9. Async error handling with a user-visible error state — orders panel
# ---------------------------------------------------------------------------

ORDERS_HTML = _page(
    "Recent Orders",
    """    <main class="panel">
      <h1>Recent orders</h1>
      <p class="subtitle">Live from the orders service.</p>
      <div id="orders"></div>
    </main>
""",
    data_file=False,
)

ORDERS_API = """// Given and locked. The orders service client.
// loadOrders() resolves to a Response-like object: { ok, status, json() }.
// It REJECTS when the network is unavailable, and resolves with ok === false
// when the service answers with an error status.
async function loadOrders() {
  return fetch("/api/orders");
}
"""

ORDERS_STARTER = """// The JavaScript layer was removed.
// loadOrders() is provided by api.js (locked). It can reject (network down) and
// it can resolve with ok === false (the service returned 4xx/5xx).
// Whatever happens, the user must never be left staring at a spinner.

async function showOrders() {
  // TODO
  // 1. show a loading state in #orders before awaiting
  // 2. await loadOrders() inside try/catch, binding the error: catch (error)
  // 3. treat a non-ok response as a failure BEFORE parsing the body
  // 4. on success: parse the body and render one row per order
  // 5. on any failure: replace the loading state with a visible error message
  //    (give it the "error" class or role="alert") and never let the failure
  //    escape this function
}

// TODO: call showOrders() so the panel loads itself.
"""

ORDERS_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const panel = __makeElement('div');
  panel.setAttribute('id', 'orders');
  panel.parentNode = root;
  root.children.push(panel);
  return root;
}

let __scenario = () => {
  throw new Error('no scenario configured');
};
let __jsonParsed = false;
let __orders = [];

globalThis.loadOrders = async () => {
  __note();
  __requestStarted = true;
  __postRequestWrites = 0;
  __domAtRequest = __regionText('#orders');
  return __scenario();
};
globalThis.fetchOrders = globalThis.loadOrders;
globalThis.fetch = globalThis.loadOrders;

function __okResponse(data) {
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => {
      __jsonParsed = true;
      __note();
      return data;
    },
    text: async () => {
      __jsonParsed = true;
      __note();
      return JSON.stringify(data);
    },
  };
}

function __failResponse(status) {
  return {
    ok: false,
    status: status || 500,
    statusText: 'Server Error',
    json: async () => {
      __jsonParsed = true;
      __note();
      return {};
    },
    text: async () => {
      __jsonParsed = true;
      __note();
      return '';
    },
  };
}

function __setup(scenario, orders) {
  __orders = orders || [];
  __jsonParsed = false;
  __resetDom();
  __scenario = scenario;
}

function __expectOrdersRendered() {
  if (!__jsonParsed) {
    return 'response.json() was never called, so the order data was never read' + __errorSuffix();
  }
  const panel = __el('#orders');
  if (!panel) return 'the #orders element is gone from the page';
  if (__postRequestWrites === 0) {
    return 'the orders arrived but nothing was written to the page' + __errorSuffix();
  }
  const html = panel.innerHTML + ' ' + panel.textContent;
  for (const order of __orders) {
    if (html.indexOf(order.reference) === -1) {
      return 'order ' + order.reference + ' was never rendered' + __errorSuffix();
    }
  }
  return __all(__expectLoadingCleared('#orders'), __noThrow());
}
"""

ORDERS_MODULE: dict[str, Any] = {
    "id": "js-orders-async-error-state",
    "title": "Recent Orders — Async Error Handling with a Visible Error State",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "js_async_error_handling",
    "technology": "JavaScript",
    "difficulty": 6,
    "estimated_minutes": 35,
    "is_remediation": True,
    "remediates_concepts": [
        "async error handling",
        "promise rejection",
        "try/catch",
        "loading states",
        "HTTP status codes",
    ],
    "summary": "The orders panel spins forever when the service is down. Handle rejections and error statuses, and put a real error message on the screen.",
    "problem_statement": (
        "`api.js` gives you `loadOrders()`. It resolves to a Response-like object when the service "
        "answers, **rejects** when the network is unavailable, and resolves with `ok === false` "
        "when the service answers 4xx/5xx. Today the panel shows a spinner forever in both "
        "failure cases.\n\n"
        "Make the panel honest: a loading state before the request, the orders rendered on "
        "success, and a **visible** error message on failure — the spinner must be replaced, not "
        "joined. `console.error` is not a user interface, and an empty panel tells the user "
        "nothing. The failure must never escape your function as an unhandled rejection."
    ),
    "constraints": [
        "index.html, styles.css and api.js are locked — only script.js may change.",
        "The awaited call must be inside try/catch with the error bound: catch (error).",
        "Check response.ok before parsing the body — do not call json() on a failed response.",
        "The error state must be visible in #orders: give it the \"error\" class or role=\"alert\".",
        "The loading state must be gone on both the success and the failure path.",
    ],
    "requirements": [
        "Await loadOrders() inside a try/catch that binds the error",
        "Treat a non-ok response as a failure and handle it before parsing the body",
        "On failure, replace the loading state with a visible error message in #orders",
        "On success, parse the body and render one row per order with its reference",
        "Show a loading state before the request and never leave it on screen afterwards",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": ORDERS_HTML,
        "styles.css": PRACTICE_CSS,
        "api.js": ORDERS_API,
        "script.js": ORDERS_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "async_fn",
            "requirement_index": 0,
            "type": "js_async_function",
            "file": "script.js",
            "label": "Declares an async function that awaits its request",
            "concept": "async/await",
            "hint": "await only works inside an async function.",
        },
        {
            "id": "try_catch",
            "requirement_index": 0,
            "type": "js_try_catch_await",
            "file": "script.js",
            "require_binding": True,
            "label": "The awaited call runs inside try/catch (error)",
            "concept": "try/catch",
            "hint": "The await must be lexically inside the try block, and catch must bind the error.",
        },
        {
            "id": "ok_before_parse",
            "requirement_index": 1,
            "type": "js_ok_before_parse",
            "file": "script.js",
            "label": "Checks response.ok and handles the failure before parsing",
            "concept": "HTTP status codes",
            "hint": "Throw (or handle) the non-ok case above the response.json() call, not below it.",
        },
        {
            "id": "catch_writes_dom",
            "requirement_index": 2,
            "type": "js_catch_handles",
            "file": "script.js",
            "require_dom_write": True,
            "label": "The catch block writes the failure into the page",
            "concept": "promise rejection",
            "hint": "An empty catch, or one that only logs, leaves the user with a spinner.",
        },
        {
            "id": "error_ui",
            "requirement_index": 2,
            "type": "js_error_feedback",
            "file": "script.js",
            "label": "Renders an error state in the DOM on failure",
            "concept": "loading/error states",
            "hint": "console.error is invisible to the user — write the message into #orders.",
        },
        {
            "id": "loading_sequence",
            "requirement_index": 4,
            "type": "js_loading_sequence",
            "file": "script.js",
            "label": "A loading state is written before the request and cleared after it",
            "concept": "loading/error states",
            "hint": "Write into #orders before the await, then overwrite that same element afterwards.",
        },
        {
            "id": "renders_orders",
            "requirement_index": 3,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "showOrders",
            "label": "showOrders has a real implementation",
            "concept": "async/await",
            "hint": "The body is comments only. Parse the body and render the rows.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(ORDERS_PRELUDE),
        "assertions": [
            {
                "id": "success_renders",
                "requirement_indexes": [3, 4],
                "label": "a successful response renders the orders and clears the loading state",
                "concept": "async/await",
                "hint": "Parse the body after the status check, then replace the loading markup with the rows.",
                "expression": (
                    "const orders = [{ reference: 'ORD-1041', total: '32.00' },"
                    " { reference: 'ORD-1042', total: '18.50' }];"
                    " __setup(async () => __okResponse(orders), orders);"
                    " await __userMain();"
                    " return __all(__ranAtAll(), __expectOrdersRendered());"
                ),
            },
            {
                "id": "rejection_shows_error",
                "requirement_indexes": [0, 2],
                "label": "a rejected request never escapes and the page shows an error",
                "concept": "promise rejection",
                "hint": "await on a rejected promise throws — catch it and render a visible error state.",
                "expression": (
                    "__setup(() => Promise.reject(new Error('network down')));"
                    " await __userMain();"
                    " return __all(__ranAtAll(), __expectErrorState('#orders'),"
                    " __expectLoadingCleared('#orders'));"
                ),
            },
            {
                "id": "non_ok_not_parsed",
                "requirement_indexes": [1, 2],
                "label": "a 500 response is treated as an error and the body is never parsed",
                "concept": "HTTP status codes",
                "hint": "Check response.ok first; json() on a failed response parses an error payload as data.",
                "expression": (
                    "__setup(async () => __failResponse(500));"
                    " await __userMain();"
                    " if (__jsonParsed) return 'response.json() was called even though the status was 500"
                    " — check response.ok before parsing';"
                    " return __all(__ranAtAll(), __expectErrorState('#orders'));"
                ),
            },
            {
                "id": "loading_shown_first",
                "requirement_index": 4,
                "label": "a loading state is on the page when the request starts",
                "concept": "loading/error states",
                "hint": "Paint the loading state before the await, otherwise the panel is blank while waiting.",
                "expression": (
                    "const orders = [{ reference: 'ORD-2001', total: '9.99' }];"
                    " __setup(async () => __okResponse(orders), orders);"
                    " await __userMain();"
                    " return __all(__ranAtAll(), __expectLoadingWasShown());"
                ),
            },
            {
                "id": "failure_never_throws",
                "requirement_index": 0,
                "hidden": True,
                "label": "a synchronous throw from the client is contained too",
                "concept": "async error handling",
                "hint": "The call itself can throw before it ever returns a promise — keep it inside the try block.",
                "expression": (
                    "__setup(() => { throw new Error('client exploded'); });"
                    " await __userMain();"
                    " if (__runtimeErrors.length) return 'the failure escaped your function: ' +"
                    " __runtimeErrors.join('; ');"
                    " return __expectErrorState('#orders');"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 10. fetch and API rendering with three states — team directory
# ---------------------------------------------------------------------------

DIRECTORY_HTML = _page(
    "Team Directory",
    """    <main class="panel">
      <h1>Team directory</h1>
      <p class="subtitle">Everyone in the workspace.</p>
      <div id="people"></div>
    </main>
""",
    data_file=False,
)

DIRECTORY_STARTER = """// The JavaScript layer was removed.
// There is no client library here: call fetch("/api/people") yourself.
// The endpoint can be slow, can answer 404/500, and can fail outright — the
// panel has to say something sensible in all three cases.

async function loadPeople() {
  // TODO
  // 1. render a loading state into #people before awaiting
  // 2. await fetch("/api/people") inside try/catch (error)
  // 3. if the response is not ok, fail BEFORE parsing the body
  // 4. parse the JSON and render one row per person (name and role)
  // 5. on any failure, replace the loading state with a visible error message
  //    that invites the user to try again
}

// TODO: call loadPeople() on load.
"""

DIRECTORY_PRELUDE = r"""
function __buildDom() {
  const root = __makeElement('main');
  root.setAttribute('class', 'panel');
  const panel = __makeElement('div');
  panel.setAttribute('id', 'people');
  panel.parentNode = root;
  root.children.push(panel);
  return root;
}

let __scenario = () => {
  throw new Error('no scenario configured');
};
let __jsonParsed = false;
let __people = [];

//: fetch itself is owned by the grader, so a hard-coded
//: `Promise.resolve({ ok: true })` can never satisfy the failure scenarios.
globalThis.fetch = async (..._args) => {
  __note();
  __requestStarted = true;
  __postRequestWrites = 0;
  __domAtRequest = __regionText('#people');
  return __scenario();
};

function __okResponse(data) {
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => {
      __jsonParsed = true;
      __note();
      return data;
    },
    text: async () => {
      __jsonParsed = true;
      __note();
      return JSON.stringify(data);
    },
  };
}

function __failResponse(status) {
  return {
    ok: false,
    status: status || 404,
    statusText: 'Not Found',
    json: async () => {
      __jsonParsed = true;
      __note();
      return { message: 'not found' };
    },
    text: async () => {
      __jsonParsed = true;
      __note();
      return '';
    },
  };
}

function __setup(scenario, people) {
  __people = people || [];
  __jsonParsed = false;
  __resetDom();
  __scenario = scenario;
}

function __expectPeopleRendered() {
  if (!__jsonParsed) {
    return 'the response body was never parsed, so the directory data was never read' + __errorSuffix();
  }
  const panel = __el('#people');
  if (!panel) return 'the #people element is gone from the page';
  if (__postRequestWrites === 0) {
    return 'the response arrived but nothing was written to the page' + __errorSuffix();
  }
  const html = panel.innerHTML + ' ' + panel.textContent;
  for (const person of __people) {
    if (html.indexOf(person.name) === -1) {
      return '"' + person.name + '" came back from the API but was never rendered' + __errorSuffix();
    }
    if (html.indexOf(person.role) === -1) {
      return 'the role "' + person.role + '" is missing from the rendered row' + __errorSuffix();
    }
  }
  return __all(__expectLoadingCleared('#people'), __noThrow());
}

const __TEAM = [
  { name: 'Ada Lovelace', role: 'Engineering' },
  { name: 'Grace Hopper', role: 'Compilers' },
];
"""

DIRECTORY_MODULE: dict[str, Any] = {
    "id": "js-directory-fetch-states",
    "title": "Team Directory — fetch with Loading, Success and Failure States",
    "kind": "web",
    "practice_layer": "javascript",
    "skill_id": "api_integration",
    "technology": "JavaScript",
    "difficulty": 6,
    "estimated_minutes": 35,
    "summary": "Call the API with fetch and render all three states honestly: loading while it waits, rows on success, a retry-able message when it fails.",
    "problem_statement": (
        "The directory panel is empty and there is no client library to lean on: call "
        "`fetch(\"/api/people\")` yourself. The endpoint is slow, sometimes answers 404 or 500, and "
        "sometimes fails outright.\n\n"
        "Render all three states: a loading state before the request, one row per person "
        "(name and role) from the parsed JSON on success, and a visible error message inviting a "
        "retry on failure. Remember that `fetch` does **not** reject on a 404 — an unchecked "
        "`response.json()` will happily parse the error payload and render nonsense."
    ),
    "constraints": [
        "index.html and styles.css are locked — only script.js may change.",
        "Use fetch directly; the grader owns the network, so hard-coded responses will fail.",
        "Check response.ok before parsing: fetch resolves for 404 and 500.",
        "Both the success and the failure path must clear the loading state.",
        "The error message must be visible in #people and mention that the user can try again.",
    ],
    "requirements": [
        "Call fetch(\"/api/people\") from inside an async function and await it",
        "Show a loading state in #people before the request and clear it once the request settles",
        "Treat a non-ok response as a failure and do not parse its body",
        "Render one row per person from the parsed JSON, showing the name and role",
        "On failure render a visible error message in #people that invites the user to try again",
    ],
    "editable_files": ["script.js"],
    "entry_file": "index.html",
    "files": {
        "index.html": DIRECTORY_HTML,
        "styles.css": PRACTICE_CSS,
        "script.js": DIRECTORY_STARTER,
    },
    "checks": [
        _syntax_check(),
        {
            "id": "calls_fetch",
            "requirement_index": 0,
            "type": "js_calls",
            "file": "script.js",
            "callee": "fetch",
            "label": "Genuinely calls fetch",
            "concept": "fetch",
            "hint": "The word \"fetch\" in a comment or a string is not a call.",
        },
        {
            "id": "async_fn",
            "requirement_index": 0,
            "type": "js_async_function",
            "file": "script.js",
            "label": "Declares an async function that awaits its request",
            "concept": "async/await",
            "hint": "await fetch(...) has to live inside an async function.",
        },
        {
            "id": "loading_sequence",
            "requirement_index": 1,
            "type": "js_loading_sequence",
            "file": "script.js",
            "label": "A loading state is written before the request and cleared after it",
            "concept": "loading/error states",
            "hint": "Write into #people before the await, then overwrite that element when the request settles.",
        },
        {
            "id": "ok_before_parse",
            "requirement_index": 2,
            "type": "js_ok_before_parse",
            "file": "script.js",
            "label": "Checks response.ok and handles it before parsing the body",
            "concept": "HTTP status codes",
            "hint": "if (!response.ok) throw new Error(...) above the response.json() call.",
        },
        {
            "id": "catch_writes_dom",
            "requirement_index": 4,
            "type": "js_catch_handles",
            "file": "script.js",
            "require_dom_write": True,
            "label": "The catch block writes the failure into the page",
            "concept": "promise rejection",
            "hint": "Logging the error leaves the panel showing a spinner forever.",
        },
        {
            "id": "error_ui",
            "requirement_index": 4,
            "type": "js_error_feedback",
            "file": "script.js",
            "label": "Renders an error state in the DOM on failure",
            "concept": "loading/error states",
            "hint": "Give the message the \"error\" class or role=\"alert\" so it reads as an error.",
        },
        {
            "id": "render_real",
            "requirement_index": 3,
            "type": "js_not_trivial",
            "file": "script.js",
            "name": "loadPeople",
            "label": "loadPeople has a real implementation",
            "concept": "fetch",
            "hint": "The body is still comments — request, check, parse, render.",
        },
        _no_dead_code_check(),
    ],
    "behaviour": {
        "wrap_as": "__userMain",
        "prelude": _prelude(DIRECTORY_PRELUDE),
        "assertions": [
            {
                "id": "success_renders_rows",
                "requirement_indexes": [0, 3],
                "label": "a successful response renders every person with their role",
                "concept": "fetch",
                "hint": "Parse the JSON after the status check and render a row per person.",
                "expression": (
                    "__setup(async () => __okResponse(__TEAM), __TEAM); await __userMain();"
                    " return __all(__ranAtAll(), __expectPeopleRendered());"
                ),
            },
            {
                "id": "loading_state_lifecycle",
                "requirement_index": 1,
                "label": "the loading state appears before the request and is gone afterwards",
                "concept": "loading/error states",
                "hint": "Paint it before the await and overwrite it once you have a result.",
                "expression": (
                    "__setup(async () => {"
                    "   await new Promise((resolve) => globalThis.setTimeout(resolve, 20));"
                    "   return __okResponse(__TEAM); }, __TEAM);"
                    " await __userMain();"
                    " return __all(__ranAtAll(), __expectLoadingWasShown(),"
                    " __expectLoadingCleared('#people'), __expectPeopleRendered());"
                ),
            },
            {
                "id": "not_found_is_an_error",
                "requirement_indexes": [2, 4],
                "label": "a 404 is treated as an error, the body is not parsed, and the page says so",
                "concept": "HTTP status codes",
                "hint": "fetch resolves for 404: only response.ok tells you it failed.",
                "expression": (
                    "__setup(async () => __failResponse(404)); await __userMain();"
                    " if (__jsonParsed) return 'response.json() was called on a 404 — check response.ok"
                    " before parsing the body';"
                    " return __all(__ranAtAll(), __expectErrorState('#people'),"
                    " __expectLoadingCleared('#people'));"
                ),
            },
            {
                "id": "network_failure_is_visible",
                "requirement_index": 4,
                "label": "a rejected request renders a visible, retry-able error message",
                "concept": "promise rejection",
                "hint": "Catch the rejection and replace the loading markup with a message mentioning a retry.",
                "expression": (
                    "__setup(() => Promise.reject(new Error('connection refused')));"
                    " await __userMain();"
                    " const state = __expectErrorState('#people'); if (state !== true) return state;"
                    " const text = __regionText('#people');"
                    " if (!/\\b(try\\s+again|retry|reload|refresh)\\b/i.test(text))"
                    "   return 'the error message never tells the user what to do — invite them to try again';"
                    " return __all(__ranAtAll(), __expectLoadingCleared('#people'));"
                ),
            },
            {
                "id": "server_error_is_an_error",
                "requirement_indexes": [2, 4],
                "hidden": True,
                "label": "a 500 is handled the same way as a 404",
                "concept": "HTTP status codes",
                "hint": "Branch on response.ok rather than on a specific status code.",
                "expression": (
                    "__setup(async () => __failResponse(500)); await __userMain();"
                    " if (__jsonParsed) return 'response.json() was called on a 500 response';"
                    " return __all(__ranAtAll(), __expectErrorState('#people'));"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Reference solutions.
#
# These never reach the learner: `practice_service.module_detail` builds the
# served payload from `files` and drops `solution_files`. They exist so
# `test_every_web_module_solution_passes_its_own_checks` grades each module's
# own spec against a solution that is known to satisfy it — a check that a
# tightened (or mis-typed) check would otherwise break silently.
# ---------------------------------------------------------------------------

ORDER_SUMMARY_SOLUTION = """function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatMoney(amount) {
  return toNumber(amount).toFixed(2);
}

function renderOrderSummary(order) {
  const items = order.items || [];
  let count = 0;
  let subtotal = 0;
  for (const item of items) {
    count += toNumber(item.quantity);
    subtotal += toNumber(item.price) * toNumber(item.quantity);
  }
  const shipping = toNumber(order.shipping);

  document.getElementById("itemCount").textContent = `${count} items`;
  document.getElementById("subtotal").textContent = formatMoney(subtotal);
  document.getElementById("shipping").textContent = formatMoney(shipping);
  document.getElementById("total").textContent = formatMoney(subtotal + shipping);

  const totals = document.getElementById("totals");
  const note = document.getElementById("emptyNote");
  if (items.length === 0) {
    note.textContent = "Your basket is empty.";
    totals.classList.add("hidden");
  } else {
    note.textContent = "";
    totals.classList.remove("hidden");
  }
}

renderOrderSummary(ORDER);
"""

COUNTERS_SOLUTION = """function createCounter(section) {
  let seatCount = 0;
  const step = Number(section.dataset.step) || 1;
  const output = section.querySelector('[data-role="value"]');

  function paint() {
    output.textContent = String(seatCount);
  }

  return {
    increment() {
      seatCount += step;
      paint();
    },
    reset() {
      seatCount = 0;
      paint();
    },
  };
}

document.querySelectorAll(".counter").forEach((section) => {
  const counter = createCounter(section);
  section.querySelector('[data-role="increment"]').addEventListener("click", counter.increment);
  section.querySelector('[data-role="reset"]').addEventListener("click", counter.reset);
});
"""

INVENTORY_SOLUTION = """function inStock(products) {
  return products.filter((product) => product.stock > 0);
}

function stockValue(products) {
  return products.reduce((sum, product) => sum + product.price * product.stock, 0);
}

function renderInventory(products) {
  const list = document.getElementById("productList");
  list.innerHTML = inStock(products)
    .map(
      (product) =>
        `<li class="product"><span>${product.name}</span><span>$${product.price.toFixed(2)}</span></li>`
    )
    .join("");

  document.getElementById("stockValue").textContent = stockValue(products).toFixed(2);
  document.getElementById("outOfStock").textContent = String(
    products.filter((product) => product.stock <= 0).length
  );
}

renderInventory(PRODUCTS);
"""

SETTINGS_SOLUTION = """function mergeSettings(defaults, overrides) {
  return { ...defaults, ...overrides };
}

function renderSettings(settings) {
  const { theme, fontSize, notifications, language } = settings;
  document.getElementById("theme").textContent = theme;
  document.getElementById("fontSize").textContent = fontSize;
  document.getElementById("notifications").textContent = notifications;
  document.getElementById("language").textContent = language;
}

renderSettings(mergeSettings(DEFAULT_SETTINGS, USER_SETTINGS));
"""

TASKBOARD_SOLUTION = """function renderTasks(tasks) {
  const list = document.getElementById("taskList");
  list.innerHTML = tasks
    .map((task) => `<li class="task ${task.status}">${task.title}</li>`)
    .join("");

  document.getElementById("taskCount").textContent = `${tasks.length} tasks`;
  document.getElementById("emptyState").textContent =
    tasks.length === 0 ? "Nothing planned for this sprint yet." : "";
}

renderTasks(TASKS);
"""

INBOX_SOLUTION = """const messageList = document.getElementById("messageList");

function renderMessages(messages) {
  messageList.innerHTML = messages
    .map(
      (message) =>
        `<li class="message" data-id="${message.id}">${message.subject}</li>`
    )
    .join("");
}

function updateUnreadCount() {
  const rows = messageList.querySelectorAll(".message");
  let unread = 0;
  rows.forEach((row) => {
    if (!row.classList.contains("read")) {
      unread += 1;
    }
  });
  document.getElementById("unreadCount").textContent = `${unread} unread`;
}

renderMessages(MESSAGES);
updateUnreadCount();

messageList.addEventListener("click", (event) => {
  const message = event.target.closest(".message");
  if (!message) {
    return;
  }
  message.classList.add("read");
  updateUnreadCount();
});
"""

SIGNUP_SOLUTION = """function validate(email, password) {
  const problems = {};
  const trimmed = email.trim();

  if (!trimmed) {
    problems.email = "Enter your email address.";
  } else if (!trimmed.includes("@")) {
    problems.email = "That address is missing an @.";
  }

  if (password.length < 8) {
    problems.password = "Use at least 8 characters.";
  }

  return problems;
}

document.getElementById("signupForm").addEventListener("submit", (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const problems = validate(email, password);

  document.getElementById("emailError").textContent = problems.email || "";
  document.getElementById("passwordError").textContent = problems.password || "";
  document.getElementById("formSuccess").textContent =
    Object.keys(problems).length === 0 ? "Account created. Check your inbox." : "";
});
"""

FORECAST_SOLUTION = """async function showForecast() {
  const panel = document.getElementById("forecast");
  panel.innerHTML = `<p class="loading">Loading the forecast…</p>`;

  const days = await loadForecast();

  panel.innerHTML = days
    .map(
      (day) =>
        `<div class="row"><span>${day.day}</span><span>${day.high} / ${day.low}</span></div>`
    )
    .join("");
}

showForecast();
"""

ORDERS_SOLUTION = """async function showOrders() {
  const panel = document.getElementById("orders");
  panel.innerHTML = `<p class="loading">Loading your orders…</p>`;

  try {
    const response = await loadOrders();

    if (!response.ok) {
      throw new Error(`the service answered ${response.status}`);
    }

    const orders = await response.json();

    panel.innerHTML = orders
      .map(
        (order) =>
          `<div class="row"><span>${order.reference}</span><span>${order.total}</span></div>`
      )
      .join("");
  } catch (error) {
    panel.innerHTML = `<p class="error" role="alert">We could not reach the orders service (${error.message}). Please try again.</p>`;
  }
}

showOrders();
"""

DIRECTORY_SOLUTION = """async function loadPeople() {
  const panel = document.getElementById("people");
  panel.innerHTML = `<p class="loading">Loading the directory…</p>`;

  try {
    const response = await fetch("/api/people");

    if (!response.ok) {
      throw new Error(`the directory answered ${response.status}`);
    }

    const people = await response.json();

    panel.innerHTML = people
      .map(
        (person) =>
          `<div class="row"><span>${person.name}</span><span>${person.role}</span></div>`
      )
      .join("");
  } catch (error) {
    panel.innerHTML = `<p class="error" role="alert">We could not load the directory (${error.message}). Please try again.</p>`;
  }
}

loadPeople();
"""

ORDER_SUMMARY_MODULE["solution_files"] = {"script.js": ORDER_SUMMARY_SOLUTION}
COUNTERS_MODULE["solution_files"] = {"script.js": COUNTERS_SOLUTION}
INVENTORY_MODULE["solution_files"] = {"script.js": INVENTORY_SOLUTION}
SETTINGS_MODULE["solution_files"] = {"script.js": SETTINGS_SOLUTION}
TASKBOARD_MODULE["solution_files"] = {"script.js": TASKBOARD_SOLUTION}
INBOX_MODULE["solution_files"] = {"script.js": INBOX_SOLUTION}
SIGNUP_MODULE["solution_files"] = {"script.js": SIGNUP_SOLUTION}
FORECAST_MODULE["solution_files"] = {"script.js": FORECAST_SOLUTION}
ORDERS_MODULE["solution_files"] = {"script.js": ORDERS_SOLUTION}
DIRECTORY_MODULE["solution_files"] = {"script.js": DIRECTORY_SOLUTION}


JS_MODULES: list[dict[str, Any]] = [
    ORDER_SUMMARY_MODULE,
    COUNTERS_MODULE,
    INVENTORY_MODULE,
    SETTINGS_MODULE,
    TASKBOARD_MODULE,
    INBOX_MODULE,
    SIGNUP_MODULE,
    FORECAST_MODULE,
    ORDERS_MODULE,
    DIRECTORY_MODULE,
]
