Building the Documentation
--------------------------
To build the docs, spin up a real AWX server, `pip install sphinx sphinxcontrib-autoprogram`, and run:

    ~ TOWER_HOST=https://awx.example.org TOWER_USERNAME=example TOWER_PASSWORD=secret make clean html
    ~ cd build/html/ && python -m http.server
    Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ..
