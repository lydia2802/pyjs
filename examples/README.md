# Examples

## todo.py
A port of the [TodoMVC](https://todomvc.com) [web components](https://todomvc.com/examples/web-components) example, matching the look, feel and feature set but structurally refactored to be simpler and more Pythonic.

```bash
pyjs todo:main --ssr server_render --ssr-args '[["task one", "task two"]]' --css todo.css --serve
```

## pegasus_attck_analyzer/
A standalone Python CLI (no transpilation) that reads MITRE ATT&CK / CISA KEV data files and writes a JSON summary report. Included as a plain Python reference example, not a `pyjs` transpilation target.

```bash
cd examples/pegasus_attck_analyzer
pip install -r requirements.txt
python3 main.py
```
