FROM themattrix/tox

ONBUILD COPY test_app/ /app/.tox/test_app/

ONBUILD RUN export PYTHONPATH=$PYTHONPATH:/app/.tox/
