FROM themattrix/tox

ONBUILD COPY /test_app /tests /app/
