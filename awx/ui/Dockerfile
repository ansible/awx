FROM node:16.13.1
ARG NPMRC_FILE=.npmrc
ENV NPMRC_FILE=${NPMRC_FILE}
ARG TARGET='https://awx:8043'
ENV TARGET=${TARGET}
ENV CI=true
WORKDIR /ui
ADD .eslintignore .eslintignore
ADD .eslintrc.json .eslintrc.json
ADD .linguirc .linguirc
ADD jsconfig.json jsconfig.json
ADD public public
ADD package.json package.json
ADD package-lock.json package-lock.json
COPY ${NPMRC_FILE} .npmrc
RUN npm install
ADD src src
EXPOSE 3001
CMD [ "npm", "start" ]
