#!/usr/bin/env node

// In development, ts-node or dist entrypoint can be executed
try {
  require('../dist/index.js');
} catch (e) {
  // If not compiled yet, invoke ts-node in development
  require('ts-node/register');
  require('../src/index.ts');
}
