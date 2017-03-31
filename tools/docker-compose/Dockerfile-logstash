FROM logstash:5-alpine
COPY logstash.conf /
RUN touch /logstash.log
RUN chown logstash:logstash /logstash.log
CMD ["-f", "/logstash.conf"]
