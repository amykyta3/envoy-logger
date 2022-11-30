// Plot the sum of consumption-line0 + consumption-line1
// Both share the same tag of: measurement-type = consumption
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "consumption")
  |> filter(fn: (r) => r["_field"] == "P")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
//group by time to isolate the values you want to sum togehter
  |> group(columns: ["_time"], mode:"by")
  |> sum(column: "_value")
  |> group()
  |> yield()
