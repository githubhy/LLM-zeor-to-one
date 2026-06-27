Report only the background task count.

Call the `TaskList` tool exactly once. Respond with a single integer on its own line — nothing else.

- `TaskList` returns "No tasks found" → respond `0`
- `TaskList` returns N tasks → respond `N`

No prose, no formatting, no explanation, no trailing punctuation. Do not call any other tool. Do not schedule anything — for recurring polling, the user composes with `/loop` (e.g. `/loop 30m /bg`).
