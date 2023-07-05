zero_pad = (v) => {
  result = if int(v) < 10 then
    "0${v}"
  else
    "${v}"

  return result
}

from(bucket: "high_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "inverter")
  |> filter(fn: (r) => r["_field"] == "P")
  // make sure the "row" and "col" tags exist
  |> filter(fn: (r) => exists r.row and exists r.col)
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  // Panels are tagged with "row" and "col". Rather than labeling them by their
  // serial number, use row/column to label them as "R##-C##"
  |> map(fn: (r) => ({r with pos: "R" + zero_pad(v: r.row) + "-C" + zero_pad(v: r.col)}))
  |> keep(columns: ["_value", "_time", "pos"])
  |> group(columns: ["pos"])
  |> yield(name: "mean")
