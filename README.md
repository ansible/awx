# AWX-PF

## Setup
Configure the external instance:

```shell
ssh -t your.external.tower.host <<-EOSH
  sudo -i -u root
  echo "CSRF_TRUSTED_ORIGINS = ['your.external.tower.host:443']" >> /etc/tower/settings.py
  ansible-tower-service restart
EOSH
```
Then update the project `webpack.config.js`:
```diff
- const TARGET = 'https://localhost:443';
+ const TARGET = 'https://your.external.tower.host:443';
```

## Usage

* `git clone git@github.com:ansible/awx-pf.git`
* cd awx-pf
* npm install
* npm start
* visit `https://127.0.0.1:3000/`
