// Calculate power phase angle for each line
import "math"
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "consumption")
  |> filter(fn: (r) => r["_field"] == "P" or r["_field"] == "Q")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> map(fn: (r) => ({r with _value: math.atan(x: r.Q / r.P) * 180.0 / 3.14159 }))
  |> keep(columns: ["_value", "_time", "line-idx"])
  |> yield(name: "mean")
