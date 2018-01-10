FROM themattrix/tox

COPY test_app/ test_app/
COPY tests/ tests/

ONBUILD RUN ls
ONBUILD RUN pws
ONBUILD RUN echo "test"
