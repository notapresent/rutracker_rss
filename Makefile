PYTHON          = $(shell which python2)
DEV_APPSERVER	= $(shell which dev_appserver.py)
PORT      		?= 8080
ADMIN_PORT      = 8081
SERVE_ADDRESS   = 0.0.0.0
DATASTORE_PATH  = $(realpath ../datastore.sqlite3)
APP_ID			= rutracker-rss
ifeq ($(findstring /bin/dev_appserver.py,$(DEV_APPSERVER)),/bin/dev_appserver.py)
APPENGINE = $(realpath $(dir $(DEV_APPSERVER))..)/platform/google_appengine
else
APPENGINE = $(patsubst %/,%,$(dir $(DEV_APPSERVER)))
endif
APPCFG = $(APPENGINE)/appcfg.py

init:
	pip install -r requirements.txt
	rm -rf lib/*
	pip install -r requirements-prod.txt -t lib

test:
	$(PYTHON) testrunner.py $(APPENGINE) .

deploy:
	$(APPCFG) update .

rollback:
	$(APPCFG) rollback .

serve:
	$(PYTHON) $(APPENGINE)/dev_appserver.py \
	--host $(SERVE_ADDRESS) --port $(PORT) \
	--admin_host $(SERVE_ADDRESS) --admin_port $(ADMIN_PORT) \
	--datastore_path=$(DATASTORE_PATH) \
	.

console:
	@$(PYTHON) $(APPENGINE)/remote_api_shell.py -s $(APP_ID).appspot.com

update-indexes:
	$(APPCFG) update_indexes .

vacuum-indexes:
	$(APPCFG) vacuum_indexes .

download-data:
ifndef filename
	@echo "Invalid usage. Try 'make help' for more details."
else
	$(APPCFG) download_data \
	--application=$(APP_ID) \
	--email=$(EMAIL) \
	--url=http://$(APP_ID).appspot.com/_ah/remote_api \
	--filename=$(filename)
endif
