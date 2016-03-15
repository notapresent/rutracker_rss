RSS Feeds for rutracker.org
===========================

Initial setup
-------------

```
make console

execfile('appengine_config.py', {})

from ttscraper.models import Account

acc = Account(username='<username>', password='<password>', userid=<userid>)
acc.put()

```