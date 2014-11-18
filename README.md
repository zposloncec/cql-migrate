cql-migrate
===========

`cql-migrate` deploys incremental changes to Cassandra schemas, for automated
deployment and CI systems.

It can create keyspaces, tables, add columns to existing tables and load
static/default data.

Example
-------

For example, v1 of an application has a database creation script like:

	CREATE KEYSPACE my_keyspace
	WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};

	CREATE TABLE my_keyspace.users (
		id uuid,
		name text,
		PRIMARY KEY (id)
	);

Which can be deployed to a local cassandra instance using:

	cql-migrate -f database.cql

We never have to remember if the script has been run already: it is always safe
to rerun it with `cql-migrate`.

We decide that we need a new column to store the user's date of birth. Add a
`ALTER TABLE` statement to add it:

	CREATE KEYSPACE my_keyspace
	WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 2};

	CREATE TABLE my_keyspace.users (
		id uuid,
		name text,
		PRIMARY KEY (id)
	);
	ALTER TABLE my_keyspace.users ADD dob timestamp;

These changes can be simply deployed by rerunning the whole script through
`cql-migrate`:

	cql-migrate -f database.cql

This will create the entire schema if run against a blank database, or just add
the 'dob' column to an existing database.

Installation
------------

cql-migrate requires pyparsing and the datastax python cassandra driver.

	sudo apt-get install python-pyparsing python-blist
	sudo pip install cassandra-driver
	bin/cql-migrate --help

It can also be installed in a virtualenv:

	virtualenv bob
	bob/bin/pip install pyparsing cassandra-driver blist
	bob/bin/python bin/cql-migrate --help
