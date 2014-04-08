data-lexingtonky
================

Site content for data.lexingtonky.gov

This is a collection of files used to provide a theme and some static content for Lexington, KY's Open Data Portal, which is based on [CKAN](http://ckan.org).

deploying
=========
Install capistrano by running `bundle install`

With the key to the target host on your ssh-agent (`ssh-add /path/to/private_key`) run:
`cap production deploy`
