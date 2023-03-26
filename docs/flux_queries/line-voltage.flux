// Per-phase line voltage plots
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "net")
  |> filter(fn: (r) => r["_field"] == "V_rms")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> keep(columns: ["_value", "_time", "line-idx"])
  |> yield(name: "mean")
