"use strict";

const fs = require("fs");
const {createInstrumenter} = require("istanbul-lib-instrument");

if (process.argv.length < 3) {
  console.error("usage: node instrument_js.cjs <file> [file ...]");
  process.exit(2);
}

for (const file of process.argv.slice(2)) {
  const source = fs.readFileSync(file, "utf8");
  const instrumenter = createInstrumenter({
    coverageVariable: "__coverage__",
    preserveComments: true,
    compact: false,
    esModules: file.endsWith(".mjs"),
  });
  const instrumented = instrumenter.instrumentSync(source, file);
  fs.writeFileSync(file, instrumented, "utf8");
}
