FROM python:3.12-slim
WORKDIR /app
COPY service /app/service
# Named state volume takes the ownership of its image mountpoint on first use.
RUN groupadd --gid 10001 hub && useradd --uid 10001 --gid 10001 --no-create-home hub && mkdir /state /output && chown hub:hub /state /output
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "service.server"]
