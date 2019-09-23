MSG_TEMPLATE='"{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"'
REPORT_DIR=./reports
APPS=oauth2_client


.PHONY: help clean_coverage coverage coverage_report diff_coverage pycodestyle pylint \
	quality test

help: ## display this help message
	@echo "Please use 'make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[0-9a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean_coverage: ## Clean coverage reports.
clean_coverage:
		mkdir -p ${REPORT_DIR} && \
		coverage erase; \
		rm -rf ${REPORT_DIR}/diff_coverage/diff_coverage_combined.html

coverage: ## Invoke coverage, only works in TOX!.
coverage: clean_coverage
		coverage run test_runner.py \
			--rcfile=.coveragerc \
			test_runnner.py

coverage_report: ## Invoke coverage report.
coverage_report:
		coverage combine \
			--rcfile=.coveragerc
		coverage xml \
			--rcfile=.coveragerc
		coverage html \
			--rcfile=.coveragerc
		coverage report

diff_coverage: ## Invoke diff-cover.
diff_coverage:
		mkdir -p ${REPORT_DIR}/diff_coverage diff-cover \
			${REPORT_DIR}/coverage.xml \
			--html-report ${REPORT_DIR}/diff_coverage/diff_coverage_combined.html

pycodestyle: ## Invoke "make pycodestyle".
pycodestyle:
		mkdir -p ${REPORT_DIR} && pycodestyle ${APPS} $(arg) | tee ${REPORT_DIR}/pycodestyle.report

pylint: ## Invoke "make pylint"
pylint:
		mkdir -p ${REPORT_DIR} | pylint ${APPS} -j 0 \
			--rcfile=./pylintrc --msg-template=${MSG_TEMPLATE} $(arg) |\
			tee ${REPORT_DIR}/pylint.report

quality: ## Invoke "make pylint && make pycodestyle" on license.
quality: pylint pycodestyle

test: ## Run unit tests.
		tox
