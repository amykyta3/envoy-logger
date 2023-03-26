// Min voltage over the window
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "net")
  |> filter(fn: (r) => r["_field"] == "V_rms")
  // Use a lower resolution window
  |> aggregateWindow(every: duration(v: int(v: v.windowPeriod) * 10), fn: min, createEmpty: false)
  // use the min of the two line voltages
  |> group(columns: ["_time"], mode:"by")
  |> min(column: "_value")
  |> map(fn: (r) => ({r with name: "min"}))
  |> group(columns: ["name"])
  |> keep(columns: ["_value", "_time", "name"])
  |> yield(name: "min")

// Max voltage over the window
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "net")
  |> filter(fn: (r) => r["_field"] == "V_rms")
  // Use a lower resolution window
  |> aggregateWindow(every: duration(v: int(v: v.windowPeriod) * 10), fn: max, createEmpty: false)
  // use the max of the two line voltages
  |> group(columns: ["_time"], mode:"by")
  |> max(column: "_value")
  |> map(fn: (r) => ({r with name: "max"}))
  |> group(columns: ["name"])
  |> keep(columns: ["_value", "_time", "name"])
  |> yield(name: "max")
