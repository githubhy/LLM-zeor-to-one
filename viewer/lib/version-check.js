// Version-check helpers — pure; Node + browser. UMD.
// shouldNudgeReload(current, lastSeen): true iff both truthy and different.
// nextLastSeen(current, lastSeen): current if truthy, else lastSeen.
(function (root) {
  'use strict';

  function shouldNudgeReload(current, lastSeen) {
    return !!(current && lastSeen && current !== lastSeen);
  }

  function nextLastSeen(current, lastSeen) {
    return current || lastSeen;
  }

  const api = { shouldNudgeReload, nextLastSeen };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) { root.shouldNudgeReload = shouldNudgeReload; root.nextLastSeen = nextLastSeen; }
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : null));
