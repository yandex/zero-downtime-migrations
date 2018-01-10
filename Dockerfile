FROM themattrix/tox

COPY test_app/ test_app/
COPY tests/ tests/

RUN ls
RUN pws
RUN echo "test"
