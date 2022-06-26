# Flexible Virtual Assistant Prototype

This is the prototype for the comparison of the Flexible Virtual Assistant prototype, built using phenotropic interaction design principles for the flexible handling of custom IFTTT rules, and a traditional implementation of the same concepts.

This was developed as part of Moreno Colombo's Ph.D. thesis "Phenotropic Interaction - Improving Interfaces with Computing With Words and Perceptions".

## Setup

The first thing to do is to clone the repository:

```sh
$ git clone https://github.com/colombmo/smartassistant.git
$ cd smartassistant
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ virtualenv2 --no-site-packages env
$ source env/bin/activate
```

Then install the dependencies:

```sh
(env)$ pip install -r requirements.txt
```

Note the `(env)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `virtualenv2`.

Once `pip` has finished downloading the dependencies:
```sh
(env)$ cd project
(env)$ python manage.py runserver
```

And navigate to:
- `http://127.0.0.1:8000/ifttt` to create new custom rules;
- `http://127.0.0.1:8000/assistant/A` to query the Flexible Virtual Assistant;
- `http://127.0.0.1:8000/assistant/A` to query the traditional Virtual Assistant.

The logic used for the implementation of the assistants can be found in `smartassistant/sa/views.py`.