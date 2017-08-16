SHELL = /bin/bash
SUPERVISORD=supervisord
SUPERVISORCTL=supervisorctl -c baselayer/conf/supervisor/common.conf

.DEFAULT_GOAL := run

bundle = ./static/build/bundle.js
webpack = ./node_modules/.bin/webpack

baselayer/README.md:
	git submodule update --init --remote
	$(MAKE) baselayer-update

.PHONY: baselayer-update
baselayer-update:
	./baselayer/tools/submodule_update.sh

dependencies: baselayer/README.md
	@./baselayer/tools/silent_monitor.py pip install -r baselayer/requirements.txt
	@./baselayer/tools/silent_monitor.py pip install -r requirements.txt
	@./baselayer/tools/silent_monitor.py ./baselayer/tools/check_js_deps.sh

db_init:
	@PYTHONPATH=. ./baselayer/tools/silent_monitor.py ./baselayer/tools/db_init.py

db_clear:
	PYTHONPATH=. ./baselayer/tools/db_init.py -f

$(bundle): webpack.config.js package.json
	$(webpack)

bundle: $(bundle)

bundle-watch:
	$(webpack) -w

paths:
	@mkdir -p log run tmp
	@mkdir -p log/sv_child
	@mkdir -p ~/.local/cesium/logs

log: paths
	./baselayer/tools/watch_logs.py

run: paths dependencies
	@echo "Supervisor will now fire up various micro-services."
	@echo
	@echo " - Please run \`make log\` in another terminal to view logs"
	@echo " - Press Ctrl-C to abort the server"
	@echo " - Run \`make monitor\` in another terminal to restart services"
	@echo
	$(SUPERVISORD) -c baselayer/conf/supervisor/app.conf

monitor:
	@echo "Entering supervisor control panel."
	@echo " - Type \`status\` too see microservice status"
	$(SUPERVISORCTL) -i status

# Attach to terminal of running webserver; useful to, e.g., use pdb
attach:
	$(SUPERVISORCTL) fg app

testrun: paths dependencies
	$(SUPERVISORD) -c baselayer/conf/supervisor/testing.conf

debug:
	@echo "Starting web service in debug mode"
	@echo "Press Ctrl-D to stop"
	@echo
	@$(SUPERVISORD) -c baselayer/conf/supervisor/debug.conf &
	@sleep 1 && $(SUPERVISORCTL) -i status
	@$(SUPERVISORCTL) shutdown

clean:
	rm $(bundle)

test_headless: paths dependencies
	PYTHONPATH='.' xvfb-run ./tools/test_frontend.py

test: paths dependencies
	PYTHONPATH='.' ./tools/test_frontend.py

stop:
	$(SUPERVISORCTL) stop all

status:
	PYTHONPATH='.' ./baselayer/tools/supervisor_status.py

docker-images:
	# Add --no-cache flag to rebuild from scratch
	docker build -t cesium/web . && docker push cesium/web

# Call this target to see which Javascript dependencies are not up to date
check-js-updates:
	./baselayer/tools/check_js_updates.sh
