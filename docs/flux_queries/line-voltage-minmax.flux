DOWNSAMPLE_BY = 20
WINDOW_DURATION = duration(v: int(v: v.windowPeriod) * DOWNSAMPLE_BY)
TIME_SHIFT = duration(v: - int(v: v.windowPeriod) * DOWNSAMPLE_BY / 2)

// Min voltage over the window
from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "net")
  |> filter(fn: (r) => r["_field"] == "V_rms")
  // Use a lower resolution window
  |> aggregateWindow(every: WINDOW_DURATION, fn: min, createEmpty: false)
  // shift back in time to 'center' the downsampled points
  |> timeShift(duration: TIME_SHIFT)
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
  |> aggregateWindow(every: WINDOW_DURATION, fn: max, createEmpty: false)
  // shift back in time to 'center' the downsampled points
  |> timeShift(duration: TIME_SHIFT)
  // use the max of the two line voltages
  |> group(columns: ["_time"], mode:"by")
  |> max(column: "_value")
  |> map(fn: (r) => ({r with name: "max"}))
  |> group(columns: ["name"])
  |> keep(columns: ["_value", "_time", "name"])
  |> yield(name: "max")
