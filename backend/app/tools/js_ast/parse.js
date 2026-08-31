#!/usr/bin/env node
"use strict";

// Reads JavaScript source on stdin, writes a single JSON line on stdout:
//   {"valid": true,  "ast": {...}, "sourceType": "module"|"script"}
//   {"valid": false, "error": {"message": ..., "line": ..., "column": ...}}
// Never throws: a non-zero exit or unparseable stdout is treated as a tooling
// failure by the caller, which fails the check closed.
//
// Pass --jsx to accept JSX syntax (used for .jsx/.tsx-free React files).

const acorn = require("acorn");
const jsx = require("acorn-jsx");

const Parser = process.argv.includes("--jsx") ? acorn.Parser.extend(jsx()) : acorn.Parser;

const OPTIONS = {
  ecmaVersion: 2022,
  locations: true,
  allowReturnOutsideFunction: true,
  allowHashBang: true,
};

function read() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
  });
}

function parse(source) {
  // Module first so `import` and top-level `await` parse; script fallback keeps
  // `return` at top level and other non-module sources working.
  let moduleError;
  try {
    return {
      valid: true,
      sourceType: "module",
      ast: Parser.parse(source, {
        ...OPTIONS,
        sourceType: "module",
        allowAwaitOutsideFunction: true,
      }),
    };
  } catch (error) {
    moduleError = error;
  }
  try {
    return {
      valid: true,
      sourceType: "script",
      ast: Parser.parse(source, { ...OPTIONS, sourceType: "script" }),
    };
  } catch (error) {
    // Report the module error: it is the more permissive grammar, so its
    // message is the one that describes genuinely invalid syntax.
    const reported = moduleError || error;
    return {
      valid: false,
      error: {
        message: String((reported && reported.message) || reported),
        line: (reported && reported.loc && reported.loc.line) || null,
        column: (reported && reported.loc && reported.loc.column) || null,
      },
    };
  }
}

read().then((source) => {
  let payload;
  try {
    payload = parse(source);
  } catch (error) {
    payload = {
      valid: false,
      error: { message: String((error && error.message) || error), line: null, column: null },
    };
  }
  process.stdout.write(JSON.stringify(payload));
});
