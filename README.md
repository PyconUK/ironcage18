# Iron Cage

## What is this?

This is the 2018 version of a web application for managing ticket sales,
attendee preferences, the CFP, grant applications,
and other aspects of PyCon UK.

The 2017 version is [here](http://github.com/pyconuk/ironcage).

## How do I run it?

This is a standard Django project, and is tested and (will be) deployed with Python 3.6.
Dependencies can be installed with `pip install -r requirements.txt`.
A local server can be started with `./manage.py runserver`,
and tests can be run with `./manage.py test`.

To run locally, you will need to create a file called `.env`.
You can copy `.env.example` to `.env`, which will be enough to run the tests.
To interact with Stripe, you will need some test API keys.
Ask [@inglesp](https://github.com/inglesp)
if you would like to use the test API keys for the PyCon UK account.

You will also need to have a Postgres database called `ironcage`.

## Contributing

Bug reports are welcome: please [open an issue](https://github.com/pyconuk/ironcage18/issues).
We're particularly interested in usability issues.

There may also be some open issues:
if they are unclaimed you are welcome to attempt to fix them.
However, please do not open a pull request without first
discussing it with the team via the issue tracker.

We would be happy to offer assistance to newer coders
(and particularly to members of the UK Python community).

See CONTRIBUTORS.md for a list of contributors.

## Deployment

TODO

## Why are you reinventing the wheel?

We are aware of a number of other projects for managing conferences.
However, they are either too opinionated about how a conference should be organised,
in which case they would overly constrain how we run PyCon UK,
or else they attempt to be a framework for building conference management systems,
in which case we risk spending excessive time understanding and fighting a framework.

## Why the name?

The name comes from Weber's [Iron Cage of Bureacracy](https://en.wikipedia.org/wiki/Iron_cage),
and @inglesp liked the sound of a system that
"traps individuals in systems based purely on teleological efficiency, rational calculation and control"!
(He now thinks that sounds a bit pretentious.)
