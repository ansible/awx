# AWX-PF

## Setup
```shell
# Configure the external tower or awx intance:
ssh -t your.external.tower.host <<-EOSH
  sudo -i -u root
  echo "CSRF_TRUSTED_ORIGINS = ['your.external.tower.host:443']" >> /etc/tower/settings.py
  ansible-tower-service restart
EOSH

# Then update the project webpack configuration:
sed 's/localhost:443/your.external.tower.host:443/g' webpack.config.js > config.js
mv config.js webpack.config.js
```

## Usage

* `git clone git@github.com:ansible/awx-pf.git`
* cd awx-pf
* npm install
* npm start
* visit `https://127.0.0.1:3000/`
