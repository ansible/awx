
FROM node:10
ARG TARGET_HOST='ui-next'
ENV TARGET_HOST=${TARGET_HOST}
ARG TARGET_PORT=8043
ENV TARGET_PORT=${TARGET_PORT}
WORKDIR /ui_next
ADD build build
ADD dist dist
ADD images images
ADD package.json package.json
ADD package-lock.json package-lock.json
RUN npm install
ADD babel.config.js babel.config.js
ADD webpack.config.js webpack.config.js
ADD src src
EXPOSE 3001
CMD [ "npm", "start" ]
