// Extension entry point.
//
// This is currently an empty shell: it only registers the extension so it can be
// installed and activated, and intentionally contributes no functionality yet.
'use strict';

/**
 * @param {import('vscode').ExtensionContext} context
 */
function activate(context) {
  // No features yet.
}

function deactivate() {
  // Nothing to clean up.
}

module.exports = { activate, deactivate };
