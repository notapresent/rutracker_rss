RSS Feeds for rutracker.org
===========================

Initial setup
-------------

```
make console

execfile('appengine_config.py', {})

from models import Account

acc = Account(username='<username>', password='<password>', userid=<userid>)
acc.put()

```