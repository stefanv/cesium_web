# Mock Cesium App w/ React

## Running the app

Initialize the RethinkDB database with `make db_init`, start the server with `make` and navigate to `localhost:4000` in a browser.


## Dev

`npm v^3.0.0` required.

Run `make install` to install dependencies locally.

Run `make bundle` to run `webpack`.

See the above section to run the app from here.

## Dev tips

- Run `make log` to watch log output
- Run `make debug` to start webserver in debug mode
- Run `make attach` to attach to output of webserver; you can then set pdb
  traces for interactive access:

    import pdb; pdb.set_trace()

