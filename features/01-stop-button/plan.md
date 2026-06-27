# Stop Button

Add a Stop button to cancel a running benchmark mid-flight.

## Changes
- `dns_benchmark.py`: add `stop_btn` QPushButton next to Run
- Wire to `worker.stop()` on click
- Toggle Stop visible / Run disabled during run; restore on completion or stop
