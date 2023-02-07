Enphase Envoy data logging service
==================================

Log your solar production locally and feed it into an InfluxDB instance.

This Python-based logging application handles the following:
* Automatically fetch the Envoy authentication token from enphaseenergy.com
    * Enphase has this idiotic token-based authentication method that makes it
      impossible to operate completely offline. This application will fetch a
      new token automatically, and refresh it as-needed upon expiration.
* Authenticate a session with your local Envoy hardware
* Scrape solar production data:
    * Per-phase production, consumption, and net
    * Per-phase voltage, phase angle, etc.
    * Per-panel production
* Push samples to an InfluxDB database
