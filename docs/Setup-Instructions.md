# Set-up Instructions

This is not intended to be an exhaustive guide, but rather provide some
additional details for you to know how things fit together. This assumes you have
a basic understanding of Grafana, InfluxDB, and general scripting. There are
plenty of great tutorials for all of these should you need additional help.

## 1. Set up an InfluxDB instance
This is where your time-series data gets stored. The logging script featured in
this repository writes into this database, and the Grafana front-end reads from
it.

* Install InfluxDB
    * Local install, or a Docker container. Really depends on what makes sense in your home setup.
* Create an InfluxDB organization, and at least one data bucket
    * I created two buckets: "low_rate" and "high_rate". This is entirely up to you regarding how you want to control data retention policies/etc.
* Create an access token for the logging script so that it is able to read/write the database.
* Create a separate read-only access token for Grafana to read from the database.
    * ... or just share the read/write access token.

## 2. Set up the `envoy_logger` logging script

* Create a config file that describes your Envoy, how to connect to InfluxDB, and a few other things.
    * Use this example file as a starting point: https://github.com/amykyta3/envoy-logger/blob/main/docs/examples/cfg.yaml
* Locally test that the logging script can read from your Envoy, and push data to InfluxDB
    * You may want to do this locally first before moving to your home automation server, docker container, or whatever your preferred environment is. This will let you tweak settings faster.
    * Clone and pip install, or pip install directly:
        * `python3 -m pip install --force-reinstall git+https://github.com/amykyta3/envoy-logger`
    * Launch the logging script: `python3 -m envoy_logger path/to/your/cfg.yaml`
    * If all goes well, you should see it go through authentication with both your Envoy and InfluxDB, and no error messages from the script.
    * Assuming that goes well, login to your InfluxDB back-end and start exploring the data using their "Data Explorer" tool. If it's working properly, you should start seeing the data flow in. I recommend that you poke around and get familiar with how the data is structured, since it will help you build queries for your dashboard later.
* Once you have proven it works decently when running locally, it is up to you to figure out how to have the logging script run in your home setup.
    * If running in a home automation server, you could wrap this into a docker container.
        * I have a rudimentary dockerfile you can use here: https://github.com/amykyta3/envoy-logger/blob/main/docs/examples/dockerfile
        * ... and a docker compose file too (volume paths will definitely be different for you): https://github.com/amykyta3/envoy-logger/blob/main/docs/examples/envoy-logger.yaml
    * Whatever you choose to run the script, be sure to have the script re-start automatically if it exits.

## 3. Set up Grafana
Grafana is the front-end visualization tool where you can design dashboards to desplay your data.
When you view a dashboard, Grafana pulls data from the InfluxDB database to display it.

* Install Grafana
    * Local install, or a Docker container. Really depends on what makes sense in your home setup.
* Add a connection to InfluxDB
    * Using the authentication token created earlier.
* Start building dashboards from your data!
    * You will need to define some Flux queries to tell Grafana what data to fetch and how to organize it.
    * I have shared the queries I use as a reference: https://github.com/amykyta3/envoy-logger/tree/main/docs/flux_queries
