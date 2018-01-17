FROM themattrix/tox

ONBUILD COPY test_app/ /test/test_app/

ONBUILD RUN export PYTHONPATH=$PYTHONPATH:/test
