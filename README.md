# jupytertracker

Track Jupyter notebook cell executions and export a clean, ordered Python script — exactly what ran, in the order it ran.

## The problem

Data scientists run cells out of order, modify and re-run cells, and produce notebooks that can't be replayed. `jupytertracker` records every execution and exports an honest log:

- Cell modified and re-run twice? Both versions appear, in order.
- Intentionally tested two hyperparameter settings? Both runs are captured.

## Install

```bash
pip install jupytertracker
```

## Usage

Add one line at the top of your notebook:

```python
import jupytertracker
jupytertracker.start()
```

When you're done, export:

```python
jupytertracker.export_script("my_analysis.py")
```

The output is a `.py` file with every cell execution in order, one block per run:

```python
# execution 1
x = load_data("train.csv")

# execution 2
model = train(x, lr=0.01)

# execution 3
evaluate(model)

# execution 4 (re-run)
# Cell was modified before this run
model = train(x, lr=0.1)

# execution 5 (re-run)
evaluate(model)
```

## API

```python
jupytertracker.start(ip=None)        # start tracking; idempotent
jupytertracker.stop()                # stop tracking
jupytertracker.export_script(path)   # write execution log to .py file
jupytertracker.clear()               # clear the log without stopping
jupytertracker.get_log()             # return list of ExecutionRecord
```

## Notes

- **Kernel restart** resets tracking automatically (Python state is cleared). Call `export_script()` before restarting if you want to preserve the session.
- The exported script is an **execution record**, not a guaranteed reproducible script. Cells that depend on intermediate kernel state may not run top-to-bottom without error. This is v1 — artifact-aware deduplication is planned for v2.
- Magic commands (`%matplotlib inline`, `!pip install ...`) are included with a comment noting they require a Jupyter environment.

## Roadmap

- **v2:** `mode='dedup'` — deduplicate to the last version of each cell, ordered by last execution. For "clean up my notebook" workflows.
- **v3:** `wpr_` annotation pattern — functions prefixed with `wpr_` have their outputs collected for automated whitepaper generation via an LLM.
