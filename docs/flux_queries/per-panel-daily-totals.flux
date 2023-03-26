zero_pad = (v) => {
  result = if int(v) < 10 then
    "0${v}"
  else
    "${v}"

  return result
}

from(bucket: "low_rate")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["source"] == "power-meter")
  |> filter(fn: (r) => r["measurement-type"] == "inverter")
  |> filter(fn: (r) => r["_field"] == "Wh")
  // Panels are tagged with "row" and "col". Rather than labeling them by their
  // serial number, use row/column to label them as "R##-C##"
  |> map(fn: (r) => ({r with pos: "R" + zero_pad(v: r.row) + "-C" + zero_pad(v: r.col)}))
  |> keep(columns: ["_time", "_value", "pos"])
  |> group(columns: ["pos"])
  |> yield(name: "total")
