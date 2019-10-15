Installation
============

download source and go to this source directory:
```
cd path/to/bugtracker_source_dir
```

Install environment :
```
pipenv install
```
```
pipenv shell
```

Install yeswehack librairie:
```
cd path/yeswehack-lib/
```
```
python setup.py install
```

Install command
```
cd path/to/bugtracker_source_dir
```
```
python setup.py install
```

Run
===
```
ywh-bugtracker {options}
```

Options:
- -n --no-interactive: Non interactive mode, all data are stored/accessible in config file
- -c --configure: configuration mode, to store information in config file
- -f --filename {filename}: send a specified config file (default : HOME/.ywh2bt.cfg)



Return code:
- 100 : YesWeHack Login error
- 110 : YesWeHack program access error
- 120 : Configuration error
- 130 : Configuration File not exist
- 200 : Login error on Bugtracker
- 210 : Project error on Bugtracker
- 220 : Configuration error on bugtracker
