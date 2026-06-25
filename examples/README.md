# Examples

## todo.py
A port of the [TodoMVC](https://todomvc.com) [web components](https://todomvc.com/examples/web-components) example, matching the look, feel and feature set but structurally refactored to be simpler and more Pythonic.

```bash
pyjs todo:main --ssr server_render --ssr-args '[["task one", "task two"]]' --css todo.css --serve
```

## pegasus_dashboard/
A larger, multi-language example: Python crunches threat-intel data (MITRE ATT&CK + CISA KEV) into a JSON report, `pyjs` transpiles a dashboard UI written in Python into real JavaScript/CSS, and Node.js serves the resulting static site (and bridges `pyjs` to the real Tailwind CLI). See `pegasus_dashboard/README.md` for full setup steps.
